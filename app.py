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
from geopy.geocoders import GoogleV3

from schema import *

CSS_ERR = 'error'
CSS_SUCC = 'success'


''' Flask app setup '''
app = Flask(__name__)
app.secret_key = os.urandom(24)
assets = Environment(app)
assets.init_app(app)

if DEBUG:
    app.debug = True
    assets.debug = True


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
geo = GoogleV3()      # see geopy


def format_datetime(value, format='%I:%M %p on %a, %b %d'):
    return value.strftime(format)

app.jinja_env.filters['datetime'] = format_datetime

''' App controllers '''

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/driver')
def driver():
    if 'user' not in session:
        flash((CSS_ERR, "You must be logged in to create a ride!"))
        return redirect(url_for('login'))
    return render_template('driver.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email    = request.form['email']
            password = request.form['password']
        except KeyError as e:
            flash((CSS_ERR, "Malformed request (%s)" % e.message))
            return to_login

        match = Driver.objects(email = email)
        if match.count() != 1:
            logger.debug("0 or >= 2 matches found")
            flash((CSS_ERR, "Your email address or password was incorrect."))
            return render_template('login.html')
        if match[0].password == password:
            session['user'] = match[0]
            logger.info('user logged in: %s' % session['user'])
            return redirect(url_for('driver'))
        else:
            logger.debug("Incorrect password")
            flash((CSS_ERR, "Incorrect password"))
            return render_template('login.html')

    else: # request.method == 'GET'
        return render_template('login.html')


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


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        try: # no parameters
            if not request.form['departure'] and not request.form['destination']:
                flash((CSS_ERR, "No search parameters provided"))
                return redirect(url_for('home'))
            # parameters
            dep  = request.form['departure']
            dest = request.form['destination']
        except KeyError as e:
            flash((CSS_ERR, "Malformed request: %s" % e.message))
            return redirect(url_for('home'))

        matches, arriving, departing = search_rides(dep, dest)
        return render_template(
            'show_results.html',
            destination = dest,
            departure   = dep,
            matches     = matches,
            arriving    = arriving,
            departing   = departing,
            absolutely_nothing = (not matches and not arriving and not departing)
        )
    return redirect(url_for('home'))


def search_rides(departure, destination):
    ''' This function does the DB search '''
    dep = re.compile("^%s$" % departure, re.IGNORECASE)
    des = re.compile("^%s$" % destination, re.IGNORECASE)
    srt = "+depart_date"
    matches = Ride.objects(
        destination = des,
        departure = dep,
        depart_date__gte = datetime.now()
    ).order_by(srt)
    if matches.count() == 0:
        logger.info("No matches found")
        arriving = Ride.objects(
            destination = des,
            depart_date__gte = datetime.now()
        ).order_by(srt)
        departing = Ride.objects(
            departure = dep,
            depart_date__gte = datetime.now()
        ).order_by(srt)
    else:
        arriving, departing = [], []
    results = (
        matches,
        arriving,
        departing
    )
    logger.debug(results)
    return results


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
        driver      = driver,
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


@app.route('/profile')
def edit_profile():
    ''' Allow someone to view and edit their own profile. '''
    return "profile page"


@app.route('/profile/<user_id>')
def view_profile(user_id):
    ''' Renders an individual user profile. '''
    return "profile page for user %s" % user_id


if __name__ == '__main__':
    app.run()
