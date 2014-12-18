from inflection import underscore, camelize, singularize, pluralize

from .parsers import ParserFactory
from .processors import ProcessorFactory
from .builders import BuilderFactory


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
    def to_model_tag(self):
        return lambda s: underscore(s)

    @property
    def to_json_tag(self):
        return lambda s: camelize(s, False)

    @property
    def resource_name_converter(self):
        return lambda s: camelize(s, False)

    @property
    def field_names(self, exclude=None):
        return set([c.name for c in self.model_class.__table__.columns if
                    not exclude or c.name not in exclude])

    @property
    def field_types(self):
        return {c.name: str(c.type)
                for c in self.model_class.__table__.columns}

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
        return (self.field_names - self.private_fields -
                self.linked_fields - {self.id_keyword})

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
    def use_links(self):
        return True

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
        return ParserFactory

    @property
    def processor_factory(self):
        return ProcessorFactory

    @property
    def builder_factory(self):
        return BuilderFactory


class EmberConfig(JSONAPIConfig):
    @property
    def use_links(self):
        return False