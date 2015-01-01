# coding=utf-8
"""
    flask_resteasy.processors
    ~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from abc import abstractmethod

from flask import request

from inflection import pluralize


class RequestProcessor(object):
    """Base class for request processors.

    :param cfg: :class:`flask_resteasy.configs.APIConfig` instance

    :param request_parser: :class:`flask_resteasy.parsers.RequestParser`
                           instance

    """
    def __init__(self, cfg, request_parser):
        self._cfg = cfg
        self._rp = request_parser
        self._resources = []
        self._links = {}
        self._render_as_list = False
        self._process()

    @abstractmethod
    def _process(self):
        pass

    @property
    def resources(self):
        """List of resource models objects set as a
        result of processing the request.
        """
        return self._resources

    @property
    def render_as_list(self):
        """Should the results for the request by rendered
        as a list or as a dictionary?
        """
        return self._render_as_list

    @property
    def links(self):
        """List of link model objects set as a
        result of processing the request.
        """
        return self._links

    @property
    def resource_name(self):
        """Resource name for the request processed.  It will either by the
        main resource name or the link name.
        """
        if self._rp.link is None:
            return (self._cfg.resource_name_plural
                    if self._render_as_list else self._cfg.resource_name)
        else:
            return self._rp.link

    def _build_query(self, model_class):
        query = model_class.query
        if self._rp.filter:
            query = query.filter_by(**self._rp.filter)
        if self._rp.sort:
            for col, order in self._rp.sort.items():
                fld = getattr(getattr(model_class, col), order)()
                query = query.order_by(fld)
        return query

    def _all(self, model_class=None):
        if model_class is None:
            model_class = self._cfg.model_class
        else:
            model_class = model_class
        return self._build_query(model_class).all()

    def _get_all(self, idents, model_class=None):
        models = []
        if model_class is None:
            model_class = self._cfg.model_class
        else:
            model_class = model_class
        for i in idents:
            models.append(self._get_or_404(i, model_class))
        return models

    def _get_or_404(self, ident, model_class=None):
        if model_class is None:
            model_class = self._cfg.model_class
        else:
            model_class = model_class
        return model_class.query.get_or_404(ident)

    def _copy(self, model, fields, field_defaults=None, model_class=None):
        if model_class is None:
            model_class = self._cfg.model_class
        else:
            model_class = model_class
        field_defaults = field_defaults if field_defaults else {}
        model_copy = model_class()
        for field in fields:
            setattr(model_copy, field, field_defaults[field]
                    if field in field_defaults else getattr(model, field))
        return model_copy

    def _copy_models(self, models, fields, field_defaults=None,
                     model_class=None):
        model_copies = []
        for model in models:
            model_copies.append(
                self._copy(model, fields, field_defaults, model_class))
        return model_copies

    def _json_to_model(self, j_dict, model):

        def _json_to_model_fields(j_dict_root):
            for fld in self._cfg.allowed_to_model:
                j_key = self._cfg.json_case(fld)
                if j_key in j_dict_root:
                    setattr(model, fld, j_dict_root[j_key])

        def _json_to_model_links(j_dict_links):
            for rel in self._cfg.allowed_relationships:
                j_key = self._cfg.json_case(rel)
                if j_key in j_dict_links:
                    model_link = j_dict_links[j_key]
                    if model_link is None:
                        continue
                    elif isinstance(model_link, list):
                        lst = self._get_all(
                            model_link,
                            self._cfg.api_manager.get_model(
                                self._cfg.resource_name_case(j_key)))
                        getattr(model, j_key).extend(lst)
                    else:
                        setattr(model, j_key,
                                self._get_or_404(
                                    model_link,
                                    self._cfg.api_manager.get_model(
                                        self._cfg.resource_name_case(j_key))))

        for j_node in j_dict:
            _json_to_model_fields(j_dict[j_node])
            if self._cfg.use_link_nodes \
                    and self._cfg.links_node in j_dict[j_node]:
                _json_to_model_links(j_dict[j_node][self._cfg.links_node])
            else:
                _json_to_model_links(j_dict[j_node])


class GetRequestProcessor(RequestProcessor):
    """Processor for HTTP GET requests.
    """
    def __init__(self, cfg, request_parser):
        super(GetRequestProcessor, self).__init__(cfg, request_parser)

    def _process(self):
        if len(self._rp.idents) > 0:
            resources = self._get_all(self._rp.idents)
        else:
            resources = self._all()

        if self._rp.link:
            assert len(resources) > 0, 'No parent resource found for links'
            for resc in resources:
                links = getattr(resc, self._rp.link)
                self._render_as_list = isinstance(links, list)
                if self._render_as_list:
                    self._resources.extend(links)
                else:
                    self._resources.append(links)
                self._process_includes_for(links)
        else:
            self._process_includes_for(resources)
            self._render_as_list = len(self._rp.idents) != 1
            self._resources.extend(resources)

    def _process_includes_for(self, resources):

        if self._rp.include:
            for include in self._rp.include:
                if include not in self._cfg.allowed_relationships:
                    continue
                if isinstance(resources, list):
                    for resource in resources:
                        self._set_include(resource, include)
                else:
                    self._set_include(resources, include)

    def _set_include(self, resc, inc):
        if hasattr(resc, inc):
            k = pluralize(inc)
            if k not in self._links:
                self._links[k] = []
            self._links[k].append(getattr(resc, inc))


class DeleteRequestProcessor(RequestProcessor):
    """Processor for HTTP DELETE requests.
    """
    def __init__(self, cfg, request_parser):
        super(DeleteRequestProcessor, self).__init__(cfg, request_parser)

    def _process(self):
        for i in self._rp.idents:
            obj = self._get_or_404(i)
            self._cfg.db.session.delete(obj)
        self._cfg.db.session.commit()


class PostRequestProcessor(RequestProcessor):
    """Processor for HTTP POST requests.
    """
    def __init__(self, cfg, request_parser):
        super(PostRequestProcessor, self).__init__(cfg, request_parser)

    def _process(self):
        # todo - handle creating many models per post
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
        # todo - handle updating many models per put
        json = request.json
        with self._cfg.db.session.no_autoflush:
            model = self._get_or_404(self._rp.idents[0])
            self._json_to_model(json, model)
        self._cfg.db.session.commit()
        self.resources.append(model)
