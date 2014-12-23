# coding=utf-8
"""
    flask_resteasy.views
    ~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2014 by Michael Schenk.
    :license: BSD, see LICENSE for more details.
"""
from flask.views import MethodView
from flask import jsonify

from .configs import JSONAPIConfig

HTTP_METHODS = {'GET', 'POST', 'PUT', 'DELETE'}


class APIView(MethodView):
    def __init__(self, cfg):
        self._cfg = cfg

    def get(self, **kwargs):
        parser = self._cfg.parser_factory.create(self._cfg, **kwargs)
        processor = self._cfg.processor_factory.create(self._cfg, parser)
        if parser.link:
            link_cfg = self._cfg.api_manager.get_cfg(
                self._cfg.resource_name_case(parser.link))
            builder = link_cfg.builder_factory.create(link_cfg, processor)
        else:
            builder = self._cfg.builder_factory.create(self._cfg, processor)

        return jsonify(builder.json_dic)

    def post(self):
        parser = self._cfg.parser_factory.create(self._cfg)
        processor = self._cfg.processor_factory.create(self._cfg, parser)
        builder = self._cfg.builder_factory.create(self._cfg, processor)
        url = builder.urls[0] if len(builder.urls) == 1 else builder.urls

        return jsonify(builder.json_dic), 201, {'Location': url}

    def delete(self, **kwargs):
        parser = self._cfg.parser_factory.create(self._cfg, **kwargs)
        self._cfg.processor_factory.create(self._cfg, parser)

        return jsonify({})

    def put(self, **kwargs):
        parser = self._cfg.parser_factory.create(self._cfg, **kwargs)
        processor = self._cfg.processor_factory.create(self._cfg, parser)
        builder = self._cfg.builder_factory.create(self._cfg, processor)

        return jsonify(builder.json_dic)


class APIManager(object):
    def __init__(self, app, db, cfg_class=JSONAPIConfig, decorators=None,
                 bp=None, excludes=None, methods=None):
        self._app = None
        self._db = None
        self._model_for_resources = {}
        self._cfg_for_resources = {}
        self._cfg_class = cfg_class
        self._excludes = excludes
        self._bp = bp
        if methods:
            self._methods = set(methods)
        else:
            self._methods = {'GET'}
        if decorators:
            APIView.decorators = decorators
        self.init_app(app, db)

    def init_app(self, app, db):
        self._app = app
        self._db = db

    def _register_cfg(self, view, resource_singular, resource_plural):
        self._cfg_for_resources[resource_singular] = view
        self._cfg_for_resources[resource_plural] = view

    def _register_model(self, model_class, resource_singular, resource_plural):
        self._model_for_resources[resource_singular] = model_class
        self._model_for_resources[resource_plural] = model_class

    def get_cfg(self, resource_name):
        return self._cfg_for_resources[resource_name]

    def get_model(self, resource_name):
        return self._model_for_resources[resource_name]

    def get_excludes_for(self, key):
        if self._excludes is not None and key in self._excludes:
            return set(self._excludes[key]) | self.get_excludes_for_all()
        else:
            return self.get_excludes_for_all()

    def get_excludes_for_all(self):
        if self._excludes is not None and 'all' in self._excludes:
            return set(self._excludes['all'])
        else:
            return set([])

    def register_api(self, model_class, cfg_class=None, methods=None,
                     bp=None, excludes=None):
        if methods:
            methods = set(methods)
        else:
            methods = self._methods

        if cfg_class is None:
            cfg_class = self._cfg_class

        cfg = cfg_class(model_class, self._app, self._db, self, excludes)

        self._register_cfg(cfg, cfg.resource_name, cfg.resource_name_plural)
        self._register_model(model_class, cfg.resource_name,
                             cfg.resource_name_plural)

        if bp is not None:
            reg_with = bp
        elif self._bp is not None:
            reg_with = self._bp
        else:
            reg_with = self._app

        url = '/%s' % cfg.resource_name_plural

        view_func = APIView.as_view(cfg.endpoint_name, cfg)

        reg_methods = list({'GET', 'POST'} & methods)
        if len(reg_methods) > 0:
            reg_with.add_url_rule(url,
                                  view_func=view_func,
                                  methods=reg_methods)

        reg_methods = list({'GET', 'PUT', 'DELETE'} & methods)
        if len(reg_methods) > 0:
            reg_with.add_url_rule('%s/<%s>' % (url, cfg.id_route_param),
                                  view_func=view_func,
                                  methods=reg_methods)

        reg_methods = list({'GET'} & methods)
        if len(reg_methods) > 0:
            if cfg.use_link_nodes:
                    reg_with.add_url_rule('%s/<%s>/%s/<%s>' %
                                          (url, cfg.id_route_param,
                                           cfg.links_node,
                                           cfg.link_route_param),
                                          view_func=view_func,
                                          methods=reg_methods)
            else:
                reg_with.add_url_rule('%s/<%s>/<%s>' %
                                      (url, cfg.id_route_param,
                                       cfg.link_route_param),
                                      view_func=view_func,
                                      methods=reg_methods)
