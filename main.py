DEBUG = True

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


@app.route('/email', methods=['POST'])
def send_email():
    logger.debug(request.values)

    sender = request.values.get('from')
    recipient = request.values.get('to')
    subject = request.values.get('subject')
    message = request.values.get('message')

    import smtplib
    from app.config import CONFIG
    smtpserver = 'smtp.gmail.com:587'
    header  = "From: %s\n" % sender
    header += "To: %s\n" % recipient
    header += "Cc: \n"
    header += "Subject: %s\n\n" % subject
    message = header + message

    server = smtplib.SMTP(smtpserver)
    server.starttls()
    server.login(CONFIG['email-login'], CONFIG['email-pass'])
    problems = server.sendmail(sender, recipient, message)
    server.quit()
    logger.debug('problems: ' + str(problems))
    return '404'


if __name__ == '__main__':
    import sys
    try:
        port = int(sys.argv[1])
    except:
        port = 5000
    app.run(port = port)
