# coding=utf-8
"""
    flask_resteasy.parsers
    ~~~~~~~~~~~~~~~~~~~~~~

"""
from abc import abstractmethod
from flask import request, current_app
from flask_resteasy.errors import UnableToProcess


class RequestParser(object):
    """Parses Route and Query parameters for an HTTP request.

    :param cfg: :class:`flask_resteasy.configs.APIConfig` instance

    :param kwargs: dictionary of keyword arguments which contains
                   route parameters and query parameters
    """

    def __init__(self, cfg, **kwargs):
        self._cfg = cfg
        self._idents = []
        self._link = None
        self._filter = None
        self._sort = None
        self._include = None
        self._page = None
        self._per_page = None
        self._parse(**kwargs)

    @property
    def idents(self):
        """List of identifiers set in the `ident` route parameter.

           For example::

               products/1
               idents = [1]

               products/1,2
               idents = [1,2]
        """
        return self._idents

    @property
    def link(self):
        """Link name set in `link` route parameter.

        For example::

            products/1/links/distributor
            link = 'distributor'

            products/1/distributor
            link = 'distributor'
        """
        return self._link

    @property
    def filter(self):
        """Dictionary of field name and value filter pairs.
        Filters are set via query parameters.

        For example::

            products?filter=name:lettuce,distributor_code:SYSCO
            filter = {'name': 'lettuce', 'distributor_code': 'SYSCO'}
        """
        return self._filter

    @property
    def sort(self):
        """Dictionary of field name and value sort pairs.
        Sort pairs are set via query parameters. The value parameter is
        the direction of the sort. Specify `-` for descending otherwise
        it's defaulted to ascending.

        For example::

            products?sort=-name,distributor_code
            sort = {'name': 'desc', 'distributor_code', 'asc'}
        """
        return self._sort

    @property
    def include(self):
        """List of relationships for a resource to side load.

        For example::

            products?include=brand,category
            include=['brand', 'category']
        """
        return self._include

    @property
    def page(self):
        """Page number requested for a paginated request.
        """
        return self._page

    @property
    def per_page(self):
        """Number of items requested per page.
        """
        return self._per_page

    @property
    def qp_key_pairs_del(self):
        """Delimiter for separating multiple key value pairs.
        """
        return ','

    @property
    def qp_key_val_del(self):
        """Delimiter for separating keys from values.
        """
        return ':'

    @property
    def filter_qp(self):
        """Filter query parameter keyword.
        """
        return 'filter'

    @property
    def sort_qp(self):
        """Sort query parameter keyword.
        """
        return 'sort'

    @property
    def include_qp(self):
        """Include query parameter keyword.
        """
        return 'include'

    @property
    def page_qp(self):
        """Query parameter for current per page requested for a paginated
        request. It's also used to build the meta pagination response
        """
        return 'page'

    @property
    def per_page_qp(self):
        """Query parameter for setting the number of items per page for a
        paginated request. It's also used to build the meta
        pagination response.
        """
        return 'per_page'

    @property
    def no_pages_param(self):
        """Not al query parameter but it's used when building
        the meta pagination response
        """
        return 'no_pages'

    @abstractmethod
    def _parse(self, **kwargs):
        """Initiates the parsing process.
        Template method that needs to implemented in subclasses
        """
        pass

    def _parse_idents(self, kwargs):
        idents = kwargs.get(self._cfg.id_route_param, None)
        if idents is None:
            return

        self._idents = idents.split(',')
        for i in self._idents:
            try:
                int(i)
            except ValueError:
                raise UnableToProcess('Route ID Error',
                                      'IDs [%s] are invalid' % idents)

    def _parse_link(self, kwargs):
        link = kwargs.get(self._cfg.link_route_param, None)
        if link is None:
            return

        # store as passed in on url, do not convert case
        self._link = link
        if self._cfg.model_case(self._link) not in self._cfg.relationships:
            # Link does not match any known relationships
            raise UnableToProcess('Route Link Error',
                                  'Link route [%s] is not valid' % self._link)
=======
                                  'Link route is not valid')
>>>>>>> d923b369ef217600d67a1141e3aa54cfe0a38762
        elif self._cfg.model_case(self._link) not in \
                self._cfg.allowed_relationships:
            # Valid link name but it's not allowed
            raise UnableToProcess('Route Link Error',
<<<<<<< HEAD
                                  'Link route [%s] not allowed' % self._link,
                                  403)
=======
                                  'Link route not allowed', 403)
>>>>>>> d923b369ef217600d67a1141e3aa54cfe0a38762

    def _parse_filter(self):
        filter_str = request.args.get(self.filter_qp, None)
        if filter_str is None:
            return

        # Filters applies to either the primary or link resource
        # if there is a link resource then we need its cfg object
        if self.link is None:
            cfg = self._cfg
        else:
            link_resc = self._cfg.resource_name_case(self.link)
            cfg = current_app.api_manager.get_cfg(link_resc)

        if len(filter_str) == 0:
            raise UnableToProcess('Filter Error', 'Filter is blank')
        else:
            self._filter = {}
            filters = filter_str.split(self.qp_key_pairs_del)
            for f in filters:
                filter_pair = f.split(self.qp_key_val_del)
                if len(filter_pair) != 2:
                    # Not a valid filter pair
                    raise UnableToProcess('Filter Error',
                                          'Filter [%s] is invalid' % f)
                filter_key = cfg.model_case(filter_pair[0])
                if filter_key in cfg.allowed_filter:
                    self._filter[filter_key] = filter_pair[1]
                else:
                    if filter_key not in cfg.fields:
                        # Filter key is not a known field
                        raise UnableToProcess('Filter Error',
                                              'Filter field [%s] is unknown'
                                              % filter_key)
                    else:
                        raise UnableToProcess('Filter Error',
                                              'Filter field [%s] not allowed'
                                              % filter_key, 403)

    def _parse_sort(self):
        sort_str = request.args.get(self.sort_qp, None)
        if sort_str is None:
            return

        # Sort applies to either the primary or link resource
        # if there is a link resource then we need its cfg object
        if self.link is None:
            cfg = self._cfg
        else:
            link_resc = self._cfg.resource_name_case(self.link)
            cfg = current_app.api_manager.get_cfg(link_resc)

        if len(sort_str) == 0:
            raise UnableToProcess('Sort Error', 'Sort is blank')
        else:
            self._sort = {}
            sorts = sort_str.split(self.qp_key_pairs_del)
            for s in sorts:
                if s[:1] == '-':
                    fld = s[1:]
                    order = 'desc'
                else:
                    fld = s
                    order = 'asc'
                fld = cfg.model_case(fld)
                if fld in cfg.allowed_sort:
                    self._sort[fld] = order
                else:
                    if fld not in cfg.fields:
                        # Unknown sort field
                        raise UnableToProcess('Sort Error',
                                              'Sort field [%s] unknown' % fld)
                    else:
                        # Sort field not allowed
                        raise UnableToProcess('Sort Error',
                                              'Sort field [%s] not allowed'
                                              % fld, 403)

    def _parse_include(self):
        include_str = request.args.get(self.include_qp, None)
        if include_str is None:
            return

        # Includes applies to either the primary or link resource
        # if there is a link resource then we need its cfg object
        if self.link is None:
            cfg = self._cfg
        else:
            link_resc = self._cfg.resource_name_case(self.link)
            cfg = current_app.api_manager.get_cfg(link_resc)

        if len(include_str) == 0:
            raise UnableToProcess('Include Error', 'Include is blank')
        else:
            self._include = set()
            includes = include_str.split(self.qp_key_pairs_del)
            for i in includes:
                i = cfg.model_case(i)
                if i in cfg.allowed_include:
                    self._include.add(i)
                else:
                    if i not in cfg.relationships:
                        # Unknown relationship name for include
                        raise UnableToProcess('Include Error',
                                              'Include name [%s] unknown' % i)
                    else:
                        # Relationship name not allowed for include
                        raise UnableToProcess('Include Error',
                                              'Include name [%s] not allowed'
                                              % i, 403)

    def _parse_pagination(self):
        page = request.args.get(self.page_qp, None)
        per_page = request.args.get(self.per_page_qp, None)

        if page is None:
            return

        if page:
            try:
                self._page = int(page)
            except ValueError:
                raise UnableToProcess('Pagination Error',
                                      'Page number [%s] is not integer' % page)

        if per_page:
            try:
                self._per_page = int(per_page)
            except ValueError:
                raise UnableToProcess('Pagination Error',
                                      'Per Page number [%s] is not integer'
                                      % per_page)


class GetRequestParser(RequestParser):
    """Parses request parameters for HTTP GET requests
    """
    def _parse(self, **kwargs):

        # what order we parse in matters
        # do idents and link before filter, sort & include
        self._parse_idents(kwargs)
        self._parse_link(kwargs)
        self._parse_filter()
        self._parse_sort()
        self._parse_include()
        self._parse_pagination()


class PostRequestParser(RequestParser):
    """Parses request parameters for HTTP POST requests
    """
    def _parse(self, **kwargs):
        self._parse_idents(kwargs)


class PutRequestParser(RequestParser):
    """Parses request parameters for HTTP PUT requests
    """
    def _parse(self, **kwargs):
        self._parse_idents(kwargs)


class DeleteRequestParser(RequestParser):
    """Parses request parameters for HTTP DELETE requests
    """
    def _parse(self, **kwargs):
        self._parse_idents(kwargs)
