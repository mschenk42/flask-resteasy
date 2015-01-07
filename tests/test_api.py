# coding: utf-8
"""
    tests.test_api
    ~~~~~~~~~~~~~~

    :copyright: (c) 2014 by Michael Schenk.
    :license: BSD, see LICENSE for more details.
"""
import unittest
import json

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from flask_resteasy.manager import APIManager
from flask_resteasy.configs import EmberConfig

app = None
db = SQLAlchemy()


class TestAPI(unittest.TestCase):

    # Models copied and adapted from
    # https://github.com/Vertabelo/vertabelo-sqlalchemy

    class Order (db.Model):
        """Order Model
        """
        __tablename__ = "order"
        id = db.Column('id', db.Integer, primary_key=True)
        order_no = db.Column('order_no', db.String)
        client_id = db.Column('client_id', db.Integer,
                              db.ForeignKey('client.id'))
        client = db.relationship('Client', foreign_keys=client_id)

    class Product (db.Model):
        """Product Model
        """
        __tablename__ = "product"
        id = db.Column('id', db.Integer, primary_key=True)
        product_category_id = db.Column('product_category_id', db.Integer,
                                        db.ForeignKey('product_category.id'))
        sku = db.Column('sku', db.String)
        name = db.Column('name', db.String)
        price = db.Column('price', db.BigInteger)
        description = db.Column('description', db.String)
        image = db.deferred(db.Column('image', db.LargeBinary))
        product_category = db.relationship('ProductCategory',
                                           foreign_keys=product_category_id)

    class OrderItem (db.Model):
        """Order Item Model
        """
        __tablename__ = "order_item"
        id = db.Column('id', db.Integer, primary_key=True)
        order_id = db.Column('order_id', db.Integer, db.ForeignKey('order.id'))
        product_id = db.Column('product_id', db.Integer,
                               db.ForeignKey('product.id'))
        amount = db.Column('amount', db.Integer)
        order = db.relationship('Order', foreign_keys=order_id,
                                backref=db.backref('order_items'))
        product = db.relationship('Product', foreign_keys=product_id)

    class ProductCategory (db.Model):
        """Product Category Model
        """
        __tablename__ = "product_category"
        id = db.Column('id', db.Integer, primary_key=True)
        name = db.Column('name', db.String)
        parent_category_id = db.Column('parent_category_id', db.Integer,
                                       db.ForeignKey('product_category.id'))
        product_category = db.relationship('ProductCategory',
                                           foreign_keys=parent_category_id)

    class Client (db.Model):
        """Client Model
        """
        __tablename__ = "client"
        id = db.Column('id', db.Integer, primary_key=True)
        full_name = db.Column('full_name', db.String)
        email = db.Column('email', db.String)
        private = db.Column('private', db.String)

    @classmethod
    def setUpClass(cls):
        global app, db

        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
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

        # clients
        author = TestAPI.Client(full_name='Arthur Dent', email='arthur@hh.net')
        ford = TestAPI.Client(full_name='Ford Prefect', email='ford@hh.net')
        marvin = TestAPI.Client(full_name='Marvin', email='marvin@hh.net')
        db.session.add_all([author, ford, marvin])

        # categories
        food = TestAPI.ProductCategory(name='Food')
        fish = TestAPI.ProductCategory(name='Fish', product_category=[food])
        produce = TestAPI.ProductCategory(name='Produce',
                                          product_category=[food])
        supplies = TestAPI.ProductCategory(name='Supplies')
        cleaning = TestAPI.ProductCategory(name='Cleaning',
                                           product_category=[supplies])
        db.session.add_all([food, fish, produce, supplies, cleaning])

        # products
        fish = TestAPI.Product(name='Lake Perch',
                               product_category=fish,
                               sku='LPERCH',
                               price=12.00,
                               description='Lake Perch from Lake Superior')
        lettuce = TestAPI.Product(name='Green Lettuce',
                                  product_category=produce,
                                  sku='GLETTUCE',
                                  price=4.95,
                                  description='Locally produced green lettuce')
        db.session.add_all([fish, lettuce])

        # orders
        order_1 = TestAPI.Order(order_no=1, client=author)
        order_item_1 = TestAPI.OrderItem(order=order_1, product=fish, amount=1)
        order_item_2 = TestAPI.OrderItem(order=order_1, product=lettuce,
                                         amount=1)
        db.session.add_all([order_1, order_item_1, order_item_2])

        order_2 = TestAPI.Order(order_no=1, client=marvin)
        order_item_3 = TestAPI.OrderItem(order=order_2, product=lettuce,
                                         amount=2)
        db.session.add_all([order_2, order_item_3])

        db.session.commit()

    def destroy_db(self):
        # db session remove is required here to support in memory database
        # and is a best practice
        # see http://flask-testing.readthedocs.org/en/latest/
        db.session.remove()
        db.drop_all()

    def get_url(self, resource_url):
        return ''.join(['http://localhost', resource_url])

    def get_headers(self):
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}
        return headers


class TestGetRequest(TestAPI):

    @classmethod
    def setUpClass(cls):
        super(TestGetRequest, cls).setUpClass()
        api_manager = APIManager(app, db)
        api_manager.register_api(TestAPI.Client,
                                 excludes={'all': ['private']})
        api_manager.register_api(TestAPI.ProductCategory)
        api_manager.register_api(TestAPI.Product)

    def test_get_all(self):
        with self.client as c:
            rv = c.get(self.get_url('/clients'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(isinstance(j['clients'], list))
            self.assertTrue(len(j['clients']) == 3)

    def test_get_one(self):
        with self.client as c:
            rv = c.get(self.get_url('/clients/1'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(isinstance(j['client'], dict))
            self.assertTrue(len(j) == 1)

    def test_get_two(self):
        with self.client as c:
            rv = c.get(self.get_url('/clients/1,2'),
                       headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue('clients' in j)
            self.assertTrue(len(j['clients']) == 2)

    def test_get_404(self):
        with self.client as c:
            rv = c.get(self.get_url('/clients/10'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 404)

    def test_get_with_links(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(j['product']['links']['product_category'] == 1)

    def test_get_link(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1/links/product_category'),
                       headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(isinstance(j['product_category'], dict))

    def test_get_private(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue('private' not in j['product'])


class TestFilter(TestAPI):

    @classmethod
    def setUpClass(cls):
        super(TestFilter, cls).setUpClass()
        api_manager = APIManager(app, db)
        api_manager.register_api(TestAPI.Client,
                                 excludes={'all': ['private']})
        api_manager.register_api(TestAPI.Product)

    def test_filter(self):
        with self.client as c:
            rv = c.get(self.get_url('/clients'), headers=self.get_headers(),
                       query_string={'filter': 'email:arthur@hh.net'})
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(len(j) == 1)
            self.assertTrue(j['clients'][0]['email'] == 'arthur@hh.net')

    def test_filter_many(self):
        with self.client as c:
            rv = c.get(self.get_url('/products'), headers=self.get_headers(),
                       query_string={'filter': 'name:Lake Perch,sku:LPERCH'})
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(len(j) == 1)
            self.assertTrue(j['products'][0]['sku'] == 'LPERCH')

    def test_filter_unknown(self):
        with self.client as c:
            rv = c.get(self.get_url('/clients'), headers=self.get_headers(),
                       query_string={'filter': 'unknown:something'})
            self.assertTrue(rv.status_code == 400)

    def test_filter_unauthorized(self):
        with self.client as c:
            rv = c.get(self.get_url('/clients'), headers=self.get_headers(),
                       query_string={'filter': 'private:sensitive data'})
            self.assertTrue(rv.status_code == 403)


class TestSort(TestAPI):

    @classmethod
    def setUpClass(cls):
        super(TestSort, cls).setUpClass()
        api_manager = APIManager(app, db)
        api_manager.register_api(TestAPI.Client,
                                 excludes={'all': ['private']})
        api_manager.register_api(TestAPI.Product)

    def test_sort(self):
        with self.client as c:
            rv = c.get(self.get_url('/clients'), headers=self.get_headers(),
                       query_string={'sort': 'full_name'})
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(j['clients'][0]['email'] == 'arthur@hh.net')
            self.assertTrue(j['clients'][2]['email'] == 'marvin@hh.net')

    def test_sort_many(self):
        with self.client as c:
            rv = c.get(self.get_url('/clients'), headers=self.get_headers(),
                       query_string={'sort': 'full_name,email'})
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(j['clients'][0]['email'] == 'arthur@hh.net')
            self.assertTrue(j['clients'][2]['email'] == 'marvin@hh.net')

    def test_sort_desc(self):
        with self.client as c:
            rv = c.get(self.get_url('/clients'), headers=self.get_headers(),
                       query_string={'sort': '-full_name'})
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(j['clients'][0]['email'] == 'marvin@hh.net')
            self.assertTrue(j['clients'][2]['email'] == 'arthur@hh.net')

    def test_sort_unknown(self):
        with self.client as c:
            rv = c.get(self.get_url('/clients'), headers=self.get_headers(),
                       query_string={'sort': 'name'})
            self.assertTrue(rv.status_code == 400)

    def test_sort_unauthorized(self):
        with self.client as c:
            rv = c.get(self.get_url('/clients'), headers=self.get_headers(),
                       query_string={'sort': 'private'})
            self.assertTrue(rv.status_code == 403)


class TestInclude(TestAPI):

    @classmethod
    def setUpClass(cls):
        super(TestInclude, cls).setUpClass()
        api_manager = APIManager(app, db)
        api_manager.register_api(TestAPI.Order)
        api_manager.register_api(TestAPI.OrderItem)
        api_manager.register_api(TestAPI.Client)
        api_manager.register_api(TestAPI.Product,
                                 excludes={'all': ['product_category']})
        api_manager.register_api(TestAPI.ProductCategory)

    def test_include(self):
        with self.client as c:
            rv = c.get(self.get_url('/orders/1'), headers=self.get_headers(),
                       query_string={'include': 'order_items'})
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(len(j['linked']['order_items']) == 2)

    def test_include_many(self):
        with self.client as c:
            rv = c.get(self.get_url('/orders/1'), headers=self.get_headers(),
                       query_string={'include': 'order_items,client'})
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(len(j['linked']['order_items']) == 2)
            self.assertTrue(len(j['linked']['client']) == 1)

    def test_include_unknown(self):
        with self.client as c:
            rv = c.get(self.get_url('/orders/1'), headers=self.get_headers(),
                       query_string={'include': 'products'})
            self.assertTrue(rv.status_code == 400)

    def test_include_unauthorized(self):
        with self.client as c:
            rv = c.get(self.get_url('/products/1'), headers=self.get_headers(),
                       query_string={'include': 'product_category'})
            self.assertTrue(rv.status_code == 403)


class TestPagination(TestAPI):

    @classmethod
    def setUpClass(cls):
        super(TestPagination, cls).setUpClass()
        api_manager = APIManager(app, db)
        api_manager.register_api(TestAPI.Order)

    def test_pagination(self):
        with self.client as c:
            rv = c.get(self.get_url('/orders'), headers=self.get_headers(),
                       query_string={'page': 1, 'per_page': 1})
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(j['meta']['page'] == 1)
            self.assertTrue(j['meta']['no_pages'] == 2)
            self.assertTrue(len(j['orders']) == 1)

            rv = c.get(self.get_url('/orders'), headers=self.get_headers(),
                       query_string={'page': 2, 'per_page': 1})
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(j['meta']['page'] == 2)
            self.assertTrue(j['meta']['no_pages'] == 2)
            self.assertTrue(len(j['orders']) == 1)

            rv = c.get(self.get_url('/orders'), headers=self.get_headers(),
                       query_string={'page': 3, 'per_page': 1})
            self.assertTrue(rv.status_code == 404)


class TestPostRequest(TestAPI):

    @classmethod
    def setUpClass(cls):
        super(TestPostRequest, cls).setUpClass()
        api_manager = APIManager(app, db)
        api_manager.register_api(TestAPI.Product,
                                 methods=['GET', 'POST', 'PUT', 'DELETE'])
        api_manager.register_api(TestAPI.ProductCategory)

    def test_post(self):
        p_json = {
            "product": {
                "sku": "BEET",
                "name": 'Beets',
                "description": "Locally produced beets",
                "price": 1.95,
                "links": {'product_category': 2},
            }
        }

        with self.client as c:
            rv = c.post(self.get_url('/products'), data=json.dumps(p_json),
                        headers=self.get_headers())
            self.assertTrue(rv.status_code == 201)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(j['product']['sku'] == "BEET")
            self.assertTrue(('Location',
                             self.get_url('/products/3')) == rv.headers[2])

        with self.client as c:
            rv = c.get(self.get_url('/products/3'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)


class TestDeleteRequest(TestAPI):

    @classmethod
    def setUpClass(cls):
        super(TestDeleteRequest, cls).setUpClass()
        api_manager = APIManager(app, db)
        api_manager.register_api(TestAPI.Product,
                                 methods=['GET', 'POST', 'PUT', 'DELETE'])

    def test_delete(self):

        with self.client as c:
            rv = c.delete(self.get_url('/products/1'),
                          headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)

        with self.client as c:
            rv = c.get(self.get_url('/products/1'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 404)


class TestPutRequest(TestAPI):

    @classmethod
    def setUpClass(cls):
        super(TestPutRequest, cls).setUpClass()
        api_manager = APIManager(app, db)
        api_manager.register_api(TestAPI.Product,
                                 methods=['GET', 'POST', 'PUT', 'DELETE'])
        api_manager.register_api(TestAPI.ProductCategory)

    def test_post(self):
        p_json = {
            "product": {
                "sku": "RLETTUCE",
                "name": 'Red Lettuce',
                "description": "Red lettuce grown locally",
                }
        }

        with self.client as c:
            rv = c.put(self.get_url('/products/2'), data=json.dumps(p_json),
                       headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(j['product']['sku'] == "RLETTUCE")

        with self.client as c:
            rv = c.get(self.get_url('/products/2'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue(j['product']['sku'] == "RLETTUCE")


class TestAllowedRequestMethods(TestAPI):

    @classmethod
    def setUpClass(cls):
        super(TestAllowedRequestMethods, cls).setUpClass()

    def test_default_allowed(self):
        api_manager = APIManager(app, db)
        api_manager.register_api(TestAPI.Product)

        with self.client as c:
            rv = c.get(self.get_url('/products'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            rv = c.post(self.get_url('/products'))
            self.assertTrue(rv.status_code == 405)
            rv = c.put(self.get_url('/products/1'))
            self.assertTrue(rv.status_code == 405)
            rv = c.delete(self.get_url('/products/1'))
            self.assertTrue(rv.status_code == 405)

    def test_set_allowed(self):
        api_manager = APIManager(app, db)
        api_manager.register_api(TestAPI.Client, methods=['GET', 'DELETE'])

        with self.client as c:
            rv = c.get(self.get_url('/clients'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            rv = c.post(self.get_url('/clients'))
            self.assertTrue(rv.status_code == 405)
            rv = c.put(self.get_url('/clients/1'))
            self.assertTrue(rv.status_code == 405)
            rv = c.delete(self.get_url('/clients/1'))
            self.assertTrue(rv.status_code == 200)


class TestEmberConfig(TestAPI):

    @classmethod
    def setUpClass(cls):
        super(TestEmberConfig, cls).setUpClass()
        api_manager = APIManager(app, db, cfg_class=EmberConfig)
        api_manager.register_api(TestAPI.Order)
        api_manager.register_api(TestAPI.OrderItem)
        api_manager.register_api(TestAPI.Client)

    def test_get_resource_camelcase(self):
        with self.client as c:
            rv = c.get(self.get_url('/orderItems'), headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)

    def test_get_link_camelcase(self):
        with self.client as c:
            rv = c.get(self.get_url('/orders/1/orderItems'),
                       headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)

    def test_get_field_camelcase(self):
        with self.client as c:
            rv = c.get(self.get_url('/clients/1'),
                       headers=self.get_headers())
            self.assertTrue(rv.status_code == 200)
            j = json.loads(rv.data.decode(encoding='UTF-8'))
            self.assertTrue('fullName' in j['client'])
