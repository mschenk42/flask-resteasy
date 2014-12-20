# coding=utf-8
"""
    flask_resteasy.configs
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2014 by Michael Schenk.
    :license: BSD, see LICENSE for more details.
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
    def all_fields(self):
        return self._all_fields()

    @property
    def relationship_fields(self):
        return self._relationship_fields()

    @property
    def private_fields(self):
        return self._private_fields()

    @property
    def field_types(self):
        return self._field_types()

    @property
    def relationships(self):
        return self._relationships()

    @property
    def allowed_from_model(self):
        return self._allowed_from_model()

    @property
    def allowed_to_model(self):
        return self._allowed_to_model()

    @property
    def allowed_relationships(self):
        return self._allowed_relationships()

    @property
    def allowed_to_sort(self):
        return self._allowed_to_sort()

    @property
    def allowed_to_filter(self):
        return self._allowed_to_filter()

    @property
    def allowed_to_include(self):
        return self._allowed_to_include()

    @property
    def json_node_case(self):
        return self._json_node_case()

    @property
    def model_field_case(self):
        return self._model_field_case()

    @property
    def model_to_json_type_converters(self):
        return self._model_to_json_type_converters()

    @property
    def private_field_prefix(self):
        return self._private_field_prefix()

    @property
    def relationship_field_id_postfix(self):
        return self._relationship_field_id_postfix()

    @property
    def id_field(self):
        return self._id_field()

    @property
    def resource_name(self):
        return self._resource_name()

    @property
    def resource_name_case(self):
        return self._resource_name_case()

    @property
    def resource_name_plural(self):
        return self._resource_name_plural()

    @property
    def endpoint_name(self):
        return self._endpoint_name()

    @property
    def use_link_nodes(self):
        return self._use_link_nodes()

    @property
    def id_route_param(self):
        return self._id_route_param()

    @property
    def link_route_param(self):
        return self._link_route_param()

    @property
    def links_node(self):
        return self._links_node()

    @property
    def linked_node(self):
        return self._linked_node()

    @property
    def parser_factory(self):
        return self._parser_factory()

    @property
    def processor_factory(self):
        return self._processor_factory()

    @property
    def builder_factory(self):
        return self._builder_factory()

    def _model_field_case(self):
        return lambda s: underscore(s)

    def _json_node_case(self):
        return lambda s: camelize(s, False)

    def _model_to_json_type_converters(self):
        return {"DATETIME": datetime.datetime.isoformat}

    def _all_fields(self):
        return set([c.name for c in self.model_class.__table__.columns])

    def _field_types(self):
        return {c.name: str(c.type)
                for c in self.model_class.__table__.columns}

    def _relationship_fields(self):
        return set([n for n in self.all_fields if
                    n.endswith(self.relationship_field_id_postfix)])

    def _resource_name_case(self):
        return lambda s: camelize(s, False)

    def _resource_name(self):
        return self.resource_name_case(
            singularize(str(self.model_class.__table__.name.lower())))

    def _resource_name_plural(self):
        return pluralize(self.resource_name)

    def _allowed_to_model(self):
        return (self.all_fields - self.private_fields -
                self.relationship_fields - {self.id_field})

    def _allowed_from_model(self):
        return self.all_fields - self.private_fields - self.relationship_fields

    def _private_fields(self):
        return set([n for n in self.all_fields
                    if n.startswith(self.private_field_prefix)])

    def _endpoint_name(self):
        return ''.join([self.resource_name, '_api'])

    def _relationships(self):
        return set([n for n in self.model_class._sa_class_manager
                    if n not in self.all_fields])

    def _use_link_nodes(self):
        return True

    def _id_field(self):
        return 'id'

    def _relationship_field_id_postfix(self):
        return '_id'

    def _private_field_prefix(self):
        return '_'

    def _id_route_param(self):
        return 'ident'

    def _link_route_param(self):
        return 'link'

    def _links_node(self):
        return 'links'

    def _linked_node(self):
        return 'linked'

    def _parser_factory(self):
        return ParserFactory

    def _processor_factory(self):
        return ProcessorFactory

    def _builder_factory(self):
        return BuilderFactory

    def _allowed_relationships(self):
        return self._relationships()

    def _allowed_to_sort(self):
        return self._allowed_from_model()

    def _allowed_to_filter(self):
        return self._allowed_from_model()

    def _allowed_to_include(self):
        return self._allowed_relationships()


class EmberConfig(JSONAPIConfig):
    def _use_link_nodes(self):
        return False