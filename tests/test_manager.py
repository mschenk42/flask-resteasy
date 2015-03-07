import unittest

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask_resteasy.manager import APIManager

db = SQLAlchemy()
app = Flask(__name__)


class TestManager(unittest.TestCase):

    def test_register_processes(self):

        class TestModel(db.Model):
            __tablename__ = 'testmodel'
            id = db.Column('id', db.Integer, primary_key=True)

        class TestPostProcess(object):
            pass

        class TestPutProcess(object):
            pass

        api_manager = APIManager(
            app=app, db=db, methods={'GET', 'PUT', 'POST'})
        api_manager.register_api(TestModel,
                                 post_process=('action', TestPostProcess),
                                 put_process=('action', TestPutProcess))
        post_process = api_manager.get_post_process('testmodel')
        put_process = api_manager.get_put_process('testmodel')
        self.assertTrue(post_process == ('action', TestPostProcess))
        self.assertTrue(put_process == ('action', TestPutProcess))
