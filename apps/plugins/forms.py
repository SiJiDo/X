# -*- encoding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

# login and registration


class FileWebForm(FlaskForm):
    tmp = StringField('Username',
                         id='username_login',
                         validators=[DataRequired()])
