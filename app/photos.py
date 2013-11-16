
from flask import redirect
from flask import Blueprint, current_app as app

from schema import Driver
from utils import *
from constants import *

photos = Blueprint('photos', __name__, url_prefix='/images')


@photos.route('/<user_id>')
def get_photo(user_id):
    img_path = grab_photo(user_id)
    if img_path:
        return redirect(img_path)
    return redirect(NO_IMAGE)
