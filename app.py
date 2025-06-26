from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import os


app = Flask(__name__)


##---------configurations---------##
load_dotenv()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')

##----------------------------------##

import models

import routes




