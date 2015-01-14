from tempfile import gettempdir
from os import remove, path

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask_resteasy.manager import APIManager

tmp_db_file = path.join(gettempdir(), 'simple.sqlite')

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + tmp_db_file
db = SQLAlchemy(app)
api_manager = APIManager(app, db)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    def __init__(self, username, email):
        self.username = username
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.username

api_manager.register_api(User)

try:
    db.drop_all()
    db.create_all()
    db.session.add(User(username='marvin', email='marvin@hhguide.net'))
    db.session.add(User(username='arthur', email='arthur@hhguide.net'))
    db.session.commit()

    print ('To access information about the API '
           'go to http://127.0.0.1:5000/api_info')
    print ('Temporary database created %s' % tmp_db_file)

    app.run(use_reloader=False)
finally:
    remove(tmp_db_file)
    print ('Temporary database removed %s' % tmp_db_file)
