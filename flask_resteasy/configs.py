# coding=utf-8
"""
    flask_resteasy.configs
    ~~~~~~~~~~~~~~~~~~~~~~

"""
import datetime
import json

from flask import current_app
from flask import url_for

from sqlalchemy.inspection import inspect

from inflection import underscore, camelize, singularize, pluralize

from flask_resteasy.factories import ParserFactory
from flask_resteasy.factories import ProcessorFactory
from flask_resteasy.factories import BuilderFactory

EXCLUDES = {'to_model',
            'from_model',
            'relationship',
            'sort',
            'filter',
            'include',
            'all'}


class APIConfig(object):
    """The default configuration class used when registering API endpoints.

    The configuration is based on conventions and sane defaults that
    allows for quickly creating REST APIs.

    The settings comply with the `must have` requirements for the
    evolving `JSON API <http://www.jsonapi.org>`_ standard.

    Variations of this configuration can be created by extending this
    class or by setting arguments when registering APIs and/or creating
    the APIManager.

    Configuration classes are instantiated when models are registered.  Each
    endpoint registered will have an associated configuration instance.

    :param model_class: :class:`flask.ext.sqlalchemy.Model`
                            registered for the endpoint

    :param excludes:

        To override default behaviour, excluded fields and relationships can be
        specified as a dictionary of key value pairs.

         * `to_model` - exclude from :attr:`allowed_to_model`
         * `from_model` - exclude from :attr:`allowed_from_model`
         * `relationship` - excludes from :attr:`allowed_relationships`
         * `sort` - excludes from :attr:`allowed_sort`
         * `filter` - exclude from :attr:`allowed_filter`
         * `include` - exclude from :attr:`allowed_include`
         * `all` - exclude from everything

         For example::

         {'to_model': ['created', 'updated'], 'from_model': ['password']}

         Exclusions can be set when registering endpoints by calling
         :meth:`flask_resteasy.views.APIManager.register_api` or for all
         endpoints when creating the :class:`flask_resteasy.views.APIManager`.
    """
    def __init__(self, model_class, excludes, max_per_page, http_methods,
                 bp_name):
        self._model = model_class
        self._excludes = excludes
        self._max_per_page = max_per_page
        self._http_methods = http_methods
        self._bp_name = bp_name

        # These attributes are set on access because some
        # SQLAlchemy models may not be initialized yet.
        # For example SQLAlchemy back refs will not be set until the model
        # creating the back ref is initialized.
        self._fields = None
        self._field_types = None
        self._relationship_fields = None
        self._relationship_types = None
        self._resource_name = None
        self._resource_name_plural = None
        self._allowed_to_model = None
        self._allowed_from_model = None
        self._allowed_relationships = None
        self._allowed_sort = None
        self._allowed_filter = None
        self._allowed_include = None
        self._excludes_for_all = None
        self._private_fields = None
        self._endpoint_name = None
        self._relationships = None

    @property
    def model_class(self):
        """:class:`flask.ext.sqlalchemy.Model` registered for the endpoint
        """
        return self._model

    @property
    def db(self):
        """:class:`flask.ext.sqlalchemy.SQLAlchemy` instance
        """
        return current_app.api_manager.db

    @property
    def api_manager(self):
        """:class:`flask_resteasy.views.APIManager` instance
        """
        return current_app.api_manager

    @property
    def max_per_page(self):
        """Maximum items returned per page
        """
        return self._max_per_page

    @property
    def http_methods(self):
        """ HTTP methods that are available for this model's configuration
        """
        return self._http_methods

    @property
    def fields(self):
        """All fields defined for the :attr:`model_class`.
        """
        return self._get_fields()

    @property
    def relationship_fields(self):
        """Fields with the postfix of :attr:`relationship_field_id_postfix`
        These should be all the foreign key fields.
        """
        return self._get_relationship_fields()

    @property
    def private_fields(self):
        """Fields with the prefix :attr:`private_field_prefix`.
        """
        return self._get_private_fields()

    @property
    def field_types(self):
        """All field types for the :attr:`model_class`
        """
        return self._get_field_types()

    @property
    def relationships(self):
        """Relationships defined for the :attr:`model_class`. These are
        links to other model instances, either directly or via a list object.
        Note this also includes an back refs created from other models.
        """
        return self._get_relationships()

    @property
    def relationship_types(self):
        """Relationship types for the :attr:`model_class`
        """
        return self._get_relationship_types()

    @property
    def allowed_from_model(self):
        """Fields that are marshaled from the :attr:`model_class`
        to JSON responses. The default is all fields minus
        private fields, relationship fields and any exclusions.
        """
        return self._get_allowed_from_model()

    @property
    def allowed_to_model(self):
        """Fields that are marshaled from the JSON request to the
        :attr:`model_class`. The default is all fields
        minus private fields, relationship fields, id field and any exclusions.
        """
        return self._get_allowed_to_model()

    @property
    def allowed_relationships(self):
        """Relationships that are  marshaled to and from the models
        and JSON requests and responses. The default is all relationships.
        """
        # todo - do we need to break out into allowed_rel_to_model?
        # and allow_rel_from_model?
        return self._get_allowed_relationships()

    @property
    def allowed_sort(self):
        """Fields that can be sorted. The default is all allowed relationships.
        """
        return self._get_allowed_sort()

    @property
    def allowed_filter(self):
        """Fields that can be filtered. The default
        is :attr:`allowed_from_model`.
        """
        return self._get_allowed_filter()

    @property
    def allowed_include(self):
        """Relationships that can be side-load in JSON responses.
        The default is :attr:`allowed_from_model`.
        """
        return self._get_allowed_include()

    @property
    def json_case(self):
        """Function used to convert the case from model fields to json nodes.
        The default is lowercase underscore.
        """
        return self._get_json_case()

    @property
    def model_case(self):
        """Function used to convert the case from json nodes to model fields.
        The default is lowercase underscore.
        """
        return self._get_model_case()

    @property
    def model_to_json_type_converters(self):
        """Functions used to convert model fields to json types.
        """
        return self._get_model_to_json_type_converters()

    @property
    def private_field_prefix(self):
        """Prefix for fields handled as private fields. The
        default is `_`, for example `_field`.
        """
        return self._get_private_field_prefix()

    @property
    def relationship_field_id_postfix(self):
        """Prefix for fields handled as relationship id fields. The
        default is `_id`, for example `field_id`
        """
        return self._get_relationship_field_id_postfix()

    @property
    def id_field(self):
        """Primary key field name for model class. The default is `id`.
        """
        return self._get_id_field()

    @property
    def resource_name(self):
        """The resource name for the registered model.  The default is
        the model_class.__table__.name in lowercase.
        """
        return self._get_resource_name()

    @property
    def resource_name_case(self):
        """Function used to convert the resource name case.  The default
        is lowercase with underscores.
        """
        return self._get_resource_name_case()

    @property
    def resource_name_plural(self):
        """Plural name for resource.
        """
        return self._get_resource_name_plural()

    @property
    def endpoint_name(self):
        """Name used when registering the endpoint.
        """
        return self._get_endpoint_name()

    @property
    def use_link_nodes(self):
        """Switch for using `links` and `linked` nodes in json responses
        and url routes for accessing resources.  To be JSON API compliant this
        switch is set to True by default.
        """
        return self._get_use_link_nodes()

    @property
    def id_route_param(self):
        """Keyword argument registered for the primary key id in routes. The
        default is `ident`.
        """
        return self._get_id_route_param()

    @property
    def link_route_param(self):
        """Keyword argument registered for a link's primary key id in routes.
        The default is `link`.
        """
        return self._get_link_route_param()

    @property
    def links_node(self):
        """Literal string name for a link node.
        """
        return self._get_links_node()

    @property
    def linked_node(self):
        """Literal string name for a links node.
        """
        return self._get_linked_node()

    @property
    def parser_factory(self):
        """Factory used to create parsers.
        """
        return self._get_parser_factory()

    @property
    def processor_factory(self):
        """Factory used to create processors.
        """
        return self._get_processor_factory()

    @property
    def builder_factory(self):
        """Factory used to create builders.
        """
        return self._get_builder_factory()

    @property
    def url_for(self):
        """Returns the url for the endpoint taking into account if it was
        registered with a Blueprint
        """
        endpoint = self._endpoint_name if not self._bp_name else '.'.join(
            [self._bp_name, self._endpoint_name])
        return url_for(endpoint)

    def allowed_to_as_json(self):
        """Returns allowed fields and relationships that are sent to the client
        for this model's configuration as JSON
        """
        return self._model_to_json(self.allowed_from_model,
                                   self.allowed_relationships)

    def allowed_from_as_json(self):
        """Returns allowed fields and relationships that are sent from the
        client for this model's configuration as JSON
        """
        return self._model_to_json(self.allowed_to_model,
                                   self.allowed_relationships)

    def _model_to_json(self, fields, relationships):
        rv = {}
        for f in fields:
            rv[self.json_case(f)] = self.field_types[f]

        for r in relationships:
            if self.use_link_nodes and self.links_node not in rv:
                rv[self.links_node] = {}
            if self.use_link_nodes:
                rv[self.links_node][self.json_case(r)] = \
                    self.relationship_types[r]
            else:
                rv[self.json_case(r)] = self.relationship_types[r]
        return json.dumps(rv, sort_keys=True, indent=4, separators=(',', ': '))

    @staticmethod
    def _get_model_case():
        return lambda s: underscore(s)

    @staticmethod
    def _get_json_case():
        return lambda s: underscore(s)

    @staticmethod
    def _get_model_to_json_type_converters():
        return {"DATETIME": datetime.datetime.isoformat}

    def _get_fields(self):
        if self._fields is None:
            self._fields = set(
                [c for c in inspect(self.model_class).column_attrs._data])
        return self._fields

    def _get_field_types(self):
        if self._field_types is None:
            self._field_types = {c.name: str(c.type)
                                 for c in self.model_class.__table__.columns}
        return self._field_types

    def _get_relationship_types(self):
        if self._relationship_types is None:
            relations = inspect(self.model_class).relationships._data
            self._relationship_types = {
                n: relations[n]._dependency_processor.direction.name
                for n in relations}
        return self._relationship_types

    def _get_relationship_fields(self):
        if self._relationship_fields is None:
            self._relationship_fields = set(
                [n for n in self.fields
                 if n.endswith(self.relationship_field_id_postfix)])
        return self._relationship_fields

    @staticmethod
    def _get_resource_name_case():
        return lambda s: s.lower()

    def _get_resource_name(self):
        if self._resource_name is None:
            self._resource_name = self.resource_name_case(
                singularize(str(self.model_class.__table__.name)))
        return self._resource_name

    def _get_resource_name_plural(self):
        if self._resource_name_plural is None:
            self._resource_name_plural = pluralize(self.resource_name)
        return self._resource_name_plural

    def _get_allowed_to_model(self):
        if self._allowed_to_model is None:
            self._allowed_to_model = set(
                map(self._get_model_case(),
                    (self.fields - self.private_fields -
                     self.relationship_fields - {self.id_field} -
                     self._get_excludes_for('to_model'))))
        return self._allowed_to_model

    def _get_allowed_from_model(self):
        if self._allowed_from_model is None:
            self._allowed_from_model = set(
                map(self._get_model_case(),
                    (self.fields - self.private_fields -
                     self.relationship_fields -
                     self._get_excludes_for('from_model'))))
        return self._allowed_from_model

    def _get_allowed_relationships(self):
        if self._allowed_relationships is None:
            self._allowed_relationships = set(
                map(self._get_model_case(),
                    (self._get_relationships() -
                     self._get_excludes_for('relationship'))))
        return self._allowed_relationships

    def _get_allowed_sort(self):
        if self._allowed_sort is None:
            self._allowed_sort = set(
                map(self._get_model_case(),
                    self._get_allowed_from_model() -
                    self._get_excludes_for('sort')))
        return self._allowed_sort

    def _get_allowed_filter(self):
        if self._allowed_filter is None:
            self._allowed_filter = set(
                map(self._get_model_case(),
                    self._get_allowed_from_model() -
                    self._get_excludes_for('filter')))
        return self._allowed_filter

    def _get_allowed_include(self):
        if self._allowed_include is None:
            self._allowed_include = set(
                map(self._get_model_case(),
                    (self._get_allowed_relationships() -
                     self._get_excludes_for('include'))))
        return self._allowed_include

    def _get_excludes_for(self, key):
        assert key in EXCLUDES, 'Exclude [%s] is not valid' % key
        if self._excludes is not None and key in self._excludes:
            # we can only check excludes that are not 'all' and are assigned
            # directly to this model
            assert key == 'all' or set(self._excludes[key]) <= (
                self._get_relationships() | self._get_fields()), \
                'Invalid excluded field or relationship'
            rv = (set(self._excludes[key]) |
                  self._get_excludes_for_all() |
                  self.api_manager.get_excludes_for(key))
        else:
            rv = (self._get_excludes_for_all() |
                  self.api_manager.get_excludes_for(key))
        return rv

    def _get_excludes_for_all(self):
        if self._excludes_for_all is None:
            if self._excludes is not None and 'all' in self._excludes:
                self._excludes_for_all = set(self._excludes['all'])
            else:
                self._excludes_for_all = set([])
        return self._excludes_for_all

    def _get_private_fields(self):
        if self._private_fields is None:
            self._private_fields = set(
                [n for n in self.fields
                 if n.startswith(self.private_field_prefix)])
        return self._private_fields

    def _get_endpoint_name(self):
        if self._endpoint_name is None:
            self._endpoint_name = ''.join([self.resource_name, '_api'])
        return self._endpoint_name

    def _get_relationships(self):
        if self._relationships is None:
            self._relationships = set(
                [c for c in inspect(self.model_class).relationships._data])
        return self._relationships
    
    def _get_use_link_nodes(self):
        return True

    @staticmethod
    def _get_id_field():
        return 'id'

    @staticmethod
    def _get_relationship_field_id_postfix():
        return '_id'

    @staticmethod
    def _get_private_field_prefix():
        return '_'

    @staticmethod
    def _get_id_route_param():
        return 'ident'

    @staticmethod
    def _get_link_route_param():
        return 'link'

    @staticmethod
    def _get_links_node():
        return 'links'

    @staticmethod
    def _get_linked_node():
        return 'linked'

    @staticmethod
    def _get_parser_factory():
        return ParserFactory

    @staticmethod
    def _get_processor_factory():
        return ProcessorFactory

    @staticmethod
    def _get_builder_factory():
        return BuilderFactory


class EmberConfig(APIConfig):
    """Provides the settings to be compatible with the Ember.js
    `REST Adapter <http://emberjs.com/api/data/classes/DS.RESTAdapter.html>`_.

    Currently Ember's REST adapter is not fully JSON compliant.  It does
    not support `links` and `linked` nodes.

    Ember.js also prefers Camel case for JSON nodes and resource names.
    """
    def _get_use_link_nodes(self):
        return False

    @staticmethod
    def _get_json_case():
        return lambda s: camelize(s, False)

    @staticmethod
    def _get_resource_name_case():
        return lambda s: camelize(s, False)
