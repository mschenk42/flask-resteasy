# coding=utf-8
"""
    flask_resteasy.views
    ~~~~~~~~~~~~~~~~~~~~

"""
from flask.views import MethodView
from flask import jsonify


class APIView(MethodView):
    """Based on the :class:`flask.views.MethodView` provided by the
    Flask framework.

    On each HTTP request for a GET, PUT, POST, DELETE or OPTIONS an instance
    of APIView will be created for the incoming request.

    Note this does not currently support HTTP PATCH request.

    """

    def __init__(self, cfg):
        self._cfg = cfg

    def get(self, **kwargs):
        """Handles HTTP GET requests. The behavior of this method
        can be changed by providing your own factories for
        parsers, processors and builders.

        :param kwargs: dictionary of keyword arguments which contains
                       route parameters and query parameters for the
                       current HTTP request
        """
        parser = self._cfg.parser_factory.create(self._cfg, **kwargs)
        processor = self._cfg.processor_factory.create(self._cfg, parser)
        if parser.link:
            link_cfg = self._cfg.api_manager.get_cfg(
                self._cfg.resource_name_case(parser.link))
            builder = link_cfg.builder_factory.create(link_cfg, processor)
        else:
            builder = self._cfg.builder_factory.create(self._cfg, processor)

        return jsonify(builder.json_dic)

    def post(self, **kwargs):
        """Handles HTTP POST requests. The behavior of this method
        can be changed by providing your own factories for
        parsers, processors and builders.

        :param kwargs: dictionary of keyword arguments which contains
                       route parameters and query parameters for the
                       current HTTP request
        """
        parser = self._cfg.parser_factory.create(self._cfg, **kwargs)
        processor = self._cfg.processor_factory.create(self._cfg, parser)
        builder = self._cfg.builder_factory.create(self._cfg, processor)
        url = builder.urls[0] if len(builder.urls) == 1 else builder.urls

        return jsonify(builder.json_dic), 201, {'Location': url}

    def delete(self, **kwargs):
        """Handles HTTP DELETE requests. The behavior of this method
        can be changed by providing your own factories for
        parsers, processors and builders.

        :param kwargs: dictionary of keyword arguments which contains
                       route parameters and query parameters for the
                       current HTTP request
        """
        parser = self._cfg.parser_factory.create(self._cfg, **kwargs)
        processor = self._cfg.processor_factory.create(self._cfg, parser)
        builder = self._cfg.builder_factory.create(self._cfg, processor)

        return jsonify(builder.json_dic)

    def put(self, **kwargs):
        """Handles HTTP PUT requests. The behavior of this method
        can be changed by providing your own factories for
        parsers, processors and builders.

        :param kwargs: dictionary of keyword arguments which contains
                       route parameters and query parameters for the
                       current HTTP request
        """
        parser = self._cfg.parser_factory.create(self._cfg, **kwargs)
        processor = self._cfg.processor_factory.create(self._cfg, parser)
        builder = self._cfg.builder_factory.create(self._cfg, processor)

        return jsonify(builder.json_dic)
