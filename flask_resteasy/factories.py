# coding=utf-8
"""
    flask_resteasy.factories
    ~~~~~~~~~~~~~~~~~~~~~~~~

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
from flask import request

from .parsers import GetRequestParser, PostRequestParser, DeleteRequestParser
from .parsers import PutRequestParser
from .processors import GetRequestProcessor, PostRequestProcessor
from .processors import DeleteRequestProcessor, PutRequestProcessor
from .builders import ResponseBuilder


class ParserFactory(object):
    @staticmethod
    def create(cfg, **kwargs):
        if request.method == 'GET':
            return GetRequestParser(cfg, **kwargs)
        elif request.method == 'POST':
            return PostRequestParser(cfg, **kwargs)
        elif request.method == 'DELETE':
            return DeleteRequestParser(cfg, **kwargs)
        elif request.method == 'PUT':
            return PutRequestParser(cfg, **kwargs)


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
