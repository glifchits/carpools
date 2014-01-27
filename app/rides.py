
from flask import render_template, request, url_for, redirect, flash, session
from flask import Blueprint, current_app as app
from schema import *
from utils import *
from constants import *
from components import login_required

from datetime import datetime

rides = Blueprint('rides', __name__, url_prefix='/rides')


@rides.route('/<ride_id>')
@login_required
def view(ride_id):
    try:
        ride = Ride.objects(id=ride_id)
        assert ride
    except AssertionError:
        app.logger.debug('caught bad ride id')
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


@rides.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'GET':
        return render_template('driver.html')

    form = request.form
    app.logger.debug(form)

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
        return redirect(url_for('rides.create'))

    try:
        datestr = date + " " + time
        fmt = "%Y-%m-%d %H:%M"
        depart_date = datetime.strptime(datestr, fmt)
    except ValueError as e:
        flash((CSS_ERR, 'The entered date was invalid (%s)' % e.message))
        return redirect(url_for('rides.create'))

    ride = Ride()
    ride.driver = session['user']['id']
    ride.people = people
    ride.depart_date = depart_date
    ride.set_places(departure, destination)

    try:
        ride.save()
        flash((CSS_SUCC, "Your ride was added successfully!"))
        return redirect(url_for('home'))
    except Exception as e:
        flash((CSS_ERR, "Could not add your ride: %s" % str(e)))
        return redirect(url_for('home'))


