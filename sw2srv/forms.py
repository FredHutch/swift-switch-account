from flask.ext.wtf import Form
from wtforms import StringField, BooleanField

class Foo(Form):
    bar = StringField('bar')
    baz = BooleanField('baz')

class AuthHelper(Form):
    #username = StringField('username')
    acct_name = StringField('acct_name')

