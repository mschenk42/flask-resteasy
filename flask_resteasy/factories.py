# coding=utf-8
"""
    flask_resteasy.factories
    ~~~~~~~~~~~~~~~~~~~~~~~~

"""
from flask import request
from flask_resteasy.parsers import GetRequestParser
from flask_resteasy.parsers import PutRequestParser
from flask_resteasy.parsers import PostRequestParser
from flask_resteasy.parsers import DeleteRequestParser
from flask_resteasy.processors import GetRequestProcessor
from flask_resteasy.processors import PutRequestProcessor
from flask_resteasy.processors import PostRequestProcessor
from flask_resteasy.processors import DeleteRequestProcessor
from flask_resteasy.builders import ResponseBuilder


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
            post_process = cfg.api_manager.get_post_process(cfg.resource_name)
            if post_process and post_process[0] in request.json:
                return post_process[1](cfg, req_par)
            else:
                return PostRequestProcessor(cfg, req_par)
        elif request.method == 'DELETE':
            return DeleteRequestProcessor(cfg, req_par)
        elif request.method == 'PUT':
            put_process = cfg.api_manager.get_put_process(cfg.resource_name)
            if put_process and put_process[0] in request.json:
                return put_process[1](cfg, req_par)
            else:
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
