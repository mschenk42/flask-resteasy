# coding=utf-8
"""
    flask_resteasy.factories
    ~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2014 by Michael Schenk.
    :license: BSD, see LICENSE for more details.
"""
from flask import request

from .parsers import RequestParser
from .processors import GetRequestProcessor, PostRequestProcessor
from .processors import DeleteRequestProcessor, PutRequestProcessor
from .builders import ResponseBuilder


class ParserFactory(object):
    @staticmethod
    def create(cfg, **kwargs):
        return RequestParser(cfg, **kwargs)


class ProcessorFactory(object):
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
    @staticmethod
    def create(cfg, response_builder):
        return ResponseBuilder(cfg, response_builder)
