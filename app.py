DEBUG = False

''' Flask+extension imports '''
from flask import Flask
from flask import render_template, request, url_for, redirect, flash, session
from flask.ext.mongoengine import MongoEngine
from flask.ext.assets import Environment, Bundle

''' other libraries '''
import os
from geopy.geocoders import GoogleV3

from app.constants import *

''' Flask app setup '''
app = Flask(__name__)
app.secret_key = os.urandom(24)

''' blueprints '''
from app.search import search
app.register_blueprint(search)
from app.profile import profile
app.register_blueprint(profile)
from app.login import login
app.register_blueprint(login)
from app.register import register
app.register_blueprint(register)
from app.photos import photos
app.register_blueprint(photos)
from app.rides import rides
app.register_blueprint(rides)

assets = Environment(app)
assets.init_app(app)

if DEBUG:
    app.debug = True
    assets.debug = True

if not os.path.exists('static/hosted'):
    os.mkdir('static/hosted')
if not os.path.exists('static/temp'):
    os.mkdir('static/temp')


''' MongoDB setup '''
from mongoengine import *
app.config['MONGODB_SETTINGS'] = {
    'DB': 'carpools',
    'USERNAME': 'heroku',
    'PASSWORD': 'cf68822c49b79afb7d70fa17002264fd',
    'HOST': 'paulo.mongohq.com',
    'PORT': 10068
}
db = MongoEngine(app)

''' Asset bundles '''
css = Bundle('css/style.css', 'css/home.css', 'css/show_results.css', \
    'css/show_ride.css', 'css/normalize.css')
assets.register('css', css)

''' Other extensions '''
# jinja template loop controls. allows {% continue %}
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

''' Random stuff '''
logger = app.logger
#geo = GoogleV3()      # see geopy


def format_datetime(value, format='%I:%M %p on %a, %b %d'):
    return value.strftime(format)

app.jinja_env.filters['datetime'] = format_datetime

''' App controllers '''

@app.route('/')
def home():
    session.debug = DEBUG
    return render_template('home.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/submit_location', methods=['POST'])
def get_browser_location():
    logger.debug("submit_location POST received")
    lat = request.values.get('lat')
    lng = request.values.get('lng')
    session.location = (lat, lng)
    return "success"


if __name__ == '__main__':
    app.run()
