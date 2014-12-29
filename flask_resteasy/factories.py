# coding=utf-8
"""
    flask_resteasy.factories
    ~~~~~~~~~~~~~~~~~~~~~~~~

"""
from flask import request

from .parsers import RequestParser
from .processors import GetRequestProcessor, PostRequestProcessor
from .processors import DeleteRequestProcessor, PutRequestProcessor
from .builders import ResponseBuilder


class ParserFactory(object):
    """Factory for creating request parser objects.
    """
    @staticmethod
    def create(cfg, **kwargs):
        return RequestParser(cfg, **kwargs)


class ProcessorFactory(object):
    """Factory for creating request processor objects.
    """
    @staticmethod
    def create(cfg, request_parser):
        if request.method == 'GET':
            return GetRequestProcessor(cfg, request_parser)
        elif request.method == 'POST':
            return PostRequestProcessor(cfg, request_parser)
        elif request.method == 'DELETE':
            return DeleteRequestProcessor(cfg, request_parser)
        elif request.method == 'PUT':
            return PutRequestProcessor(cfg, request_parser)


class BuilderFactory(object):
    """Factory for creating response builder objects.
    """
    @staticmethod
    def create(cfg, response_builder):
        return ResponseBuilder(cfg, response_builder)
