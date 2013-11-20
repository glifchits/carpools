
from functools import wraps
from flask import session, request, url_for, redirect, flash
from constants import *


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user') is None:
            flash((CSS_ERR, "You must login before you can do that!"))
            return redirect(url_for('login.login_user', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

