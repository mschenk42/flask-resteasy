# coding=utf-8
"""
    flask_resteasy.parsers
    ~~~~~~~~~~~~~~~~~~~~~~

"""
from abc import abstractmethod
from flask import request, abort, current_app


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
                current_app.logger.debug(
                    '[%s] route param are not Integers [%s]'
                    % (self._cfg.id_route_param, self._idents))
                abort(404)

    def _parse_link(self, kwargs):
        link = kwargs.get(self._cfg.link_route_param, None)
        if link is None:
            return

        self._link = self._cfg.model_case(link)
        if len(self._idents) == 0:
            current_app.debug('No [%s] specified for link route [%s]'
                              % (self._cfg.id_route_param,
                                 self._link))
            abort(404)
        elif self._link not in self._cfg.relationships:
            current_app.logger.debug('Link [%s] is unknown relationship'
                                     % self._link)
            abort(404)
        elif self._link not in self._cfg.allowed_relationships:
            current_app.logger.debug(
                'Link route [%s] not allowed' % self._link)
            abort(403)

    def _parse_filter(self):
        filter_str = request.args.get(self.filter_qp, None)
        if filter_str is None:
            return

        # Filters applies to either the primary or link resource
        # if there is a link resource then we need its cfg object
        if self.link is None:
            cfg = self._cfg
        else:
            link_resc = self._cfg.resource_case_name(self.link)
            cfg = current_app.api_manager.get_cfg(link_resc)

        if len(filter_str) == 0:
            return
        else:
            self._filter = {}
            filters = filter_str.split(self.qp_key_pairs_del)
            for f in filters:
                filter_pair = f.split(self.qp_key_val_del)
                if len(filter_pair) != 2:
                    current_app.logger.debug('Invalid filter pair [%s]' % f)
                    abort(404)
                filter_key = cfg.model_case(filter_pair[0])
                if filter_key in cfg.allowed_filter:
                    self._filter[filter_key] = filter_pair[1]
                else:
                    if filter_key not in cfg.fields:
                        current_app.logger.debug('Filter [%s] unknown field'
                                                 % filter_key)
                        abort(404)
                    else:
                        current_app.logger.debug('Filter [%s] not allowed'
                                                 % filter_key)
                        abort(403)

    def _parse_sort(self):
        sort_str = request.args.get(self.sort_qp, None)
        if sort_str is None:
            return

        # Sort applies to either the primary or link resource
        # if there is a link resource then we need its cfg object
        if self.link is None:
            cfg = self._cfg
        else:
            link_resc = self._cfg.resource_case_name(self.link)
            cfg = current_app.api_manager.get_cfg(link_resc)

        if len(sort_str) == 0:
            return
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
                        current_app.logger.debug(
                            'Sort [%s] unknown field' % fld)
                        abort(404)
                    else:
                        current_app.logger.debug('Sort [%s] not allowed' % fld)
                        abort(403)

    def _parse_include(self):
        include_str = request.args.get(self.include_qp, None)
        if include_str is None:
            return

        # Includes applies to either the primary or link resource
        # if there is a link resource then we need its cfg object
        if self.link is None:
            cfg = self._cfg
        else:
            link_resc = self._cfg.resource_case_name(self.link)
            cfg = current_app.api_manager.get_cfg(link_resc)
            
        if len(include_str) == 0:
            return
        else:
            self._include = set()
            includes = include_str.split(self.qp_key_pairs_del)
            for i in includes:
                i = cfg.model_case(i)
                if i in cfg.allowed_include:
                    self._include.add(i)
                else:
                    if i not in cfg.relationships:
                        current_app.logger.debug(
                            'Include [%s] unknown relationship' % i)
                        abort(404)
                    else:
                        current_app.logger.debug(
                            'Include [%s] not allowed' % i)
                        abort(403)

    def _parse_pagination(self):
        page = request.args.get(self.page_qp, None)
        per_page = request.args.get(self.per_page_qp, None)

        if page is None or per_page is None:
            return

        if page:
            try:
                self._page = int(page)
            except ValueError:
                current_app.logger.debug(
                    '[%s] of [%s] is invalid' % (self.page_qp, page))
                abort(400)

        if per_page:
            try:
                self._per_page = int(per_page)
            except ValueError:
                current_app.logger.debug(
                    '[%s] of [%s] is invalid' % (self.per_page_qp, per_page))
                abort(400)


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
