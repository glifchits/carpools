DEBUG = True

from flask import Flask
from flask import render_template, request, url_for, redirect, \
        flash
from flask.ext.assets import Environment, Bundle
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import os
import re


''' Flask app setup '''
app = Flask(__name__)
app.secret_key = os.urandom(24)
assets = Environment(app)
assets.init_app(app)

''' MongoDB setup '''
client = MongoClient()
db = client.carpools
rides = db.rides

if DEBUG:
    app.debug = True
    assets.debug = True

''' Asset bundles '''
css = Bundle('style.css', 'show_rides.css')
assets.register('css', css)

''' Other extensions '''
# jinja template loop controls. allows {% continue %}
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

''' Random stuff '''
logger = app.logger



''' App controllers '''

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/driver')
def driver():
    return render_template('driver.html')


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
            flash("Malformed request: %s" % e.msg)
            return redirect(url_for('home'))

        matches, arriving, departing = search_rides(dep, dest)
        return render_template(
            'show_results.html',
            destination = dest,
            departure   = dep,
            matches     = matches,
            arriving    = arriving,
            departing   = departing
        )
    return redirect(url_for('home'))


def search_rides(departure, destination):
    ''' This function does the DB search '''
    dep = re.compile("^%s$" % departure, re.IGNORECASE)
    des = re.compile("^%s$" % destination, re.IGNORECASE)
    matches = rides.find({
        'departure'   : dep,
        'destination' : des
    })
    if matches.count() == 0:
        logger.info("No matches found")
        arriving = rides.find({
            'destination' : des
        })
        departing = rides.find({
            'departure' : dep
        })
    else:
        arriving, departing = [], []
    results = (
        [match for match in matches],
        [arrival for arrival in arriving],
        [departure for departure in departing]
    )
    logger.debug(results)
    return results


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
    ride = {
        'driver'      : name,
        'departure'   : departure,
        'destination' : destination,
        'people'      : people,
        'depart-time' : depart_time
    }
    try:
        rides.insert(ride)
        return redirect(url_for('driver'))
    except Exception as e:
        flash("Could not add your ride: %s (%s)" % (str(e), e.message))
        return redirect(url_for('home'))


@app.route('/rides/<ride_id>')
def get_ride(ride_id):
    ride = rides.find_one({ '_id': ObjectId(str(ride_id)) })
    return render_template('show_ride.html', ride=ride)


if __name__ == '__main__':
    app.run()
