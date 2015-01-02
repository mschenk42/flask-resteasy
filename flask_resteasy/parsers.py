# coding=utf-8
"""
    flask_resteasy.parsers
    ~~~~~~~~~~~~~~~~~~~~~~

"""
from flask import request, abort, current_app


class RequestParser(object):
    """Parses Route and Query parameters for an HTTP request.

    :param cfg: :class:`flask_resteasy.configs.APIConfig` instance

    :param kwargs: dictionary of keyword arguments which contains
                   route parameters and query parameters
    """

    def __init__(self, cfg, **kwargs):
        self._cfg = cfg
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

    def _parse(self, **kwargs):

        # parse id route param
        self._idents = []
        if self._cfg.id_route_param in kwargs and kwargs[
                self._cfg.id_route_param] is not None:
            self._idents = kwargs[self._cfg.id_route_param].split(',')
            for i in self._idents:
                try:
                    int(i)
                except ValueError:
                    current_app.logger.debug(
                        '[%s] route param are not Integers [%s]'
                        % (self._cfg.id_route_param, self._idents))
                    abort(404)

        # parse link route param
        self._link = None
        if self._cfg.link_route_param in kwargs and kwargs[
                self._cfg.link_route_param] is not None:
            self._link = self._cfg.model_case(
                kwargs[self._cfg.link_route_param])
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

        # parse filter query param
        self._filter = None
        if self.filter_qp in request.args and request.args[
                self.filter_qp] is not None:
            self._filter = self._parse_filter(request.args[self.filter_qp])

        # parse sort query param
        self._sort = None
        if self.sort_qp in request.args and request.args[
                self.sort_qp] is not None:
            self._sort = self._parse_sort(request.args[self.sort_qp])

        # parse include query param
        self._include = None
        if self.include_qp in request.args and request.args[
                self.include_qp] is not None:
            self._include = self._parse_include(request.args[self.include_qp])

    def _parse_filter(self, filter_str):
        # Filters applies to either the primary or link resource
        # if there is a link resource then we need its cfg object
        if self.link is None:
            cfg = self._cfg
        else:
            link_resc = self._cfg.resource_case_name(self.link)
            cfg = current_app.api_manager.get_cfg(link_resc)

        rv = {}
        if len(filter_str) == 0:
            return rv
        else:
            filters = filter_str.split(self.qp_key_pairs_del)
            for f in filters:
                filter_pair = f.split(self.qp_key_val_del)
                if len(filter_pair) != 2:
                    current_app.logger.debug('Invalid filter pair [%s]' % f)
                    abort(404)
                filter_key = cfg.model_case(filter_pair[0])
                if filter_key in cfg.allowed_filter:
                    rv[filter_key] = filter_pair[1]
                else:
                    if filter_key not in cfg.fields:
                        current_app.logger.debug('Filter [%s] unknown field'
                                                 % filter_key)
                        abort(404)
                    else:
                        current_app.logger.debug('Filter [%s] not allowed'
                                                 % filter_key)
                        abort(403)
        return rv

    def _parse_sort(self, sort_str):
        # Sort applies to either the primary or link resource
        # if there is a link resource then we need its cfg object
        if self.link is None:
            cfg = self._cfg
        else:
            link_resc = self._cfg.resource_case_name(self.link)
            cfg = current_app.api_manager.get_cfg(link_resc)

        rv = {}
        if len(sort_str) == 0:
            return rv
        else:
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
                    rv[fld] = order
                else:
                    if fld not in cfg.fields:
                        current_app.logger.debug(
                            'Sort [%s] unknown field' % fld)
                        abort(404)
                    else:
                        current_app.logger.debug('Sort [%s] not allowed' % fld)
                        abort(403)
        return rv

    def _parse_include(self, include_str):
        # Includes applies to either the primary or link resource
        # if there is a link resource then we need its cfg object
        if self.link is None:
            cfg = self._cfg
        else:
            link_resc = self._cfg.resource_case_name(self.link)
            cfg = current_app.api_manager.get_cfg(link_resc)
            
        rv = set()
        if len(include_str) == 0:
            return rv
        else:
            includes = include_str.split(self.qp_key_pairs_del)
            for i in includes:
                i = cfg.model_case(i)
                if i in cfg.allowed_include:
                    rv.add(i)
                else:
                    if i not in cfg.relationships:
                        current_app.logger.debug(
                            'Include [%s] unknown relationship' % i)
                        abort(404)
                    else:
                        current_app.logger.debug(
                            'Include [%s] not allowed' % i)
                        abort(403)
        return rv
