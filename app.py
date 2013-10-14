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


''' Document schema definition '''
class Ride(Document):
    '''Defines a ride; this is figuratively a car that is travelling from
    `departure` to `destination`.
    '''
    driver = StringField(required=True)
    departure = StringField(required=True)
    destination = StringField(required=True)
    depart_date = DateTimeField(required=True)
    people = IntField(required=True)

    def set_lat_long(self):
        place, (lat, lng) = geo.geocode(self.departure)
        self.depart_loc = (lat, lng)
        place, (lat, lng) = geo.geocode(self.destination)
        self.destination_loc = (lat, lng)

    def __unicode__(self):
        return "%s, %s->%s" % (self.driver, self.departure, self.destination)


class Driver(Document):
    '''A registered user who can sign up to be a driver'''
    email = EmailField(required=True, unique=True)
    password = StringField(required=True)
    name = StringField(required=True)

    def __unicode__(self):
        return "%s" % self.name


''' App controllers '''

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/driver')
def driver():
    if 'user' not in session:
        flash("You must be logged in to create a ride!")
        return redirect(url_for('login'))
    return render_template('driver.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email    = request.form['email']
            password = request.form['password']
        except KeyError as e:
            flash("Malformed request (%s)" % e.message)
            return to_login

        match = Driver.objects(email = email)
        if match.count() != 1:
            logger.debug("0 or >= 2 matches found")
            flash("Your email address or password was incorrect.")
            return render_template('login.html')
        if match[0].password == password:
            session['user'] = email
            logger.info('user logged in: %s' % session['user'])
            return redirect(url_for('driver'))
        else:
            logger.debug("Incorrect password")
            flash("Incorrect password")
            return render_template('login.html')

    else: # request.method == 'GET'
        return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            email    = request.form['email']
            name     = request.form['name']
            password = request.form['password']
            confirm  = request.form['confirm-password']
        except KeyError as e:
            flash("Malformed request (%s)" % e.message)
            return redirect(url_for('register'))

        if password != confirm:
            flash("Password did not match confirmation")
            return redirect(url_for('register'))

        driver = Driver(
            email    = email,
            name     = name,
            password = password
        )
        driver.save()
        flash("Register successful!")
        return redirect(url_for('login'))
    else: # request.method == 'GET'
        return render_template('register.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        try: # no parameters
            if not request.form['departure'] and not request.form['destination']:
                flash("No search parameters provided")
                return redirect(url_for('home'))
            # parameters
            dep  = request.form['departure']
            dest = request.form['destination']
        except KeyError as e:
            flash("Malformed request: %s" % e.message)
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
        name        = form['name']
        departure   = form['departure']
        destination = form['destination']
        date        = form['depart-date']
        time        = form['depart-time']
        people      = form['people']
    except KeyError as e:
        flash('Malformed request: %s (%s)' % (str(e), e.message))
        return redirect(url_for('home'))

    datestr = date + " " + time
    fmt = "%Y-%m-%d %H:%M"
    depart_time = datetime.strptime(datestr, fmt)

    ride = Ride(
        driver      = name,
        departure   = departure,
        destination = destination,
        people      = people,
        depart_time = depart_time
    )
    try:
        ride.save()
        return redirect(url_for('driver'))
    except Exception as e:
        flash("Could not add your ride: %s (%s)" % (str(e), e.message))
        return redirect(url_for('home'))


@app.route('/rides/<ride_id>')
def get_ride(ride_id):
    ride = Ride.objects(id=ride_id)
    if len(ride) > 1:
        flash("Non-unique ride ID")
        return redirect(url_for('home'))
    else:
        return render_template('show_ride.html', ride=ride[0])


if __name__ == '__main__':
    app.run()
