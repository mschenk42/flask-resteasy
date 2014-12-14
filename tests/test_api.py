import unittest
import os
import json

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from flask_resteasy.views import APIView, APIConfig, APIManager


db = SQLAlchemy()
basedir = os.path.abspath(os.path.dirname(__file__))

USE_TOKEN_AUTH = False
TESTING = True
SECRET_KEY = 'secret'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + \
                          os.path.join(basedir, 'data-test.sqlite')

app = Flask(__name__)
app.config.from_object(__name__)


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

    distributor_id = db.Column(db.Integer,
                               db.ForeignKey('distributors.id'),
                               nullable=False)
    distributor = db.relationship('Distributor',

                                  backref=db.backref(__tablename__))


class ProductAPI(APIView):
    @classmethod
    def create_cfg(cls, app, db):
        return APIConfig(Product, app, db)


class DistributorAPI(APIView):
    @classmethod
    def create_cfg(cls, app, db):
        return APIConfig(Distributor, app, db)


APIManager.load(app, db, [ProductAPI, DistributorAPI])


class TestAPI(unittest.TestCase):
    def create_db(self):
        db.init_app(app)
        db.drop_all()
        db.create_all()
        self.load_data()

    def load_data(self):
        distributor1 = Distributor()
        distributor1.name = 'Sysco Inc'
        distributor1.description = "Distributor with a variety of brands"

        distributor2 = Distributor()
        distributor2.name = 'Whole Foods'
        distributor2.description = "Provide fresh and organic produce"

        product1 = Product()
        product1.name = 'Green Lettuce'
        product1.description = 'Organic green lettuce from the state of CA'
        product1.distributor_code = 'SYSCO'
        product1.lead_time = 5
        product1.min_order_qty = 12
        product1.max_order_qty = 144
        product1.reorder_level = 12
        product1.reorder_qty = 24
        product1.distributor = distributor1

        product2 = Product()
        product2.name = 'Red Leaf Lettuce'
        product2.description = 'Organic red leaf lettuce from the state of CA'
        product2.distributor_code = 'SYSCO'
        product2.lead_time = 5
        product2.min_order_qty = 12
        product2.max_order_qty = 144
        product2.reorder_level = 12
        product2.reorder_qty = 24
        product2.distributor = distributor1

        db.session.add(product1, product2)
        db.session.commit()

    def destroy_db(self):
        db.drop_all()

    def setUp(self):
        self.ctx = app.app_context()
        self.ctx.push()
        self.client = app.test_client()
        self.create_db()

    def tearDown(self):
        self.destroy_db()

    def get_url(self, resource_url):
        return ''.join(['http://localhost', resource_url])

    def get_headers(self):
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}
        return headers

    def test_get_all_products(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'), headers=self.get_headers())
            j = json.loads(rv.data)
            self.assertTrue(rv.status_code == 200)
            self.assertTrue('products' in j)
            self.assertTrue(len(j['products']) == 2)

    def test_get_product(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1'), headers=self.get_headers())
            j = json.loads(rv.data)
            self.assertTrue(rv.status_code == 200)
            self.assertTrue('product' in j)
            self.assertTrue(isinstance(j['product'], dict))

    def test_get_product_not_found(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/100'),
                       headers=self.get_headers())
            self.assertTrue(rv.status_code == 404)

    def test_get_multiple_product(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1,2'),
                       headers=self.get_headers())
            j = json.loads(rv.data)
            self.assertTrue(rv.status_code == 200)
            self.assertTrue('products' in j)
            self.assertTrue(len(j['products']) == 2)

    def test_post_product(self):
        p_json = {
            "product": {
                "distributor_code": "SYSCO",
                "category": 1,
                "brand": 1,
                "stocklevels": [1],
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
            j = json.loads(rv.data)
            self.assertTrue(rv.status_code == 201)
            self.assertTrue(
                ('Location', self.get_url('/products/3')) == rv.headers[2])
            self.assertTrue(
                j['product']['description'] ==
                "Organic green lettuce from the state of CA")

    def test_put_product(self):
        p_json = {
            "product": {
                "name": "Greenest Lettuce",
                "description": "Organic green lettuce from the state of CA",
            }
        }
        with self.client as c:
            rv = c.put(self.get_url('/products/1'), data=json.dumps(p_json),
                       headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)

    def test_delete_product(self):
        with self.client as c:
            rv = c.delete(self.get_url('/products/1'),
                          headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            rv = c.get(self.get_url('/products/1'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 404)
