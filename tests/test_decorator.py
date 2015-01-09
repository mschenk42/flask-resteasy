# coding=utf-8
"""
    tests.test_decorator
    ~~~~~~~~~~~~~~

    :copyright: (c) 2014 by Michael Schenk.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from flask import Flask
from flask import abort

from flask_sqlalchemy import SQLAlchemy

from flask_resteasy.manager import APIManager


class TestDecorator(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.db = SQLAlchemy()
        self.db.init_app(self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = self.app.test_client()

        class Product(self.db.Model):
            """Product model
            """
            __tablename__ = "product"
            id = self.db.Column('id', self.db.Integer, primary_key=True)

        api_manager = APIManager(self.app, self.db, decorators=[a_decorator])
        api_manager.register_api(Product)

    def test_decorator(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 404)

    def get_url(self, resource_url):
        return ''.join(['http://localhost', resource_url])

    def get_headers(self):
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}
        return headers


def a_decorator(f):
    """Decorator for testing register an endpoint with a decorator
    :param f:
    """
    def decorator(*args, **kwargs):
        """Decorator method
        :param args:
        :param kwargs:
        """
        abort(404)
        return f(*args, **kwargs)
    return decorator
