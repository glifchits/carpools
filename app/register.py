
from flask import render_template, request, url_for, redirect, flash, session
from flask import Blueprint, current_app as app
import mongoengine.errors

from schema import *
from utils import *
from config import CONFIG
from constants import *
from login import facebook_auth

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
        return render_template('register.html')


@register.route('/facebook')
def facebook_register():
    '''Facebook register: authentication and profile creation'''
    code = request.values['code']

    redirecturi = CONFIG['url'] + url_for('.facebook_register')
    values = facebook_auth(code, redirecturi)

    req = graph('me', values[ 'access_token' ])
    app.logger.debug(req)

    driver = Driver()
    driver.email = req['email']
    driver.name = req['name']
    driver.facebook = values['fb_object_id']

    fb = Facebook.objects(id = values['fb_object_id'])
    if fb.count() != 1:
        pass
    else:
        fb = fb[0]
        user_id = req['id']
        fb.username = req.get('username','')
        fb.link = req.get('link', '')

        img_url = 'http://graph.facebook.com/%s/picture?width=300&height=300'
        image_request = requests.get(img_url % user_id, stream=True)
        if image_request.status_code == 200:
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
    try:
        driver.save()
        fb.save()
    except:
        raise

    try:
        driver.save()
    except Exception as e:
        flash((CSS_ERR, """That Facebook account is already linked to a user on
this site!"""))
        return redirect(url_for('login.login_user'))

    session['user'] = jsonify(driver)
    app.logger.debug(driver)

    flash((CSS_SUCC, "Success!"))
    return redirect(url_for('.register_user'))


