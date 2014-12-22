# coding: utf-8
"""
    tests.test_api
    ~~~~~~~~~~~~~~

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
import unittest
import os
import json

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from flask_resteasy.views import APIManager
from flask_resteasy.configs import JSONAPIConfig, EmberConfig


app = None
db = SQLAlchemy()


class TestAPI(unittest.TestCase):
    class Distributor(db.Model):
        __tablename__ = 'distributors'

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(64), nullable=False)
        description = db.Column(db.Text)

    class Product(db.Model):
        __tablename__ = 'products'

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(64), nullable=False)
        description = db.Column(db.Text)
        distributor_code = db.Column(db.String(32))
        supplier_code = db.Column(db.String(32))
        lead_time = db.Column(db.Integer)
        min_order_qty = db.Column(db.Integer)
        max_order_qty = db.Column(db.Integer)
        reorder_level = db.Column(db.Integer)
        reorder_qty = db.Column(db.Integer)
        _private_fld = db.Column(db.String(32))
        created = db.Column(db.DATE)
        distributor_id = db.Column(
            db.Integer, db.ForeignKey('distributors.id'),
            nullable=False)
        distributor = db.relationship(
            'Distributor', backref=db.backref(__tablename__))

    class StockCount(db.Model):
        __tablename__ = 'stock_counts'

        id = db.Column(db.Integer, primary_key=True)
        description = db.Column(db.Text)
        processed = db.Column(db.Boolean)
        started_by = db.Column(db.String(64))

    class StockLevel(db.Model):
        __tablename__ = 'stock_levels'

        id = db.Column(db.Integer, primary_key=True)
        on_hand_qty = db.Column(db.Integer)
        processed = db.Column(db.Boolean)

        product_id = db.Column(db.Integer,
                               db.ForeignKey('products.id'))
        product = db.relationship('Product',
                                  backref=db.backref(__tablename__))

        stockcount_id = db.Column(db.Integer,
                                  db.ForeignKey('stock_counts.id'))
        stock_count = db.relationship('StockCount',
                                      backref=db.backref(__tablename__))

    @classmethod
    def setUpClass(cls):
        global app, db

        basedir = os.path.abspath(os.path.dirname(__file__))
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = \
            'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
        db.init_app(app)

    def setUp(self):
        self.ctx = app.app_context()
        self.ctx.push()
        self.client = app.test_client()
        self.create_db()

    def tearDown(self):
        self.destroy_db()

    def create_db(self):
        db.drop_all()
        db.create_all()
        self.load_data()

    def load_data(self):
        distributor1 = TestAPI.Distributor()
        distributor1.name = 'Sysco Inc'
        distributor1.description = "Distributor with a variety of brands"

        distributor2 = TestAPI.Distributor()
        distributor2.name = 'Whole Foods'
        distributor2.description = "Provide fresh and organic produce"

        product1 = TestAPI.Product()
        product1.name = 'Green Lettuce'
        product1.description = 'Organic green lettuce from the state of CA'
        product1.distributor_code = 'SYSCO'
        product1.lead_time = 5
        product1.min_order_qty = 12
        product1.max_order_qty = 144
        product1.reorder_level = 12
        product1.reorder_qty = 24
        product1.distributor = distributor1

        product2 = TestAPI.Product()
        product2.name = 'Red Leaf Lettuce'
        product2.description = 'Organic red leaf lettuce from the state of CA'
        product2.distributor_code = 'SYSCO'
        product2.lead_time = 5
        product2.min_order_qty = 12
        product2.max_order_qty = 144
        product2.reorder_level = 12
        product2.reorder_qty = 24
        product2.distributor = distributor1

        stockcount1 = TestAPI.StockCount()
        stockcount1.description = 'Initial stock count'
        stockcount1.processed = False

        stocklevel1 = TestAPI.StockLevel()
        stocklevel1.on_hand_qty = 12
        stocklevel1.processed = False
        stocklevel1.stock_count = stockcount1
        stocklevel1.product = product1

        stocklevel2 = TestAPI.StockLevel()
        stocklevel2.on_hand_qty = 100
        stocklevel2.processed = False
        stocklevel2.stock_count = stockcount1
        stocklevel2.product = product2

        db.session.add(product1, product2)
        db.session.commit()

    def destroy_db(self):
        db.drop_all()

    def get_url(self, resource_url):
        return ''.join(['http://localhost', resource_url])

    def get_headers(self):
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}
        return headers


class TestJSONAPI(TestAPI):
    @classmethod
    def setUpClass(cls):
        super(TestJSONAPI, cls).setUpClass()
        api_manager = APIManager(app, db, cfg_class=JSONAPIConfig)
        api_manager.register_api(TestAPI.Product)
        api_manager.register_api(TestAPI.Distributor)
        api_manager.register_api(TestAPI.StockCount)
        api_manager.register_api(TestAPI.StockLevel)

    def test_get_relationship(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1/links/distributor'),
                       headers=self.get_headers())
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(rv.status_code == 200)
            self.assertTrue('distributor' in j)
            self.assertTrue(isinstance(j['distributor'], dict))

    def test_get_all(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'), headers=self.get_headers())
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(rv.status_code == 200)
            self.assertTrue('products' in j)
            self.assertTrue(len(j['products']) == 2)

    def test_get(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1'), headers=self.get_headers())
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(rv.status_code == 200)
            self.assertTrue('product' in j)
            self.assertTrue(isinstance(j['product'], dict))

    def test_get_not_found(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/100'),
                       headers=self.get_headers())
            self.assertTrue(rv.status_code == 404)

    def test_get_multiple(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1,2'),
                       headers=self.get_headers())
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(rv.status_code == 200)
            self.assertTrue('products' in j)
            self.assertTrue(len(j['products']) == 2)

    def test_post(self):
        p_json = {
            "product": {
                "distributor_code": "SYSCO",
                "category": 1,
                "brand": 1,
                "distributor": 1,
                "unit": 1,
                "name": "Green Lettuce",
                "description": "Organic green lettuce from the state of CA",
                "reorder_qty": 24,
                "min_order_qty": 12,
                "max_order_qty": 144,
                "supplier_code": "",
                "reorder_level": 12,
                "lead_time": 5
            }
        }

        with self.client as c:
            rv = c.post(self.get_url('/products'), data=json.dumps(p_json),
                        headers=self.get_headers())
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(rv.status_code == 201)
            self.assertTrue(
                ('Location', self.get_url('/products/3')) == rv.headers[2])
            self.assertTrue(j['product']['description'] ==
                            "Organic green lettuce from the state of CA")
            self.assertTrue(j['product']['min_order_qty'] == 12)

    def test_put(self):
        p_json = {
            "product": {
                "name": "Greenest Lettuce",
                "description": "Organic green lettuce from the state of CA",
                "min_order_qty": 100
            }
        }
        with self.client as c:
            rv = c.put(self.get_url('/products/1'), data=json.dumps(p_json),
                       headers=self.get_headers())
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(j['product']['description'] ==
                            "Organic green lettuce from the state of CA")
            self.assertTrue(j['product']['min_order_qty'] == 100)
            self.assertTrue(rv.status_code == 200)

    def test_delete(self):
        with self.client as c:
            rv = c.delete(self.get_url('/products/1'),
                          headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            rv = c.get(self.get_url('/products/1'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 404)

    def test_filter(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'filter': 'name:Green Lettuce'})
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(rv.status_code == 200)
            self.assertTrue('products' in j)
            self.assertTrue(j['products'][0]['name'] == 'Green Lettuce')
            self.assertTrue(len(j['products']) == 1)

    def test_sort_desc(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'sort': '-name'})
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(rv.status_code == 200)
            self.assertTrue('products' in j)
            self.assertTrue(j['products'][0]['name'] == 'Red Leaf Lettuce')
            self.assertTrue(len(j['products']) == 2)

    def test_sort_asc(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'sort': 'name'})
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(rv.status_code == 200)
            self.assertTrue('products' in j)
            self.assertTrue(j['products'][0]['name'] == 'Green Lettuce')
            self.assertTrue(len(j['products']) == 2)

    def test_include_list_obj(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'include': 'stock_levels'})
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(rv.status_code == 200)
            self.assertTrue('linked' in j)
            self.assertTrue('stock_levels' in j['linked'])
            self.assertTrue(len(j['linked']['stock_levels']) == 2)

    def test_include_obj(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'include': 'distributor'})
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(rv.status_code == 200)
            self.assertTrue('linked' in j)
            self.assertTrue('distributors' in j['linked'])
            self.assertTrue(len(j['linked']['distributors']) == 1)


class TestEmberAPI(TestJSONAPI):
    @classmethod
    def setUpClass(cls):
        super(TestJSONAPI, cls).setUpClass()
        api_manager = APIManager(app, db, cfg_class=EmberConfig)
        api_manager.register_api(TestAPI.Product)
        api_manager.register_api(TestAPI.Distributor)
        api_manager.register_api(TestAPI.StockCount)
        api_manager.register_api(TestAPI.StockLevel)

    def test_get_relationship(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1/distributor'),
                       headers=self.get_headers())
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(rv.status_code == 200)
            self.assertTrue('distributor' in j)
            self.assertTrue(isinstance(j['distributor'], dict))

    def test_include_list_obj(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'include': 'stockLevels'})
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(rv.status_code == 200)
            self.assertTrue('stockLevels' in j)
            self.assertTrue(len(j['stockLevels']) == 2)

    def test_include_obj(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'include': 'distributor'})
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(rv.status_code == 200)
            self.assertTrue('distributors' in j)
            self.assertTrue(len(j['distributors']) == 1)

    def test_post(self):
        p_json = {
            "product": {
                "distributorCode": "SYSCO",
                "category": 1,
                "brand": 1,
                "distributor": 1,
                "unit": 1,
                "name": "Green Lettuce",
                "description": "Organic green lettuce from the state of CA",
                "reorderQty": 24,
                "minOrderQty": 12,
                "maxOrderQty": 144,
                "supplierCode": "",
                "reorderLevel": 12,
                "leadTime": 5
            }
        }

        with self.client as c:
            rv = c.post(self.get_url('/products'), data=json.dumps(p_json),
                        headers=self.get_headers())
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(rv.status_code == 201)
            self.assertTrue(
                ('Location', self.get_url('/products/3')) == rv.headers[2])
            self.assertTrue(j['product']['description'] ==
                            "Organic green lettuce from the state of CA")
            self.assertTrue(j['product']['minOrderQty'] == 12)

    def test_put(self):
        p_json = {
            "product": {
                "name": "Greenest Lettuce",
                "description": "Organic green lettuce from the state of CA",
                "minOrderQty": 100
            }
        }
        with self.client as c:
            rv = c.put(self.get_url('/products/1'), data=json.dumps(p_json),
                       headers=self.get_headers())
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(j['product']['description'] ==
                            "Organic green lettuce from the state of CA")
            self.assertTrue(j['product']['minOrderQty'] == 100)
            self.assertTrue(rv.status_code == 200)


class TestRegisterAPIExcludes(TestAPI):
    @classmethod
    def setUpClass(cls):
        super(TestRegisterAPIExcludes, cls).setUpClass()
        api_manager = APIManager(app, db, cfg_class=JSONAPIConfig,
                                 excludes={'from_model': ['created']})
        api_manager.register_api(TestAPI.Product,
                                 excludes={'from_model': ['reorder_qty']})
        api_manager.register_api(TestAPI.Distributor)

    def test_get_with_excludes(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1'), headers=self.get_headers())
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(rv.status_code == 200)
            self.assertTrue('product' in j)
            self.assertTrue(isinstance(j['product'], dict))
            self.assertTrue('reorder_qty' not in j['product'])
