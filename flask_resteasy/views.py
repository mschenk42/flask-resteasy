from abc import abstractmethod
import datetime

from flask.views import MethodView
from flask import jsonify, request
from inflection import singularize, pluralize, camelize, underscore


class APIView(MethodView):
    cfg = None

    @classmethod
    @abstractmethod
    def create_cfg(cls, app, db):
        pass

    @classmethod
    def init_cfg(cls, app, db):
        cls.cfg = cls.create_cfg(app, db)

    @classmethod
    def register_urls(cls):
        view_func = cls.as_view(cls.cfg.endpoint_name)
        url = '/%s' % cls.cfg.resource_name_plural
        cls.cfg.app.add_url_rule(
            url, view_func=view_func, methods=['GET', 'POST'])
        cls.cfg.app.add_url_rule(
            '%s/<ident>' % url,
            view_func=view_func,
            methods=['GET', 'PUT', 'DELETE'])
        if cls.cfg.use_links:
            cls.cfg.app.add_url_rule(
                '%s/<ident>/links/<link>' % url,
                view_func=view_func,
                methods=['GET', ])
        else:
            cls.cfg.app.add_url_rule('%s/<ident>/<link>' % url,
                                     view_func=view_func,
                                     methods=['GET', ])

    def get(self, ident=None, link=None):
        req_parser = self.cfg.parser_factory.create(self,
                                                    ident=ident,
                                                    link=link)
        req_processor = self.cfg.processor_factory.create(self, req_parser)

        if req_parser.link:
            link_cls = APIManager.apis[req_parser.link]
            resp_builder = link_cls.cfg.builder_factory.create(
                link_cls, req_processor)
        else:
            resp_builder = self.cfg.builder_factory.create(self, req_processor)

        return jsonify(resp_builder.json_dic)

    def post(self):
        req_parser = self.cfg.parser_factory.create(self)
        req_processor = self.cfg.processor_factory.create(self, req_parser)
        resp_builder = self.cfg.builder_factory.create(self, req_processor)

        return jsonify(resp_builder.json_dic), 201, {
            'Location': resp_builder.urls[0]
            if len(resp_builder.urls) == 1 else resp_builder.urls}

    def delete(self, ident=None, link=None):
        req_parser = self.cfg.parser_factory.create(self,
                                                    ident=ident,
                                                    link=link)
        self.cfg.processor_factory.create(self, req_parser)

        return jsonify({})

    def put(self, ident=None, link=None):
        req_parser = self.cfg.parser_factory.create(self,
                                                    ident=ident,
                                                    link=link)
        req_processor = self.cfg.processor_factory.create(self, req_parser)
        resp_builder = self.cfg.builder_factory.create(self, req_processor)

        return jsonify(resp_builder.json_dic)


class APIConfig(object):
    def __init__(self, model, app, db):
        self._model = model
        self._app = app
        self._db = db

    @property
    def to_model_tag(self):
        return lambda s: underscore(s)

    @property
    def to_json_tag(self):
        return lambda s: camelize(s, False)

    @property
    def resource_name_converter(self):
        return lambda s: camelize(s, False)

    @property
    def model_class(self):
        return self._model

    @model_class.setter
    def model_class(self, value):
        self._model = value

    @property
    def app(self):
        return self._app

    @app.setter
    def app(self, value):
        self._app = value

    @property
    def db(self):
        return self._db

    @db.setter
    def db(self, value):
        self._db = value

    @property
    def field_names(self, exclude=None):
        return set([c.name for c in self.model_class.__table__.columns if
                    not exclude or c.name not in exclude])

    @property
    def field_types(self):
        return {c.name: str(c.type) for c in self.model_class.__table__.columns}

    @property
    def linked_fields(self):
        return set([n for n in self.field_names if
                    n.endswith(self.link_id_postfix)])

    @property
    def resource_name(self):
        return self.resource_name_converter(
            singularize(str(self.model_class.__table__.name.lower())))

    @property
    def resource_name_plural(self):
        return pluralize(self.resource_name)

    @property
    def fields_to_model(self):
        return self.field_names - self.private_fields - self.linked_fields - {
            self.id_keyword}

    @property
    def fields_to_json(self):
        return self.field_names - self.private_fields - self.linked_fields

    @property
    def private_fields(self):
        return set([n for n in self.field_names
                    if n.startswith(self.private_field_prefix)])

    @property
    def endpoint_name(self):
        return ''.join([self.resource_name, self.endpoint_postfix])

    @property
    def links(self):
        return set([n for n in self.model_class._sa_class_manager
                    if n not in self.field_names])

    @property
    def links_keyword(self):
        return 'links'

    @property
    def links_url_pattern(self):
        return '/links/'

    @property
    def use_links(self):
        # currently Ember's Restful Adapter doesn't support the links keyword
        return False

    @property
    def id_keyword(self):
        return 'id'

    @property
    def linked_keyword(self):
        return 'linked'

    @property
    def endpoint_postfix(self):
        return '_api'

    @property
    def link_id_postfix(self):
        return '_id'

    @property
    def private_field_prefix(self):
        return '_'

    @property
    def parser_factory(self):
        return RequestParserFactory

    @property
    def processor_factory(self):
        return RequestProcessorFactory

    @property
    def builder_factory(self):
        return ResponseBuilderFactory


class APIManager(object):
    apis = {}
    models = {}

    @classmethod
    def load(cls, app, db, apis):
        for api in apis:
            api.init_cfg(app, db)
            cls.models[api.cfg.resource_name] = api.cfg.model_class
            cls.models[api.cfg.resource_name_plural] = api.cfg.model_class
            cls.apis[api.cfg.resource_name] = api
            cls.apis[api.cfg.resource_name_plural] = api
            api.register_urls()


class RequestParser(object):
    def __init__(self, api_class, **kwargs):
        self._api = api_class
        self._idents = kwargs['ident'].split(',') \
            if 'ident' in kwargs and kwargs['ident'] is not None else []
        self._link = kwargs['link'] \
            if 'link' in kwargs and kwargs['link'] is not None else None
        self._parse()

    @property
    def idents(self):
        return self._idents

    @property
    def link(self):
        return self._link

    def _parse(self):
        assert self.link is None or self._api.cfg.to_model_tag(
            self.link) in self._api.cfg.links, 'invalid links resource url'
        assert self.link is None or len(self.idents) > 0, \
            'invalid links resource url'


class PostRequestParser(RequestParser):
    pass


class GetRequestParser(RequestParser):
    pass


class DeleteRequestParser(RequestParser):
    pass


class PutRequestParser(RequestParser):
    pass


class RequestProcessor(object):
    def __init__(self, api_class, request_parser):
        self._api = api_class
        self._model_class = api_class.cfg.model_class
        self._db = api_class.cfg.db
        self._rp = request_parser
        self._models = []
        self._render_as_list = False
        self._process()

    @abstractmethod
    def _process(self):
        pass

    @property
    def models(self):
        return self._models

    @property
    def render_as_list(self):
        return self._render_as_list

    @property
    def root_name(self):
        if self._rp.link is None:
            return self._api.cfg.resource_name_plural \
                if self._render_as_list else self._api.cfg.resource_name
        else:
            return self._rp.link

    def _all(self, model_class=None):
        """Returns a generator containing all instances of the service's model.
        """
        model_class = self._model_class if model_class is None else model_class
        return model_class.query.all()

    def _get_all(self, idents, model_class=None):
        """Returns a list of instances of the service's model with the specified
        ids.

        :param *ids: instance ids
        """
        models = []
        model_class = self._model_class if model_class is None else model_class
        for i in idents:
            models.append(self._get_or_404(i, model_class))
        return models

    def _find(self, model_class=None, **kwargs):
        """Returns a list of instances of the service's model filtered by the
        specified key word arguments.

        :param **kwargs: filter parameters
        """
        model_class = self._model_class if model_class is None else model_class
        return model_class.query.filter_by(**kwargs)

    def _first(self, model_class=None, **kwargs):
        """Returns the first instance found of the service's model filtered by
        the specified key word arguments.

        :param **kwargs: filter parameters
        """
        model_class = self._model_class if model_class is None else model_class
        return self._find(model_class, **kwargs).first()

    def _get_or_404(self, id, model_class=None):
        """Returns an instance of the service's model with the specified id or
        raises an 404 error if an instance with the specified id does not exist.

        :param id: the instance id
        """
        model_class = self._model_class if model_class is None else model_class
        return model_class.query.get_or_404(id)

    def _copy(self, model, fields, field_defaults=None, model_class=None):
        model_class = self._model_class if model_class is None else model_class
        field_defaults = field_defaults if field_defaults else {}
        model_copy = model_class()
        for field in fields:
            setattr(model_copy,
                    field,
                    field_defaults[field]
                    if field in field_defaults else getattr(model, field))
        return model_copy

    def _copy_models(self, models, fields, field_defaults=None,
                     model_class=None):
        model_copies = []
        for model in models:
            model_copies.append(self._copy(
                model, fields, field_defaults, model_class))
        return model_copies

    def _json_to_model(self, j_dict, model):

        def _json_to_model_fields(j_dict_root):
            for c in self._api.cfg.fields_to_model:
                if c in j_dict_root:
                    setattr(model, c, j_dict_root[c])

        def _json_to_model_links(j_dict_links):
            for c in self._api.cfg.links:
                if c in j_dict_links:
                    model_link = j_dict_links[c]
                    if model_link is None:
                        continue
                    elif isinstance(model_link, list):
                        lst = self._get_all(model_link, APIManager.models[c])
                        getattr(model, c).extend(lst)
                    else:
                        setattr(model,
                                c,
                                self._get_or_404(model_link,
                                                 APIManager.models[c]))

        for root in j_dict:
            _json_to_model_fields(j_dict[root])
            if self._api.cfg.use_links and \
                    self._api.cfg.links_keyword in j_dict[root]:
                _json_to_model_links(j_dict[root][self._api.cfg.links_keyword])
            else:
                _json_to_model_links(j_dict[root])


class GetRequestProcessor(RequestProcessor):
    def __init__(self, api_class, request_parser):
        super(GetRequestProcessor, self).__init__(api_class, request_parser)

    def _process(self):
        if len(self._rp.idents) > 0:
            r_objs = self._get_all(self._rp.idents)
        else:
            r_objs = self._all()

        if self._rp.link:
            assert len(r_objs) > 0, 'No parent resource found for links'
            for r_o in r_objs:
                l_objs = getattr(r_o, self._api.cfg.to_model_tag(self._rp.link))
                if isinstance(l_objs, list):
                    self._render_as_list = True
                    self._models.extend(l_objs)
                else:
                    self._render_as_list = False
                    self._models.append(l_objs)
        else:
            self._render_as_list = len(self._rp.idents) != 1
            self._models.extend(r_objs)


class DeleteRequestProcessor(RequestProcessor):
    def __init__(self, api_class, request_parser):
        super(DeleteRequestProcessor, self).__init__(api_class, request_parser)

    def _process(self):
        for i in self._rp.idents:
            obj = self._get_or_404(i)
            self._db.session.delete(obj)
        self._db.session.commit()


class PostRequestProcessor(RequestProcessor):
    def __init__(self, api_class, request_parser):
        super(PostRequestProcessor, self).__init__(api_class, request_parser)

    def _process(self):
        # todo - handle creating many models per post
        json = request.json
        with self._db.session.no_autoflush:
            model = self._model_class()
            self._json_to_model(json, model)
        self._db.session.commit()
        self._models.append(model)


class PutRequestProcessor(RequestProcessor):
    def __init__(self, api_class, request_parser):
        super(PutRequestProcessor, self).__init__(api_class, request_parser)

    def _process(self):
        # todo - handle updating many models per put
        json = request.json
        with self._db.session.no_autoflush:
            model = self._get_or_404(self._rp.idents[0])
            self._json_to_model(json, model)
        self._db.session.commit()
        self.models.append(model)


class ResponseBuilder(object):
    def __init__(self, api_class, request_processor):
        self._api = api_class
        self._rp = request_processor
        self._json_dic = None
        self._build()

    @property
    def json_dic(self):
        return self._json_dic

    @property
    def urls(self):
        return self._get_urls_for(self._rp.models)

    def _build(self):
        json_dic = {self._rp.root_name: [] if self._rp.render_as_list else {}}

        if self._rp.render_as_list:
            for model in self._rp.models:
                json_dic[self._rp.root_name].append(self._obj_to_dic(model))
        else:
            json_dic[self._rp.root_name] = self._obj_to_dic(self._rp.models[0])

        self._json_dic = json_dic

    def _obj_to_dic(self, obj):
        dic = self._obj_fields_to_dic(obj)
        dic.update(self._obj_links_to_dic(obj))
        return dic

    def _obj_fields_to_dic(self, obj):
        """
        Copied and adapted from
        https://coderwall.com/p/5rbcxq/sqlalchemy-model-to-dictionary
        """
        dic = {}
        convert = {"DATETIME": datetime.datetime.isoformat}
        if obj is not None:
            for field_name in self._api.cfg.fields_to_json:
                field_name_key = self._api.cfg.to_json_tag(field_name)
                v = getattr(obj, field_name)
                current_type = self._api.cfg.field_types[field_name]
                if current_type in convert and v is not None:
                    try:
                        dic[field_name_key] = convert[current_type](v)
                    except:
                        dic[field_name_key] = \
                            'Error:  Failed to covert using ', \
                            unicode(
                                convert[self._api.cfg.field_types[field_name]])
                elif v is None:
                    dic[field_name_key] = unicode()
                else:
                    dic[field_name_key] = v
        return dic

    def _set_link(self, dic, link_key, link_obj):
        if self._api.cfg.use_links:
            if self._api.cfg.links_keyword not in dic:
                dic[self._api.cfg.links_keyword] = {}
            dic[self._api.cfg.links_keyword][link_key] = link_obj
        else:
            dic[link_key] = link_obj

    def _obj_links_to_dic(self, obj):
        dic = {}
        if obj is not None:
            links = self._api.cfg.links
            dic = {}
            for link in links:
                link_key = self._api.cfg.to_json_tag(link)
                linked_obj = getattr(obj, link)
                if isinstance(linked_obj, list):
                    l_lst = []
                    for l_item in linked_obj:
                        l_lst.append(getattr(l_item, self._api.cfg.id_keyword))
                    self._set_link(dic, link_key, l_lst)
                else:
                    if linked_obj:
                        self._set_link(dic, link_key, getattr(
                            linked_obj, self._api.cfg.id_keyword))
                    else:
                        self._set_link(dic, link_key, None)
        return dic

    def _get_urls_for(self, objs):
        urls = []
        if isinstance(objs, list):
            for o in objs:
                urls.append('%s/%d' % (request.url, o.id))
        else:
            urls.append('%s/%d' % (request.url, objs.id))
        return urls


class RequestParserFactory(object):
    @classmethod
    def create(cls, api_class, **kwargs):
        if request.method == 'GET':
            return GetRequestParser(api_class, **kwargs)
        elif request.method == 'POST':
            return PostRequestParser(api_class, **kwargs)
        elif request.method == 'DELETE':
            return DeleteRequestParser(api_class, **kwargs)
        elif request.method == 'PUT':
            return PutRequestParser(api_class, **kwargs)


class RequestProcessorFactory(object):
    @classmethod
    def create(cls, api_class, request_parser):
        if request.method == 'GET':
            return GetRequestProcessor(api_class, request_parser)
        elif request.method == 'POST':
            return PostRequestProcessor(api_class, request_parser)
        elif request.method == 'DELETE':
            return DeleteRequestProcessor(api_class, request_parser)
        elif request.method == 'PUT':
            return PutRequestProcessor(api_class, request_parser)


class ResponseBuilderFactory(object):
    @classmethod
    def create(cls, api_class, response_builder):
        return ResponseBuilder(api_class, response_builder)
