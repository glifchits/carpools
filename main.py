DEBUG = True

''' Flask+extension imports '''
from flask import Flask
from flask import render_template, request, url_for, redirect, flash, session
from flask.ext.mongoengine import MongoEngine
from flask.ext.assets import Environment, Bundle
from flask.ext.mail import Mail, Message

''' other libraries '''
import os
import json

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
'''
from app.email import email
app.register_blueprint(email)
'''

from app.config import CONFIG
''' Mail setup '''
from app.schema import Ride, Location
from app import geocode
app.config.update({
    'MAIL_SERVER': 'smtp.gmail.com',
    'MAIL_PORT': 465,
    'MAIL_USE_SSL': True,
    'MAIL_USERNAME': CONFIG['email-login'],
    'MAIL_PASSWORD': CONFIG['email-pass'],
    'DEFAULT_MAIL_SENDER': CONFIG['email-login']
})
mail = Mail(app)

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
    lat = request.values.get('lat')
    lng = request.values.get('lon')
    session['location'] = (lat, lng)
    app.logger.debug("client's location is (%s, %s)" % (lat, lng))
    geocode.save_locations(lat, lng)
    return "success"


@app.route('/email/<ride_id>', methods=['POST'])
def send_email(ride_id):
    message = request.values.get('message')

    sender = session['user']['email']
    subject = "You got a message from %s on Sharecar!"
    subject = subject % session['user']['name']
    ride = Ride.objects(id = ride_id).first()
    recipient = ride.driver.email

    app.logger.debug("sender: " + str(sender))
    app.logger.debug("recipient: " + str(recipient))

    msg = Message(subject, recipients = [recipient], body = message,
            sender = sender)

    mail.send(msg)
    return 'success'


import math
def distance(p1, p2):
    x1, y1 = map(float, p1)
    x2, y2 = map(float, p2)
    return math.sqrt( (x2 - x1) ** 2 + (y2 - y1) ** 2 )


@app.route('/locations')
def get_locations():
    if 'location' not in session:
        # test location.
        lat = 43.48
        lon = -80.5
    else:
        lat, lon = session['location']

    def datum(location):
        return {
            'value': location.name,
            'name': location.name,
            'tokens' : location.name.split(' '),
            'distance': distance((lat, lon), location.location)
        }

    query = request.args.get('q')

    locations = Location.objects(
        location__near = (lat, lon),
        name__istartswith = query
    )
    app.logger.debug(locations)

    results = [datum(loc) for loc in locations]
    return json.dumps(results, indent=4)


if __name__ == '__main__':
    import sys
    try:
        port = int(sys.argv[1])
    except:
        port = 5000
    app.run(port = port)
