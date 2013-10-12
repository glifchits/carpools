DEBUG = True
from flask import Flask
from flask import render_template, request, url_for, redirect, \
        flash
from flask.ext.assets import Environment, Bundle
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)
assets = Environment(app)
assets.init_app(app)

client = MongoClient()
db = client.carpools
rides = db.rides

if DEBUG:
    app.debug = True
    assets.debug = True
    app.config['ASSETS_DEBUG'] = True

css = Bundle('style.css')
assets.register('css', css)

app.jinja_env.add_extension('jinja2.ext.loopcontrols')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/driver')
def driver():
    return render_template('driver.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        matches, arriving, departing = list_results(request.form)
        return render_template(
                'show_results.html',
                destination=request.form['destination'],
                departure=request.form['depart'],
                matches=matches,
                arriving=arriving,
                departing=departing)
    else:
        return redirect(url_for('home'))

def list_results(form):
    departure = form['depart']
    destination = form['destination']
    matches = rides.find( {
        'departure': '%s' % departure,
        'destination': '%s' % destination
    } )
    departing = rides.find( {
        'departure': '%s' % departure,
        'destination': { '$ne': '%s' % destination }
    } )
    arriving = rides.find( {
        'departure': { '$ne': '%s' % departure },
        'destination': '%s' % destination
    } )
    results = (
        [match for match in matches],
        [departure for departure in departing],
        [arrival for arrival in arriving]
    )
    return results

@app.route('/submit_ride', methods=['POST'])
def add_ride():
    def totimestamp(dt, epoch=datetime(1970,1,1)):
        td = dt - epoch
        return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 1e6

    form = request.form
    name = form['name']
    depart = form['depart']
    destination = form['destination']
    date = form['depart-date']
    time = form['depart-time']
    people = form['people']
    datestr = date + " " + time
    fmt = "%Y-%m-%d %H:%M"
    depart_time = datetime.strptime(datestr, fmt)
    ride = {'driver': name,
            'departure': depart,
            'destination': destination,
            'people': people,
            'depart-time': totimestamp(depart_time)
            }
    try:
        rides.insert(ride)
        return redirect(url_for('driver'))
    except Error as e:
        return e.msg


if __name__ == '__main__':
    app.run()
