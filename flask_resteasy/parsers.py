# coding=utf-8
"""
    flask_resteasy.parsers
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2014 by Michael Schenk.
    :license: BSD, see LICENSE for more details.
"""
from flask import request


class RequestParser(object):
    def __init__(self, cfg, **kwargs):
        self._cfg = cfg
        self._parse(**kwargs)

    @property
    def idents(self):
        return self._idents

    @property
    def link(self):
        return self._link

    @property
    def filter(self):
        return self._filter

    @property
    def sort(self):
        return self._sort

    @property
    def include(self):
        return self._include

    @property
    def qp_key_pairs_del(self):
        return ','

    @property
    def qp_key_val_del(self):
        return ':'

    @property
    def filter_qp(self):
        return 'filter'

    @property
    def sort_qp(self):
        return 'sort'

    @property
    def include_qp(self):
        return 'include'

    def _parse(self, **kwargs):

        # parse route params
        self._idents = []
        if self._cfg.id_route_param in kwargs and kwargs[
                self._cfg.id_route_param] is not None:
            self._idents = kwargs[self._cfg.id_route_param].split(',')

        self._link = None
        if self._cfg.link_route_param in kwargs and kwargs[
                self._cfg.link_route_param] is not None:
            self._link = kwargs[self._cfg.link_route_param]

        # parse query params
        self._filter = None
        if self.filter_qp in request.args and request.args[
                self.filter_qp] is not None:
            self._filter = self._parse_filter(request.args[self.filter_qp])

        self._sort = None
        if self.sort_qp in request.args and request.args[
                self.sort_qp] is not None:
            self._sort = self._parse_sort(request.args[self.sort_qp])

        self._include = None
        if self.include_qp in request.args and request.args[
                self.include_qp] is not None:
            self._include = self._parse_include(request.args[self.include_qp])

        assert self.link is None or self._cfg.model_case(
            self.link) in self._cfg.allowed_relationships, \
            'invalid links resource url'

        assert self.link is None or len(
            self.idents) > 0, 'invalid links resource url'

    def _parse_filter(self, filter_str):
        rv = {}
        if len(filter_str) == 0:
            return rv
        else:
            filters = filter_str.split(self.qp_key_pairs_del)
            for f in filters:
                filter_pair = f.split(self.qp_key_val_del)
                filter_key = self._cfg.model_case(filter_pair[0])
                if filter_key in self._cfg.allowed_filter:
                    rv[filter_key] = filter_pair[1]
        return rv

    def _parse_sort(self, sort_str):
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
                fld = self._cfg.model_case(fld)
                if fld in self._cfg.allowed_sort:
                    rv[fld] = order
        return rv

    def _parse_include(self, include_str):
        rv = set()
        if len(include_str) == 0:
            return rv
        else:
            includes = include_str.split(self.qp_key_pairs_del)
            for i in includes:
                i = self._cfg.model_case(i)
                if i in self._cfg.allowed_include:
                    rv.add(i)
        return rv
