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


@app.route('/fb_register')
def fb_register():
    '''Facebook register: authentication and profile creation'''
    code = request.values['code']

    redirecturi = CONFIG['url'] + url_for('fb_register')
    values = facebook_auth(code, redirecturi)

    req = graph('me', values[ 'access_token' ])
    logger.debug(req)

    driver = Driver(
        email = req['email'],
        name = req['name'],
        facebook = values['fb_object_id']
    )

    fb = Facebook.objects(id = values['fb_object_id'])
    if fb.count() != 1:
        pass
    else:
        fb = fb[0]
        user_id = req['id']
        fb.username = req.get('username','')
        fb.link = req.get('link', '')

        img_url = 'http://graph.facebook.com/%s/picture?width=300&height=300'
        image_request = requests.get(img_url % user_id, stream=True)
        if image_request.status_code == 200:
            image_path = 'static/temp/profile_temp.jpg'
            image = open(image_path, 'wb')
            for chunk in image_request.iter_content():
                image.write(chunk)
            image.close()
            image = open(image_path, 'r')
            driver.photo.put(image, content_type='image/jpeg')
            image.close()
        else:
            logger.error("image request failed %s" % image_request.status_code)
    try:
        driver.save()
        fb.save()
    except:
        raise

    try:
        driver.save()
    except Exception as e:
        flash((CSS_ERR, """That Facebook account is already linked to a user on
this site!"""))
        return redirect(url_for('login'))

    session['user'] = jsonify(driver)
    logger.debug(driver)

    flash((CSS_SUCC, "Success!"))
    return redirect(url_for('register'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            email    = request.form['email']
            name     = request.form['name']
            password = request.form['password']
            confirm  = request.form['confirm-password']
        except KeyError as e:
            flash((CSS_ERR, "Malformed request (%s)" % e.message))
            return redirect(url_for('register'))

        if password != confirm:
            flash((CSS_ERR, "Password did not match confirmation"))
            return redirect(url_for('register'))

        driver = Driver(
            email    = email,
            name     = name,
            password = password
        )
        try:
            driver.save()
        except Exception as e:
            logger.debug(type(e))
            flash((CSS_ERR, "A user with that email already exists."))
            return redirect(url_for('register'))

        flash((CSS_SUCC, "Register successful!"))
        return redirect(url_for('login'))
    else: # request.method == 'GET'
        return render_template('register.html')


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
