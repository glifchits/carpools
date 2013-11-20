
from flask import render_template, request, url_for, redirect, flash, session
from flask import Blueprint, current_app as app
from schema import *
from utils import *
from config import CONFIG
from constants import *

login = Blueprint('login', __name__, url_prefix = '/login')


def login_finally(request):
    app.logger.debug('reached login_finally')
    if 'user' in session:
        app.logger.debug('user in session hooray')
        app.logger.debug(request.args)
        next = request.args.get('next')
        if not next:
            next = url_for('home')
        app.logger.debug('redirecting to %s' % next)
        return redirect(next)
    return '404'


@login.route('', methods=['GET', 'POST'])
def login_user():
    redirect_self = url_for('.login_user', next=request.args.get('next'))
    if request.method == 'POST':
        app.logger.debug('login POST. request args is: %s' % request.args)
        try:
            email    = request.form['email']
            password = request.form['password']
        except KeyError as e:
            flash((CSS_ERR, "Malformed request (%s)" % e.message))
            return redirect(redirect_self)

        match = Driver.objects(email = email)
        if match.count() != 1 or not match.first().check_password(password):
            app.logger.debug("0 or >= 2 matches found or bad password")
            flash((CSS_ERR, "Your email address or password was incorrect."))
            return redirect(redirect_self)

        session['user'] = jsonify(match.first())
        app.logger.info('user logged in: %s' % session['user'])
        return login_finally(request)

    else: # request.method == 'GET'
        app.logger.debug(request.args)
        return render_template('login.html')


@login.route('/facebook')
def facebook_login():
    '''Facebook login flow'''
    # this redirect URI is called and the request contains a `code`
    code = request.values['code']
    redirecturi = CONFIG['url'] + url_for('.facebook_login')

    # `values` are what we need
    values = facebook_auth(code, redirecturi)
    app.logger.debug("values is: " + str(values))
    if values['status'] != 200:
        err = values['error']
        flash((CSS_ERR, err['type'] + ": " + err['message']))
        return redirect(url_for('.login_user'))


    app.logger.debug('got user ID %s' % values['user_id'])

    drivers = Driver.objects(facebook = values['fb_object_id'])
    app.logger.debug("drivers are: " + str( drivers ))
    if drivers.count() == 0:
        flash((CSS_ERR, "Your Facebook account has not registered"))
        return redirect(url_for('home'))
    elif drivers.count() != 1:
        return "400 failed"

    session['user'] = jsonify(drivers[0])
    return login_finally(request)


def facebook_auth(code, redirect_uri):
    '''Generalized FB authentication flow. Returns an access token and its
    debug values'''

    def request_return(request):
        j = request.json()
        j[u'status'] = request.status_code
        return j

    app_id = CONFIG['app-id']
    app_secret = CONFIG['app-secret']

    # `code` is used to retrieve an access token
    url = "https://graph.facebook.com/oauth/access_token?"
    url += "client_id=%s&redirect_uri=%s&client_secret=%s&code=%s"
    request_url = url % (app_id, redirect_uri, app_secret, code)
    r = requests.get(request_url)

    if r.status_code != requests.codes.ok:
        return request_return(r)

    # this is just parsing the request parameters for its fields
    request_values = {}
    for elem in r.text.split("&"):
        key, value = elem.split("=")
        request_values[key] = value
    access_token = request_values['access_token']

    # STEP 3: call the access token debug endpoint to get the user ID
    url = "https://graph.facebook.com/debug_token?input_token=%s&access_token=%s"
    request_url = url % (access_token, access_token)
    r = requests.get(request_url)

    if r.status_code != requests.codes.ok:
        return request_return(r)

    values = request_return(r)['data']
    values[u'status'] = r.status_code
    values['access_token'] = access_token

    app.logger.debug(values)

    # and so on: create an authentication record for the right user ID
    fb = Facebook.objects(user_id = values['user_id'])
    if fb.count() == 0:
        fb = Facebook()
        fb.user_id = values['user_id']
    else:
        fb = fb[0]
    fb.access_token = values['access_token']
    fb.expires_at = values['expires_at']
    fb.username = values.get('username', '')
    try:
        fb.save()
    except:
        raise

    values['fb_object_id'] = fb.id
    return values


