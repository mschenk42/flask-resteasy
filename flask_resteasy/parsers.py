# coding=utf-8
"""
    flask_resteasy.parsers
    ~~~~~~~~~~~~~~~~~~~~~~

    Copyright 2014 Michael Schenk

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
    see LICENSE file for more details

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
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
    def sort_by(self):
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
        if self._cfg.id_route_param in kwargs:
            if kwargs[self._cfg.id_route_param] is not None:
                self._idents = kwargs[self._cfg.id_route_param].split(',')
            else:
                self._idents = []
        else:
            self._idents = []

        if self._cfg.link_route_param in kwargs:
            if kwargs[self._cfg.link_route_param] is not None:
                self._link = kwargs[self._cfg.link_route_param]
            else:
                self._link = None
        else:
            self._link = None

        # parse query params
        if self.filter_qp in request.args:
            if request.args[self.filter_qp] is not None:
                self._filter = self._parse_filter(request.args[self.filter_qp])
            else:
                self._filter = None
        else:
            self._filter = None

        if self.sort_qp in request.args:
            if request.args[self.sort_qp] is not None:
                self._sort = self._parse_sort(request.args[self.sort_qp])
            else:
                self._sort = None
        else:
            self._sort = None

        if self.include_qp in request.args:
            if request.args[self.include_qp] is not None:
                self._include = self._parse_include(
                    request.args[self.include_qp])
            else:
                self._include = None
        else:
            self._include = None

        assert self.link is None or self._cfg.to_model_field(self.link) in \
            self._cfg.relationships, 'invalid links resource url'

        assert self.link is None or len(self.idents) > 0, \
            'invalid links resource url'

    def _parse_filter(self, filter_str):
        rv = {}
        if len(filter_str) == 0:
            return rv
        else:
            filters = filter_str.split(self.qp_key_pairs_del)
            for f in filters:
                filter_pair = f.split(self.qp_key_val_del)
                if filter_pair[0] in self._cfg.field_names:
                    rv[filter_pair[0]] = filter_pair[1]
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
                if fld in self._cfg.field_names:
                    rv[fld] = order
        return rv

    def _parse_include(self, include_str):
        rv = set()
        if len(include_str) == 0:
            return rv
        else:
            includes = include_str.split(self.qp_key_pairs_del)
            for i in includes:
                # todo add the ability to exclude relationships?
                if i in self._cfg.relationships:
                    rv.add(i)
        return rv


class PostRequestParser(RequestParser):
    pass


class GetRequestParser(RequestParser):
    pass


class DeleteRequestParser(RequestParser):
    pass


class PutRequestParser(RequestParser):
    pass
