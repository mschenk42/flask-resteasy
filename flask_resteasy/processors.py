# coding=utf-8
"""
    flask_resteasy.processors
    ~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from abc import abstractmethod

from flask import request

from inflection import pluralize

from flask_resteasy.errors import UnableToProcess


class RequestProcessor(object):
    """Base class for request processors.

    :param cfg: :class:`flask_resteasy.configs.APIConfig` instance

    :param request_parser: :class:`flask_resteasy.parsers.RequestParser`
                           instance

    """
    def __init__(self, cfg, request_parser):
        self._cfg = cfg
        self._parser = request_parser
        self._resources = []
        self._links = {}
        self._render_as_list = False
        self._pager = None
        self._process()

    @abstractmethod
    def _process(self):
        pass

    @property
    def resources(self):
        """List of resource models objects set as a result of processing
        the request.
        """
        return self._resources

    @property
    def render_as_list(self):
        """Should the results for the request by rendered as a list or
        as a dictionary?
        """
        return self._render_as_list

    @property
    def links(self):
        """List of link model objects set as a result of processing
        the request.
        """
        return self._links

    @property
    def resource_name(self):
        """Resource name for the request processed.  It will either by the
        main resource name or the link name.
        """
        if self._parser.link is None:
            return (self._cfg.resource_name_plural
                    if self._render_as_list else self._cfg.resource_name)
        else:
            return self._parser.link

    @property
    def pager(self):
        """Encapsulates paginated queries
        """
        return self._pager

    def _build_query(self, idents, target_class, join_class=None):
        q = target_class.query
        if join_class:
            q = q.join(join_class).filter(join_class.id.in_(idents))
        else:
            if len(idents) > 0:
                q = q.filter(target_class.id.in_(idents))
        if self._parser.filter:
            q = q.filter_by(**self._parser.filter)
        if self._parser.sort:
            for col, order in self._parser.sort.items():
                # todo research why we have to access the col this way
                fld = getattr(getattr(target_class, col), order)()
                q = q.order_by(fld)
        return q

    def _get_all(self, model_class):
        self._pager = Pager(self._parser, self._build_query([], model_class))
        return self._pager.items

    def _get_all_or_404(self, idents, target_class=None, join_class=None):
        if target_class is None:
            target_class = self._cfg.model_class
        else:
            target_class = target_class

        q = self._build_query(idents, target_class, join_class)
        self._pager = Pager(self._parser, q)
        rv = self._pager.items

        # if we are retrieving a primary resource link, for example
        # products/1 or products/1,3 - length of ids should match results
        # if no filter set
        if self._parser.filter is None and join_class is None \
                and len(idents) != self._pager.total_items:
            raise UnableToProcess('Not found', 404)
        return rv

    def _get_or_404(self, ident, model_class):
        rv = model_class.query.get(ident)
        if rv is None:
            raise UnableToProcess('Not found', 404)
        return rv

    def _copy(self, obj, flds, fld_defaults=None, model_class=None):
        # if it's a large collection it could have scaling issue
        # do this on the database server?
        if model_class is None:
            model_class = self._cfg.model_class
        else:
            model_class = model_class
        fld_defaults = fld_defaults if fld_defaults else {}
        rv = model_class()
        for field in flds:
            setattr(rv, field, fld_defaults[field]
                    if field in fld_defaults else getattr(obj, field))
        return rv

    def _copy_objs(self, objs, flds, fld_defaults=None, model_class=None):
        rv = [self._copy(obj, flds, fld_defaults, model_class) for obj in objs]
        return rv

    def _json_to_model(self, j_dict, model):

        def _json_to_model_fields(j_dict_root):
            """Update model fields from JSON
            """
            for fld in self._cfg.allowed_to_model:
                j_key = self._cfg.json_case(fld)
                if j_key in j_dict_root:
                    setattr(model, fld, j_dict_root[j_key])

        def _json_to_model_rels(j_dict_links):
            """Update model relationships from JSON
            """
            for rel in self._cfg.allowed_relationships:
                j_key = self._cfg.json_case(rel)
                if j_key in j_dict_links:
                    link_ids = j_dict_links[j_key]
                    # link_ids is a list, str(single id) or None
                    if link_ids is None:
                        continue
                    elif isinstance(link_ids, list):
                        lst = self._get_all_or_404(
                            link_ids,
                            self._cfg.api_manager.get_model(
                                self._cfg.resource_name_case(j_key)))
                        # todo will it work if it's lazy=dynamic relationship?
                        # I think you can only use append and not extend for
                        # this type of relationship
                        # write a test for this condition
                        getattr(model, j_key).extend(lst)
                    else:
                        setattr(model, j_key, self._get_or_404(link_ids,
                                self._cfg.api_manager.get_model(
                                    self._cfg.resource_name_case(j_key))))

        # loop through main nodes
        for j_node in j_dict:
            # update model fields
            _json_to_model_fields(j_dict[j_node])

            # update model relationships
            if self._cfg.use_link_nodes \
                    and self._cfg.links_node in j_dict[j_node]:
                # using "links" node
                _json_to_model_rels(j_dict[j_node][self._cfg.links_node])
            else:
                # no "links" node, saving on same level with fields
                _json_to_model_rels(j_dict[j_node])


class GetRequestProcessor(RequestProcessor):
    """Processor for HTTP GET requests.
    """
    def __init__(self, cfg, request_parser):
        super(GetRequestProcessor, self).__init__(cfg, request_parser)

    def _process(self):
        # todo, include try catch for database errors?
        if self._parser.link:
            target_class = self._cfg.api_manager.get_model(
                self._cfg.resource_name_case(self._parser.link))
            join_class = self._cfg.model_class
        else:
            target_class = self._cfg.model_class
            join_class = None

        if len(self._parser.idents) > 0:
            resources = self._get_all_or_404(self._parser.idents,
                                             target_class, join_class)
        else:
            resources = self._get_all(target_class)

        # Should we render response as a list? - tricky logic here
        # if no route parm ids or,
        # if route parm ids provided is more than 1 & it's not a link resource
        # or, if it's a link resource and the link name is plural,
        # then true, otherwise false
        self._render_as_list = (
            (len(self._parser.idents) == 0) or
            (len(self._parser.idents) > 1 and self._parser.link is None) or
            (self._parser.link and self._parser.link == pluralize(
                self._parser.link)))

        self._process_includes_for(resources)
        self._resources.extend(resources)

    def _process_includes_for(self, resources):
        # todo - what if includes are large collections?
        if self._parser.include:
            for include in self._parser.include:
                if isinstance(resources, list):
                    for resource in resources:
                        self._set_include(resource, include)
                else:
                    self._set_include(resources, include)

    def _set_include(self, resc, inc):
        if hasattr(resc, inc):
            # need a plural resource name, includes are always added as lists
            inc_key = pluralize(inc)
            if inc_key not in self._links:
                self._links[inc_key] = []
            # todo should we check for duplicates here and
            # remove from builder process?
            # todo if inc is a list will it get loaded by calling
            # getattr, do we need to limit here what loads or handle
            # this in the builder process?
            self._links[inc_key].append(getattr(resc, inc))


class DeleteRequestProcessor(RequestProcessor):
    """Processor for HTTP DELETE requests.
    """
    def __init__(self, cfg, request_parser):
        super(DeleteRequestProcessor, self).__init__(cfg, request_parser)

    def _process(self):
        for i in self._parser.idents:
            obj = self._get_or_404(i, self._cfg.model_class)
            self._cfg.db.session.delete(obj)
        self._cfg.db.session.commit()


class PostRequestProcessor(RequestProcessor):
    """Processor for HTTP POST requests.
    """
    def __init__(self, cfg, request_parser):
        super(PostRequestProcessor, self).__init__(cfg, request_parser)

    def _process(self):
        # todo - handle many inserts per post
        json = request.json
        with self._cfg.db.session.no_autoflush:
            model = self._cfg.model_class()
            self._json_to_model(json, model)
        self._cfg.db.session.commit()
        self._resources.append(model)


class PutRequestProcessor(RequestProcessor):
    """Processor for HTTP PUT requests.
    """
    def __init__(self, cfg, request_parser):
        super(PutRequestProcessor, self).__init__(cfg, request_parser)

    def _process(self):
        # todo - handle many updates per put
        json = request.json
        with self._cfg.db.session.no_autoflush:
            model = self._get_or_404(self._parser.idents[0],
                                     self._cfg.model_class)
            self._json_to_model(json, model)
        self._cfg.db.session.commit()
        self.resources.append(model)


class Pager(object):
    """
    Paginates a query
    """
    def __init__(self, rp, query):
        self._set_by_client = rp.page is not None
        self._page = rp.page if rp.page else 1

        if rp.per_page is None or rp.per_page > rp._cfg.max_per_page:
            self._per_page = rp._cfg.max_per_page
        else:
            self._per_page = rp.per_page

        self._query = query
        self._no_pages = 0
        self._total_items = 0
        self._items = None
        self._page_no_param = rp.page_qp
        self._per_page_param = rp.per_page_qp
        self._no_pages_param = rp.no_pages_param
        self._paginate()

    @property
    def page_no_param(self):
        """Number of pages key used when building pagination meta response.
        """
        return self._page_no_param

    @property
    def per_page_param(self):
        """Number of items per page key used when build pagination
        meta response.
        """
        return self._per_page_param

    @property
    def no_pages_param(self):
        """Number of pages key used when build pagination
        meta response.
        """
        return self._no_pages_param

    @property
    def page(self):
        """Current page number
        """
        return self._page

    @property
    def per_page(self):
        """Results per page
        """
        return self._per_page

    @property
    def no_pages(self):
        """Total number of pages available
        """
        return self._no_pages

    @property
    def items(self):
        """Results for current page
        """
        return self._items

    @property
    def total_items(self):
        """Total number of items
        """
        return self._total_items

    @property
    def client_requested(self):
        """Did the client request pagination via query parameters?
        """
        return self._set_by_client

    @property
    def should_return_meta(self):
        """Should we build the response with a meta pagination section?
        """
        return self.client_requested or self.no_pages > 1

    def _paginate(self):
        pagination = self._query.paginate(self._page, self._per_page)
        self._no_pages = pagination.pages
        self._items = pagination.items
        self._total_items = pagination.total
