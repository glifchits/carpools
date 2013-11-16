DEBUG = True

''' Flask+extension imports '''
from flask import Flask
from flask import render_template, request, url_for, redirect, flash, session
from flask.ext.mongoengine import MongoEngine
from flask.ext.assets import Environment, Bundle

''' other libraries '''
from datetime import datetime, timedelta
import os
import re
import random
import json
from geopy.geocoders import GoogleV3
import requests
import urllib

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
app.config['MONGODB_SETTINGS'] = {'DB': 'carpools'}
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


@app.route('/driver')
def driver():
    if 'user' not in session:
        flash((CSS_ERR, "You must be logged in to create a ride!"))
        return redirect(url_for('login'))
    return render_template('driver.html')

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


@app.route('/submit_ride', methods=['POST'])
def add_ride():
    form = request.form
    logger.debug(form)
    try:
        driver = session['user']
    except:
        flash((CSS_ERR, "Not logged in"))
        return redirect(url_for('login'))

    try:
        departure   = form['departure']
        destination = form['destination']
        date        = form['depart-date']
        time        = form['depart-time']
        people      = form['people']
    except KeyError as e:
        flash((CSS_ERR, 'Malformed request: %s (%s)' % (str(e), e.message)))
        return redirect(url_for('home'))

    if '' in [departure, destination, date, time, people]:
        flash((CSS_ERR, 'You should fill out every value in the form!'))
        return redirect(url_for('driver'))

    try:
        datestr = date + " " + time
        fmt = "%Y-%m-%d %H:%M"
        depart_date = datetime.strptime(datestr, fmt)
    except ValueError as e:
        flash((CSS_ERR, 'The entered date was invalid (%s)' % e.message))
        return redirect(url_for('add_ride'))

    ride = Ride(
        driver      = driver['id'],
        departure   = departure,
        destination = destination,
        people      = people,
        depart_date = depart_date
    )

    try:
        ride.save()
        flash((CSS_SUCC, "Your ride was added successfully!"))
        return redirect(url_for('home'))
    except Exception as e:
        flash((CSS_ERR, "Could not add your ride: %s" % str(e)))
        return redirect(url_for('home'))


@app.route('/rides/<ride_id>')
def get_ride(ride_id):
    try:
        ride = Ride.objects(id=ride_id)
        assert ride
    except AssertionError:
        logger.debug('caught bad ride id')
        flash((CSS_ERR, "Invalid ride ID"))
        return redirect(url_for('home'))
    if len(ride) > 1:
        flash((CSS_ERR, "Non-unique ride ID"))
        return redirect(url_for('home'))
    elif len(ride) == 0:
        flash((CSS_ERR, "No ride with that ID!"))
        return redirect(url_for('home'))
    else:
        return render_template('show_ride.html', ride=ride[0])


if __name__ == '__main__':
    app.run()
