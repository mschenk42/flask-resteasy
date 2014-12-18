from abc import abstractmethod
from flask import request


class RequestProcessor(object):
    def __init__(self, cfg, request_parser):
        self._cfg = cfg
        self._rp = request_parser
        self._results = []
        self._render_as_list = False
        self._process()

    @abstractmethod
    def _process(self):
        pass

    @property
    def results(self):
        return self._results

    @property
    def render_as_list(self):
        return self._render_as_list

    @property
    def root_name(self):
        if self._rp.link is None:
            return (self._cfg.resource_name_plural
                    if self._render_as_list else self._cfg.resource_name)
        else:
            return self._rp.link

    def _build_query(self, model_class):
        query = model_class.query
        if self._rp.filter:
            query = query.filter_by(**self._rp.filter)
        if self._rp.sort_by:
            for col, order in self._rp.sort_by.items():
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

    def _get_or_404(self, id, model_class=None):
        if model_class is None:
            model_class = self._cfg.model_class
        else:
            model_class = model_class
        return model_class.query.get_or_404(id)

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
            for c in self._cfg.fields_to_model:
                if c in j_dict_root:
                    setattr(model, c, j_dict_root[c])

        def _json_to_model_links(j_dict_links):
            for c in self._cfg.links:
                if c in j_dict_links:
                    model_link = j_dict_links[c]
                    if model_link is None:
                        continue
                    elif isinstance(model_link, list):
                        lst = self._get_all(
                            model_link,
                            self._cfg.api_manager.get_model(c))
                        getattr(model, c).extend(lst)
                    else:
                        setattr(model, c,
                                self._get_or_404(
                                    model_link,
                                    self._cfg.api_manager.get_model(c)))

        for root in j_dict:
            _json_to_model_fields(j_dict[root])
            if self._cfg.use_links:
                if self._cfg.links_keyword in j_dict[root]:
                    _json_to_model_links(j_dict[root][self._cfg.links_keyword])
                else:
                    _json_to_model_links(j_dict[root])
            else:
                _json_to_model_links(j_dict[root])


class GetRequestProcessor(RequestProcessor):
    def __init__(self, cfg, request_parser):
        super(GetRequestProcessor, self).__init__(cfg, request_parser)

    def _process(self):
        if len(self._rp.idents) > 0:
            r_objs = self._get_all(self._rp.idents)
        else:
            r_objs = self._all()

        if self._rp.link:
            assert len(r_objs) > 0, 'No parent resource found for links'
            for r_o in r_objs:
                l_objs = getattr(r_o, self._cfg.to_model_tag(self._rp.link))
                self._render_as_list = isinstance(l_objs, list)
                if self._render_as_list:
                    self._results.extend(l_objs)
                else:
                    self._results.append(l_objs)
        else:
            self._render_as_list = len(self._rp.idents) != 1
            self._results.extend(r_objs)


class DeleteRequestProcessor(RequestProcessor):
    def __init__(self, cfg, request_parser):
        super(DeleteRequestProcessor, self).__init__(cfg, request_parser)

    def _process(self):
        for i in self._rp.idents:
            obj = self._get_or_404(i)
            self._cfg.db.session.delete(obj)
        self._cfg.db.session.commit()


class PostRequestProcessor(RequestProcessor):
    def __init__(self, cfg, request_parser):
        super(PostRequestProcessor, self).__init__(cfg, request_parser)

    def _process(self):
        # todo - handle creating many models per post
        json = request.json
        with self._cfg.db.session.no_autoflush:
            model = self._cfg.model_class()
            self._json_to_model(json, model)
        self._cfg.db.session.commit()
        self._results.append(model)


class PutRequestProcessor(RequestProcessor):
    def __init__(self, cfg, request_parser):
        super(PutRequestProcessor, self).__init__(cfg, request_parser)

    def _process(self):
        # todo - handle updating many models per put
        json = request.json
        with self._cfg.db.session.no_autoflush:
            model = self._get_or_404(self._rp.idents[0])
            self._json_to_model(json, model)
        self._cfg.db.session.commit()
        self.results.append(model)


class ProcessorFactory(object):
    @staticmethod
    def create(cfg, request_parser):
        if request.method == 'GET':
            return GetRequestProcessor(cfg, request_parser)
        elif request.method == 'POST':
            return PostRequestProcessor(cfg, request_parser)
        elif request.method == 'DELETE':
            return DeleteRequestProcessor(cfg, request_parser)
        elif request.method == 'PUT':
            return PutRequestProcessor(cfg, request_parser)