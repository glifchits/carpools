
from flask import current_app as app

def random_hex():
    return '%030x' % random.randrange(16**30)


def grab_photo(user_dict):
    salt = user_dict['id'] #random_hex()
    image_path = 'static/hosted/profile%s.jpg' % salt
    app.logger.debug("user is " + str(user_dict))
    try:
        open(image_path)
        return image_path
    except IOError:
        pass

    user = Driver.objects(id = user_dict['id'])
    if user.count() != 1:
        raise ValueError("somehow there are != 1 users with id %s" % \
                user_dict['id'])
    user = user[0]
    if not user.photo:
        return NO_IMAGE

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


if __name__ == '__main__':
    from schema import *
    connect('carpools')
    driver = Driver.objects.first()
    from pprint import pprint
    pprint(  jsonify(driver) )
