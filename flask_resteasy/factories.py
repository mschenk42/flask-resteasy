# coding=utf-8
"""
    flask_resteasy.factories
    ~~~~~~~~~~~~~~~~~~~~~~~~

"""
from flask import request

from .parsers import GetRequestParser, PostRequestParser, PutRequestParser
from .parsers import DeleteRequestParser
from .processors import GetRequestProcessor, PostRequestProcessor
from .processors import DeleteRequestProcessor, PutRequestProcessor
from .builders import ResponseBuilder


class ParserFactory(object):
    """Factory for creating request parser objects.
    """
    @staticmethod
    def create(cfg, **kwargs):
        """Factory method for creating RequestParser.

        :param cfg: :class:`flask_resteasy.configs.APIConfig` instance

        :param kwargs: dictionary of keyword arguments which contains
                       route parameters and query parameters for the
                       current HTTP request
        """
        if request.method == 'GET':
            return GetRequestParser(cfg, **kwargs)
        elif request.method == 'POST':
            return PostRequestParser(cfg, **kwargs)
        elif request.method == 'DELETE':
            return DeleteRequestParser(cfg, **kwargs)
        elif request.method == 'PUT':
            return PutRequestParser(cfg, **kwargs)


class ProcessorFactory(object):
    """Factory for creating request processor objects.
    """
    @staticmethod
    def create(cfg, req_par):
        """Factory method for creating RequestProcessor.

        :param cfg: :class:`flask_resteasy.configs.APIConfig` instance

        :param req_par: :class:`flask_resteasy.parsers.RequestParser`
                        for the current HTTP request
        """
        if request.method == 'GET':
            return GetRequestProcessor(cfg, req_par)
        elif request.method == 'POST':
            return PostRequestProcessor(cfg, req_par)
        elif request.method == 'DELETE':
            return DeleteRequestProcessor(cfg, req_par)
        elif request.method == 'PUT':
            return PutRequestProcessor(cfg, req_par)


class BuilderFactory(object):
    """Factory for creating response builder objects.
    """
    @staticmethod
    def create(cfg, req_proc):
        """Factoring method for creating ResponseBuilder.

        :param cfg: :class:`flask_resteasy.configs.APIConfig` instance

        :param req_proc: :class:`flask_resteasy.processors.RequestProcessor`
                         for the current HTTP request
        """
        return ResponseBuilder(cfg, req_proc)
