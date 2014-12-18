from flask.views import MethodView

from flask import jsonify

from .configs import JSONAPIConfig


class APIView(MethodView):
    def __init__(self, cfg):
        self._cfg = cfg

    @property
    def cfg(self):
        return self._cfg

    def get(self, ident=None, link=None):
        parser = self.cfg.parser_factory.create(self.cfg, ident=ident,
                                                link=link)
        processor = self.cfg.processor_factory.create(self.cfg, parser)
        if parser.link:
            link_cfg = self.cfg.api_manager.get_cfg(parser.link)
            builder = link_cfg.builder_factory.create(link_cfg, processor)
        else:
            builder = self.cfg.builder_factory.create(self.cfg, processor)

        return jsonify(builder.json_dic)

    def post(self):
        parser = self.cfg.parser_factory.create(self.cfg)
        processor = self.cfg.processor_factory.create(self.cfg, parser)
        builder = self.cfg.builder_factory.create(self.cfg, processor)
        url = builder.urls[0] if len(builder.urls) == 1 else builder.urls

        return jsonify(builder.json_dic), 201, {'Location': url}

    def delete(self, ident=None, link=None):
        parser = self.cfg.parser_factory.create(self.cfg, ident=ident,
                                                link=link)
        self.cfg.processor_factory.create(self.cfg, parser)

        return jsonify({})

    def put(self, ident=None, link=None):
        parser = self.cfg.parser_factory.create(self.cfg, ident=ident,
                                                link=link)
        processor = self.cfg.processor_factory.create(self.cfg, parser)
        builder = self.cfg.builder_factory.create(self.cfg, processor)

        return jsonify(builder.json_dic)


class APIManager(object):
    def __init__(self, app, db, cfg_class=JSONAPIConfig, decorators=None):
        self._app = None
        self._db = None
        self._model_for_resources = {}
        self._cfg_for_resources = {}
        self._cfg_class = cfg_class
        if decorators:
            APIView.decorators = decorators
        self.init_app(app, db)

    def init_app(self, app, db):
        self._app = app
        self._db = db

    def _register_cfg(self, view, resource_singular, resource_plural):
        self._cfg_for_resources[str(resource_singular.lower())] = view
        self._cfg_for_resources[str(resource_plural.lower())] = view

    def _register_model(self, model_class, resource_singular, resource_plural):
        self._model_for_resources[str(resource_singular.lower())] = model_class
        self._model_for_resources[str(resource_plural.lower())] = model_class

    def get_cfg(self, resource_name):
        return self._cfg_for_resources[str(resource_name.lower())]

    def get_model(self, resource_name):
        return self._model_for_resources[str(resource_name.lower())]

    def register_api(self, model_class, for_methods=None, bp=None, **kwargs):

        if for_methods is None:
            for_methods = ['GET', 'POST', 'PUT', 'DELETE']

        if 'cfg_class' not in kwargs:
            cfg_class = self._cfg_class
        else:
            cfg_class = kwargs['cfg_class']
        cfg = cfg_class(model_class, self._app, self._db, self, **kwargs)

        self._register_cfg(cfg, cfg.resource_name, cfg.resource_name_plural)
        self._register_model(model_class, cfg.resource_name,
                             cfg.resource_name_plural)

        reg_with = self._app if bp is None else bp
        url = '/%s' % cfg.resource_name_plural

        view_func = APIView.as_view(cfg.endpoint_name, cfg, **kwargs)

        def reg_methods(meths):
            return [m for m in meths if m in for_methods]

        methods = reg_methods(['GET', 'POST'])
        if len(methods) > 0:
            reg_with.add_url_rule(url,
                                  view_func=view_func,
                                  methods=methods)

        methods = reg_methods(['GET', 'PUT', 'DELETE'])
        if len(methods) > 0:
            reg_with.add_url_rule('%s/<ident>' % url,
                                  view_func=view_func,
                                  methods=methods)

        methods = reg_methods(['GET'])
        if len(methods) > 0:
            if cfg.use_links:
                    reg_with.add_url_rule('%s/<ident>/links/<link>' % url,
                                          view_func=view_func,
                                          methods=methods)
            else:
                reg_with.add_url_rule('%s/<ident>/<link>' % url,
                                      view_func=view_func,
                                      methods=methods)
