
from flask import render_template, request, url_for, redirect, flash, session
from flask import Blueprint, current_app as app
from schema import *
from utils import *
from datetime import datetime
import re

search = Blueprint('search', __name__)


@search.route('/search', methods=['GET', 'POST'])
def search_results():
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
        matches = [ride for ride in matches]
        arriving = [ride for ride in arriving]
        departing = [ride for ride in departing]

        all_results = matches + arriving + departing
        for ride in all_results:
            grab_photo(ride.driver)
        app.logger.debug(all_results)

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
        app.logger.info("No matches found")
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
    app.logger.debug(results)
    return results


