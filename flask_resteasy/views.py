# coding=utf-8
"""
    flask_resteasy.views
    ~~~~~~~~~~~~~~

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
from flask.views import MethodView
from flask import jsonify

from configs import JSONAPIConfig

HTTP_METHODS = {'GET', 'POST', 'PUT', 'DELETE'}


class APIView(MethodView):
    def __init__(self, cfg):
        self._cfg = cfg

    @property
    def cfg(self):
        return self._cfg

    def get(self, **kwargs):
        parser = self.cfg.parser_factory.create(self.cfg, **kwargs)
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

    def delete(self, **kwargs):
        parser = self.cfg.parser_factory.create(self.cfg, **kwargs)
        self.cfg.processor_factory.create(self.cfg, parser)

        return jsonify({})

    def put(self, **kwargs):
        parser = self.cfg.parser_factory.create(self.cfg, **kwargs)
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

    def register_api(self, model_class, reg_methods=None, bp=None, **kwargs):

        if reg_methods is None:
            reg_methods = HTTP_METHODS

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

        methods = list({'GET', 'POST'}.intersection(reg_methods))
        if len(methods) > 0:
            reg_with.add_url_rule(url,
                                  view_func=view_func,
                                  methods=methods)

        methods = list({'GET', 'PUT', 'DELETE'}.intersection(reg_methods))
        if len(methods) > 0:
            reg_with.add_url_rule('%s/<%s>' % (url, cfg.id_route_param),
                                  view_func=view_func,
                                  methods=methods)

        methods = list({'GET'}.intersection(reg_methods))
        if len(methods) > 0:
            if cfg.use_link_nodes:
                    reg_with.add_url_rule('%s/<%s>/%s/<%s>' %
                                          (url, cfg.id_route_param,
                                           cfg.links_node,
                                           cfg.link_route_param),
                                          view_func=view_func,
                                          methods=methods)
            else:
                reg_with.add_url_rule('%s/<%s>/<%s>' %
                                      (url, cfg.id_route_param,
                                       cfg.link_route_param),
                                      view_func=view_func,
                                      methods=methods)
