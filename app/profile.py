
from flask import render_template, request, url_for, redirect, flash, session
from flask import Blueprint, current_app as app
from schema import *
from utils import *
from constants import *

import json

profile = Blueprint('profile', __name__, url_prefix='/profile')


@profile.route('/')
def edit():
    ''' Allow someone to view and edit their own profile. '''
    if 'user' in session:
        return render_template('profile.html', user=session['user'])
    else:
        flash((CSS_ERR, "You have to be logged in to view your profile!"))
        return redirect(url_for('login.login_user'))


@profile.route('/fields')
def available_fields():
    ''' Returns a JSON list of fields that are not filled out. '''
    if 'user' in session:
        driver = Driver.objects(id = session['user']['id']).first()
        fields = [name for name, value in driver._fields.iteritems()]
        fields = filter(lambda f: not driver.__getattribute__(f), fields)
        return json.dumps(fields)
    else:
        return '404'


@profile.route('/save_changes', methods=['POST'])
def save():
    ''' Accepts a save profile POST request. '''
    form = request.form
    app.logger.debug(form)
    attribs = {
        'name': 'profile-name',
        'facebook': 'profile-facebook',
        'phone': 'profile-phone',
        'email': 'profile-email'
    }
    if 'user' in session:
        user = session['user']
        app.logger.debug('modifying' + str(user))

    for attr in attribs.keys():
        user[attr] = form[attribs[attr]]

    return '200'


@profile.route('/<user_id>')
def view(user_id):
    ''' Renders an individual user profile. '''
    match = Driver.objects(id = user_id)
    try:
        assert match
    except AssertionError:
        flash((CSS_ERR, "Invalid profile ID"))
        return redirect(url_for('home'))
    app.logger.debug(match)
    if match.count() != 1:
        flash((CSS_ERR, "No user with that profile ID was found."))
        return redirect(url_for('home'))
    return render_template('profile.html', user=match[0])



