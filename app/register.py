
from flask import render_template, request, url_for, redirect, flash, session
from flask import Blueprint, current_app as app
import mongoengine.errors

from schema import *
from utils import *
from config import exported as CONFIG
from constants import *
from login import facebook_auth, get_facebook_auth_url

register = Blueprint('register', __name__, url_prefix = '/register')


@register.route('/', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        try:
            email    = request.form['email']
            name     = request.form['name']
            password = request.form['password']
            confirm  = request.form['confirm-password']
        except KeyError as e:
            flash((CSS_ERR, "Malformed request (%s)" % e.message))
            return redirect(url_for('.register_user'))

        if password != confirm:
            flash((CSS_ERR, "Password did not match confirmation"))
            return redirect(url_for('.register_user'))

        driver = Driver()
        driver.email = email
        driver.name = name
        driver.set_password(password)
        try:
            driver.save()
        except mongoengine.errors.ValidationError as e:
            flash((CSS_ERR, e.message))
            return redirect(url_for('.register_user'))
        except Exception as e:
            app.logger.debug(type(e))
            flash((CSS_ERR, "A user with that email already exists."))
            return redirect(url_for('.register_user'))

        flash((CSS_SUCC, "Register successful!"))
        return redirect(url_for('login.login_user'))
    else: # request.method == 'GET'
        client_id = CONFIG.app_id
        redirect_uri = CONFIG.url + url_for('.facebook_register')
        auth_url = get_facebook_auth_url(client_id, redirect_uri)
        return render_template('register.html', facebook_auth_url = auth_url)


@register.route('/facebook')
def facebook_register():
    '''Facebook register: authentication and profile creation'''
    code = request.values['code']

    redirecturi = CONFIG.url + url_for('.facebook_register')

    # get the facebook login info. profile created and saved to DB
    auth_request = facebook_auth(code, redirecturi)

    # get the facebook user info by making a graph API request
    user_info = graph('me', auth_request[ 'access_token' ])

    # create the persistent Driver object
    driver = Driver()
    driver.email = user_info['email']
    driver.name = user_info['name']

    # recall that 'fb_object_id' key was added in the `facebook_auth` function
    # will get the Facebook object if the profile was successfully created
    fb = Facebook.objects(id = auth_request['fb_object_id']).first()
    if fb:
        # we just update their user info
        fb.username = user_info.get('username','')
        fb.link = user_info.get('link', '')

        img_url = 'http://graph.facebook.com/%s/picture?width=300&height=300'
        image_request = requests.get(img_url % user_info['id'], stream=True)
        if image_request.status_code == 200:
            # here we just save the user's current profile image to the database
            image_path = 'static/temp/profile_temp.jpg'
            image = open(image_path, 'wb')
            for chunk in image_request.iter_content():
                image.write(chunk)
            image.close()
            image = open(image_path, 'r')
            driver.photo.put(image, content_type='image/jpeg')
            image.close()
        else:
            app.logger.error("image request failed %s" % image_request.status_code)
    else:
        app.logger.error("no facebook object found!")
        raise

    driver.facebook = fb

    try:
        driver.save()
        fb.save()
    except mongoengine.errors.NotUniqueError:
        flash((CSS_ERR, "Your email is already registered on this site!"))
        return redirect(url_for('login.login_user'))

    session['user'] = jsonify(driver)
    app.logger.debug(driver)

    flash((CSS_SUCC, "Success!"))
    return redirect(url_for('.register_user'))


