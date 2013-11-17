DEBUG = True

print "Hello Heroku logs"

''' Flask+extension imports '''
from flask import Flask
from flask import render_template, request, url_for, redirect, flash, session
from flask.ext.mongoengine import MongoEngine

print "Done flask imports"

''' other libraries '''
import os
from geopy.geocoders import GoogleV3

from app.constants import *

print "Starting Flask setup"

''' Flask app setup '''
app = Flask(__name__)
app.secret_key = os.urandom(24)

print "adding blueprints"

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

if DEBUG:
    app.debug = True

print "mkdirs"

if not os.path.exists('static/hosted'):
    os.mkdir('static/hosted')
if not os.path.exists('static/temp'):
    os.mkdir('static/temp')

print "start mongodb setup"

''' MongoDB setup '''
from mongoengine import *
app.config['MONGODB_SETTINGS'] = {
    'DB': 'app19550831',
    'USERNAME': 'heroku',
    'PASSWORD': 'cf68822c49b79afb7d70fa17002264fd',
    'HOST': 'paulo.mongohq.com',
    'PORT': 10068
}
db = MongoEngine(app)

print "and the rest"

''' Other extensions '''
# jinja template loop controls. allows {% continue %}
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

''' Random stuff '''
logger = app.logger
#geo = GoogleV3()      # see geopy


def format_datetime(value, format='%I:%M %p on %a, %b %d'):
    return value.strftime(format)

app.jinja_env.filters['datetime'] = format_datetime

print 'done with preamble'

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
    port = int(os.environ.get('PORT', 5000))
    print "running app"
    app.run(port = port, use_reloader = False)
