from flask import request

FILTER_KEY = 'filter'
SORT_KEY = 'sort'
ID_PARAM = 'ident'
LINK_PARAM = 'link'


class ParserFactory(object):
    @staticmethod
    def create(cfg, **kwargs):
        if request.method == 'GET':
            return GetRequestParser(cfg, **kwargs)
        elif request.method == 'POST':
            return PostRequestParser(cfg, **kwargs)
        elif request.method == 'DELETE':
            return DeleteRequestParser(cfg, **kwargs)
        elif request.method == 'PUT':
            return PutRequestParser(cfg, **kwargs)


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

    def _parse(self, **kwargs):

        # parse route params
        if ID_PARAM in kwargs and kwargs[ID_PARAM] is not None:
            self._idents = kwargs[ID_PARAM].split(',')
        else:
            self._idents = []

        if LINK_PARAM in kwargs and kwargs[LINK_PARAM] is not None:
            self._link = kwargs[LINK_PARAM]
        else:
            self._link = None

        # parse query params
        if FILTER_KEY in request.args and request.args[FILTER_KEY] is not None:
            self._filter = self.parse_filter(request.args[FILTER_KEY])
        else:
            self._filter = None

        if SORT_KEY in request.args and request.args[SORT_KEY] is not None:
            self._sort = self.parse_sort(request.args[SORT_KEY])
        else:
            self._sort = None

        assert self.link is None or self._cfg.to_model_tag(self.link) in \
            self._cfg.links, 'invalid links resource url'

        assert self.link is None or len(self.idents) > 0, \
            'invalid links resource url'

    def parse_filter(self, filter_str):
        rv = {}
        if len(filter_str) == 0:
            return rv
        else:
            filters = filter_str.split('|')
            for f in filters:
                filter_pair = f.split('::')
                if filter_pair[0] in self._cfg.field_names:
                    rv[filter_pair[0]] = filter_pair[1]
        return rv

    def parse_sort(self, sort_str):
        rv = {}
        if len(sort_str) == 0:
            return rv
        else:
            sorts = sort_str.split('|')
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


class PostRequestParser(RequestParser):
    pass


class GetRequestParser(RequestParser):
    pass


class DeleteRequestParser(RequestParser):
    pass


class PutRequestParser(RequestParser):
    pass
