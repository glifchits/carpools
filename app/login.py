
from flask import render_template, request, url_for, redirect, flash, session
from flask import Blueprint, current_app as app
from schema import *
from utils import *
from config import exported as CONFIG
from constants import *

login = Blueprint('login', __name__, url_prefix = '/login')


def login_finally(next_url):
    if 'user' in session:
        next_url = next_url or url_for('home')
        app.logger.debug('redirecting to %s' % next)
        return redirect(next_url)
    return '404'


def get_facebook_auth_url(client_id, redirect_uri):
    s = "https://www.facebook.com/dialog/oauth?client_id={client_id}&redirect_uri={redirect_uri}"
    return s.format(client_id = client_id, redirect_uri = redirect_uri)


@login.route('', methods=['GET', 'POST'])
def login_user():
    # this is the URL for redirect to self if login failure
    # reattaches the redirect URL
    redirect_self = url_for('.login_user', next=request.args.get('next'))

    if request.method == 'POST':
        # gets the redirect URL. simultaneously removes this value from session
        next_url = session.pop('after_login_post', None)

        # this is the login logic
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
        # here we pass in the next_url to allow redirect
        return login_finally(next_url)

    else: # request.method == 'GET'
        app.logger.debug(request.args)
        # put the redirect URL in session. so we can use FB login
        session['after_login_post'] = request.args.get('next')
        client_id = CONFIG.app_id
        redirect_uri = CONFIG.url + url_for('.facebook_login')
        auth_url = get_facebook_auth_url(client_id, redirect_uri)
        return render_template('login.html', facebook_login_link = auth_url)


@login.route('/facebook')
def facebook_login():
    '''Facebook login flow'''
    # this redirect URI is called and the request contains a `code`
    code = request.values['code']
    app.logger.debug('config url is %s' % CONFIG.url)
    redirecturi = CONFIG.url + url_for('.facebook_login')
    app.logger.debug('redirect url %s' % redirecturi)

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

    # get redirect URL from session as we saw in GET /login
    next_url = session.pop('after_login_post', None)
    return login_finally(next_url)


def facebook_auth(code, redirect_uri):
    '''Generalized FB authentication flow. Returns an access token and its
    debug values'''

    def request_return(request):
        j = request.json()
        j[u'status'] = request.status_code
        return j

    app_id = CONFIG.app_id
    app_secret = CONFIG.app_secret

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


