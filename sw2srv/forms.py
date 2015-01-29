from flask.ext.wtf import Form
from wtforms import StringField, BooleanField

class AuthHelper(Form):
    acct_name = StringField('acct_name')

