
from flask import current_app as app
from schema import *
from constants import *

import requests
import urllib


def random_hex():
    return '%030x' % random.randrange(16**30)


def grab_photo(user_id):
    user = Driver.objects(id = user_id)
    if user.count() != 1:
        raise ValueError("somehow there are != 1 users with id %s" % \
                user_dict['id'])
    user = user.first()
    if not user.photo:
        return None

    image_path = 'static/hosted/profile%s.jpg' % user_id
    try:
        open(image_path)
        return image_path
    except IOError:
        pass

    image = open(image_path, 'wb')
    image.write(user.photo.read())
    image.close()
    return image_path


def jsonify(obj):
    d = {}
    for field in obj:
        field_data = obj[field]
        datatype = str(type(field_data))
        if 'unicode' in datatype or 'int' in datatype:
            d[str(field)] = field_data
        elif 'ObjectId' in datatype:
            d['id'] = str(field_data)
        elif 'schema' in datatype:
            d[str(field)] = jsonify(field_data)
        elif 'None' in datatype:
            d[str(field)] = ''
        else:
            pass
    return d


def graph(endpoint, access_token):
    '''Makes a Facebook Graph API request, returns its JSON'''
    url_base = 'https://graph.facebook.com/'
    req = requests.get(
        url_base + endpoint + '?' +
        urllib.urlencode(dict(access_token = access_token))
    )
    return req.json()


if __name__ == '__main__':
    pass
