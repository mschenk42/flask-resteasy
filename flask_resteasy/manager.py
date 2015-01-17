# coding=utf-8
"""
    flask_resteasy.manager
    ~~~~~~~~~~~~~~~~~~~~~~

"""
from flask import render_template
from flask import Blueprint

from inflection import singularize

from flask_resteasy.configs import APIConfig
from flask_resteasy.views import APIView
from flask_resteasy.errors import UnableToProcess
from flask_resteasy.errors import handle_errors


class APIManager(object):
    """Main class to register the Flask RestEasy extension with
    the Flask application instance.

    :param app: :class:`flask.Flask` application instance

    :param db: :class:`flask.ext.sqlalchemy.SQLAlchemy` instance

    :param cfg_class: global default configuration class, default is
                      :class:`flask_resteasy.configs.APIConfig`

    :param decorators: list of decorators to
                       apply to all registered HTTP methods

    :param bp: global default Flask Blueprint to register all routes with

    :param excludes: see `exclude` info in class
                     :class:`flask_resteasy.configs.APIConfig`

    :param methods: global default list of HTTP methods to register
                    for each endpoint, the default setting is ['GET']

    :param error_handler: error_handler for UnableToProcess exceptions
    """

    def __init__(self, app=None, db=None, cfg_class=APIConfig, decorators=None,
                 bp=None, excludes=None, methods=None, max_per_page=20,
                 error_handler=None):
        self._app = app
        self._db = db
        self._cfg_class = cfg_class
        self._bp = bp
        self._excludes = excludes
        self._methods = methods
        self._model_for_resources = {}
        self._cfg_for_resources = {}
        self._max_per_page = max_per_page
        if app is not None:
            self.init_app(app, db, cfg_class, decorators,
                          bp, excludes, methods, max_per_page, error_handler)

    def init_app(self, app, db, cfg_class=APIConfig, decorators=None,
                 bp=None, excludes=None, methods=None, max_per_page=20,
                 error_handler=None):
        """Stores the :class:`flask.Flask` application object,
        :class:`flask.ext.sqlalchemy.SQLAlchemy` object and any global
        default settings.

        Use this method if you need to instantiate the APIManager before
        creating the Flask and SQLAlchemy application objects.

        :param app: :class:`flask.Flask` application instance

        :param db: :class:`flask.ext.sqlalchemy.SQLAlchemy` instance

        :param cfg_class: global default configuration class, default is
                          :class:`flask_resteasy.configs.APIConfig`

        :param decorators: list of decorators to
                           apply to all registered HTTP methods

        :param bp: global default Flask Blueprint to register all routes with

        :param excludes: see `exclude` info in class
                         :class:`flask_resteasy.configs.APIConfig`

        :param methods: global default list of HTTP methods to register
                        for each endpoint, the default setting is ['GET']

        :param max_per_page: global default maximum items returned
                             per page for a paginated response

        :param error_handler: error_handler for UnableToProcess exceptions
        """
        self._app = app
        self._app.api_manager = self
        self._db = db
        self._cfg_class = cfg_class
        self._excludes = excludes
        self._bp = bp

        if methods:
            self._methods = set(methods)
        else:
            self._methods = {'GET'}
        self._max_per_page = max_per_page

        if decorators:
            APIView.decorators = decorators

        # Don't use relative imports with Flask, had an odd issues only with
        # Python 3 when registering error handlers,  if I used a relative
        # import for the exception class, Flask registered the exception with
        # '.ext.' in the package name.  This caused the Flask error handling to
        # not find a match for the exception when doing the isinstance
        # type check.
        #
        # Below is the code that fails with Python 3.
        #
        # if isinstance(e, typecheck):
        # return handler(e)
        #
        if error_handler is None:
            error_handler = handle_errors
        self._app.register_error_handler(UnableToProcess, error_handler)

        def resteasy_api():
            """View API information for registered endpoints
            """
            return render_template('api_info.html', cfgs=self.configs)

        if self._app.debug:
            re_bp = Blueprint('resteasy_bp', __name__,
                              template_folder="templates")
            re_bp.add_url_rule('/api_info', 'resteasy_api', resteasy_api)
            self._app.register_blueprint(re_bp)

    @property
    def db(self):
        """
        :class:`flask.ext.sqlalchemy.SQLAlchemy` instance
        """
        return self._db

    @property
    def configs(self):
        """Dictionary of configurations objects by resource name
        """
        return self._cfg_for_resources

    def get_cfg(self, resource_name):
        """Returns the :class:`flask_resteasy.configs.APIConfig` for
        a resource.

        :param resource_name: name of resource
        """
        resource_name = singularize(resource_name)
        if resource_name not in self._cfg_for_resources:
            raise UnableToProcess('Resource Error',
                                  'Resource [%s] not found' % resource_name)
        return self._cfg_for_resources[resource_name]

    def get_model(self, resource_name):
        """Returns the model :class:`flask.ext.sqlalchemy.Model`
        for a resource.

        :param resource_name: name of resource
        """
        resource_name = singularize(resource_name)
        if resource_name not in self._model_for_resources:
            raise UnableToProcess('Resource Error',
                                  'Resource [%s] not found' % resource_name)
        return self._model_for_resources[resource_name]

    def _register_cfg(self, cfg, resource_name):
        resource_name = singularize(resource_name)
        self._cfg_for_resources[resource_name] = cfg

    def _register_model(self, model_class, resource_name):
        resource_name = singularize(resource_name)
        self._model_for_resources[resource_name] = model_class

    def get_excludes_for(self, key):
        """Returns an exclude list for a specific key.

        :param key: exclude keyword, for list of keys see `exclude` info in
                   class :class:`flask_resteasy.configs.APIConfig`
        """
        if self._excludes is not None and key in self._excludes:
            return set(self._excludes[key]) | self.get_excludes_for_all()
        else:
            return self.get_excludes_for_all()

    def get_excludes_for_all(self):
        """Returns the exclude list for key 'all'.
        For list of keys see `exclude` info in class
        :class:`flask_resteasy.configs.APIConfig`
        """
        if self._excludes is not None and 'all' in self._excludes:
            return set(self._excludes['all'])
        else:
            return set([])

    def register_api(self, model_class, cfg_class=None, methods=None,
                     bp=None, excludes=None, max_per_page=None):
        """Registers an API endpoint for a SQLAlchemy model.

        :param model_class: class:`flask.ext.sqlalchemy.Model` to registered
                            for the endpoint

        :param cfg_class: configuration class, if None provided will
                          default to :class:`flask_resteasy.configs.APIConfig`

        :param methods: list of HTTP methods to register
                        for this endpoint, the default setting is ['GET']

        :param bp: Flask Blueprint to register this API endpoint's routes.
                   If Blueprint is not provided routes are registered with
                   the Flask application object.

        :param excludes: excludes to apply to this API endpoint,
                         see `exclude` info in class
                         :class:`flask_resteasy.configs.APIConfig`

        :param max_per_page: default maximum items returned per page
                             for a paginated response

        This example registers the models using default settings
        set when initializing the APIManager::

            api_manager = APIManager(app, db, cfg_class=APIConfig,
                                     methods=['GET', 'PUT', 'POST', 'DELETE'])

            api_manager.register_api(Product)
            api_manager.register_api(Distributor)
            api_manager.register_api(StockCount)
            api_manager.register_api(StockLevel)

        """
        if methods:
            methods = set(methods)
        else:
            methods = self._methods

        if max_per_page is None:
            max_per_page = self._max_per_page

        if cfg_class is None:
            cfg_class = self._cfg_class

        # create API configuration object for the model class
        cfg = cfg_class(model_class, excludes, max_per_page, methods)

        # register API configuration object by resource name
        self._register_cfg(cfg, cfg.resource_name)

        # register model class by resource name
        self._register_model(model_class, cfg.resource_name)

        # register with blueprint or application?
        if bp is not None:
            # use blueprint pass into this method
            has_blueprint = True
            reg_with = bp
        elif self._bp is not None:
            # use blueprint set on initialization of APIManager
            has_blueprint = True
            reg_with = self._bp
        else:
            # no blueprint, register on the Flask app instance
            has_blueprint = False
            reg_with = self._app

        # root resource url, i.e. /products
        url = '/%s' % cfg.resource_name_plural

        # create view function for endpoint with API configuration object
        view_func = APIView.as_view(cfg.endpoint_name, cfg)

        # register routes
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

        # register blueprint with app
        if has_blueprint:
            self._app.register_blueprint(reg_with)
