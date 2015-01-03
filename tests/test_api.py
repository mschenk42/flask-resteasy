# coding: utf-8
"""
    tests.test_api
    ~~~~~~~~~~~~~~

    :copyright: (c) 2014 by Michael Schenk.
    :license: BSD, see LICENSE for more details.
"""
import unittest
import os
import json

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from flask.ext.resteasy.manager import APIManager
from flask_resteasy.configs import APIConfig, EmberConfig


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

        cls.ctx = app.app_context()
        cls.ctx.push()
        cls.client = app.test_client()

    def setUp(self):
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
        api_manager = APIManager(app, db, cfg_class=APIConfig,
                                 methods=['GET', 'PUT', 'POST', 'DELETE'])
        api_manager.register_api(TestAPI.Product)
        api_manager.register_api(TestAPI.Distributor)
        api_manager.register_api(TestAPI.StockCount)
        api_manager.register_api(TestAPI.StockLevel)

    def test_get_relationship(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1/links/distributor'),
                       headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue('distributor' in j)
            self.assertTrue(isinstance(j['distributor'], dict))

    def test_get_invalid_relationship(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1/links/invalid'),
                       headers=self.get_headers())
            self.assertTrue(rv.status_code == 404)

    def test_get_all(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue('products' in j)
            self.assertTrue(len(j['products']) == 2)

    def test_get(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
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
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
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
            self.assertTrue(rv.status_code == 201)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(
                ('Location', self.get_url('/products/3')) == rv.headers[2])
            self.assertTrue(j['product']['description'] ==
                            "Organic green lettuce from the state of CA")
            self.assertTrue(j['product']['min_order_qty'] == 12)

            rv = c.get(self.get_url('/products/3'), headers=self.get_headers())
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(rv.status_code == 200)
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
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(j['product']['description'] ==
                            "Organic green lettuce from the state of CA")
            self.assertTrue(j['product']['min_order_qty'] == 100)

            rv = c.get(self.get_url('/products/1'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(j['product']['description'] ==
                            "Organic green lettuce from the state of CA")
            self.assertTrue(j['product']['min_order_qty'] == 100)

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
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue('products' in j)
            self.assertTrue(j['products'][0]['name'] == 'Green Lettuce')
            self.assertTrue(len(j['products']) == 1)

    def test_sort_desc(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'sort': '-name'})
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue('products' in j)
            self.assertTrue(j['products'][0]['name'] == 'Red Leaf Lettuce')
            self.assertTrue(len(j['products']) == 2)

    def test_sort_asc(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'sort': 'name'})
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue('products' in j)
            self.assertTrue(j['products'][0]['name'] == 'Green Lettuce')
            self.assertTrue(len(j['products']) == 2)

    def test_include_list_obj(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'include': 'stock_levels'})
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue('linked' in j)
            self.assertTrue('stock_levels' in j['linked'])
            self.assertTrue(len(j['linked']['stock_levels']) == 2)

    def test_include_obj(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'include': 'distributor'})
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue('linked' in j)
            self.assertTrue('distributors' in j['linked'])
            self.assertTrue(len(j['linked']['distributors']) == 1)

    def test_paginated(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'page': 1, 'per_page': 1})
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue('products' in j)
            self.assertTrue(len(j['products']) == 1)
            self.assertTrue('meta' in j)

            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'page': 2, 'per_page': 1})
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue('products' in j)
            self.assertTrue(len(j['products']) == 1)
            self.assertTrue('meta' in j)

            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'page': 3, 'per_page': 1})
            self.assertTrue(rv.status_code == 404)


class TestEmberAPI(TestJSONAPI):
    @classmethod
    def setUpClass(cls):
        super(TestJSONAPI, cls).setUpClass()
        api_manager = APIManager(app, db, cfg_class=EmberConfig,
                                 methods=['GET', 'PUT', 'POST', 'DELETE'])
        api_manager.register_api(TestAPI.Product)
        api_manager.register_api(TestAPI.Distributor)
        api_manager.register_api(TestAPI.StockCount)
        api_manager.register_api(TestAPI.StockLevel)

    def test_get_relationship(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1/distributor'),
                       headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue('distributor' in j)
            self.assertTrue(isinstance(j['distributor'], dict))

    def test_get_invalid_relationship(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1/invalid'),
                       headers=self.get_headers())
            self.assertTrue(rv.status_code == 404)

    def test_include_list_obj(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'include': 'stockLevels'})
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue('stockLevels' in j)
            self.assertTrue(len(j['stockLevels']) == 2)

    def test_include_obj(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'include': 'distributor'})
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
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
            self.assertTrue(rv.status_code == 201)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(
                ('Location', self.get_url('/products/3')) == rv.headers[2])
            self.assertTrue(j['product']['description'] ==
                            "Organic green lettuce from the state of CA")
            self.assertTrue(j['product']['minOrderQty'] == 12)

            rv = c.get(self.get_url('/products/3'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
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
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(j['product']['description'] ==
                            "Organic green lettuce from the state of CA")
            self.assertTrue(j['product']['minOrderQty'] == 100)

            rv = c.get(self.get_url('/products/1'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(j['product']['description'] ==
                            "Organic green lettuce from the state of CA")
            self.assertTrue(j['product']['minOrderQty'] == 100)


class TestRegisterAPIExcludes(TestAPI):
    @classmethod
    def setUpClass(cls):
        super(TestRegisterAPIExcludes, cls).setUpClass()
        api_manager = APIManager(app, db, cfg_class=APIConfig,
                                 excludes={'from_model': ['created']})
        api_manager.register_api(TestAPI.Product,
                                 excludes={'from_model': ['reorder_qty']})
        api_manager.register_api(TestAPI.Distributor)

    def test_get_with_excludes(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue('product' in j)
            self.assertTrue(isinstance(j['product'], dict))
            self.assertTrue('reorder_qty' not in j['product'])


class TestMethodRegistration(TestAPI):
    def test_default_method_registration(self):
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
        api_manager = APIManager(app, db, cfg_class=APIConfig)
        api_manager.register_api(TestAPI.Product)
        api_manager.register_api(TestAPI.Distributor)
        api_manager.register_api(TestAPI.StockCount)
        api_manager.register_api(TestAPI.StockLevel)

        with self.client as c:
            rv = c.get(self.get_url('/products/1'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            rv = c.post(self.get_url('/products'), data=json.dumps(p_json),
                        headers=self.get_headers())
            self.assertTrue(rv.status_code == 405)
            rv = c.put(self.get_url('/products/1'), data=json.dumps(p_json),
                       headers=self.get_headers())
            self.assertTrue(rv.status_code == 405)
            rv = c.delete(self.get_url('/products/1'),
                          headers=self.get_headers())
            self.assertTrue(rv.status_code == 405)


class TestInvalidRequests(TestAPI):
    @classmethod
    def setUpClass(cls):
        super(TestInvalidRequests, cls).setUpClass()
        api_manager = APIManager(app, db, cfg_class=APIConfig,
                                 excludes={'relationship': ['distributor']})

        api_manager.register_api(TestAPI.Product)
        api_manager.register_api(TestAPI.Distributor)

    def test_not_allowed_link(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1/links/distributor'),
                       headers=self.get_headers())
            self.assertTrue(rv.status_code == 403)

    def test_invalid_link(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1/links/invalid'),
                       headers=self.get_headers())
            self.assertTrue(rv.status_code == 404)

    def test_invalid_idents(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1,a'),
                       headers=self.get_headers())
            self.assertTrue(rv.status_code == 404)

    def test_invalid_filter(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'filter': 'names:Green Lettuce'})
            self.assertTrue(rv.status_code == 404)
            # test valid filter attribute without filter condition
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'filter': 'name'})
            self.assertTrue(rv.status_code == 404)

    def test_invalid_sort(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'sort': '-names'})
            self.assertTrue(rv.status_code == 404)

    def test_invalid_include(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'include': 'invalid'})
            self.assertTrue(rv.status_code == 404)

    def test_not_allowed_include(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'),
                       headers=self.get_headers(),
                       query_string={'include': 'distributor'})
            self.assertTrue(rv.status_code == 403)
