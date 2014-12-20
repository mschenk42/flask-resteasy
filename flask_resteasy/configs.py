# coding=utf-8
"""
    flask_resteasy.configs
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
import datetime

from inflection import underscore, camelize, singularize, pluralize

from .factories import ParserFactory, ProcessorFactory, BuilderFactory


class JSONAPIConfig(object):
    def __init__(self, model_class, app, db, api_manager):
        self._model = model_class
        self._app = app
        self._db = db
        self._api_manager = api_manager

    @property
    def model_class(self):
        return self._model

    @property
    def app(self):
        return self._app

    @property
    def db(self):
        return self._db

    @property
    def api_manager(self):
        return self._api_manager

    @property
    def to_model_field(self):
        return lambda s: underscore(s)

    @property
    def to_json_node(self):
        return lambda s: camelize(s, False)

    @property
    def to_json_converters(self):
        return {"DATETIME": datetime.datetime.isoformat}

    @property
    def field_names(self, exclude=None):
        return set([c.name for c in self.model_class.__table__.columns if
                    not exclude or c.name not in exclude])

    @property
    def field_types(self):
        return {c.name: str(c.type)
                for c in self.model_class.__table__.columns}

    @property
    def relationship_fields(self):
        return set([n for n in self.field_names if
                    n.endswith(self.relationship_field_id_postfix)])

    @property
    def resource_name_converter(self):
        return lambda s: camelize(s, False)

    @property
    def resource_name(self):
        return self.resource_name_converter(
            singularize(str(self.model_class.__table__.name.lower())))

    @property
    def resource_name_plural(self):
        return pluralize(self.resource_name)

    @property
    def fields_to_model(self):
        return (self.field_names - self.private_fields -
                self.relationship_fields - {self.id_field})

    @property
    def fields_to_json(self):
        return self.field_names - self.private_fields - \
            self.relationship_fields

    @property
    def private_fields(self):
        return set([n for n in self.field_names
                    if n.startswith(self.private_field_prefix)])

    @property
    def endpoint_name(self):
        return ''.join([self.resource_name, self.endpoint_postfix])

    @property
    def relationships(self):
        return set([n for n in self.model_class._sa_class_manager
                    if n not in self.field_names])

    @property
    def use_link_nodes(self):
        return True

    @property
    def id_field(self):
        return 'id'

    @property
    def endpoint_postfix(self):
        return '_api'

    @property
    def relationship_field_id_postfix(self):
        return '_id'

    @property
    def private_field_prefix(self):
        return '_'

    @property
    def id_route_param(self):
        return 'ident'

    @property
    def link_route_param(self):
        return 'link'

    @property
    def links_node(self):
        return 'links'

    @property
    def linked_node(self):
        return 'linked'

    @property
    def parser_factory(self):
        return ParserFactory

    @property
    def processor_factory(self):
        return ProcessorFactory

    @property
    def builder_factory(self):
        return BuilderFactory


class EmberConfig(JSONAPIConfig):
    @property
    def use_link_nodes(self):
        return False