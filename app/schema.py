'''schema.py

This contains the schemas for `carpools`
'''

from mongoengine import *
from werkzeug.security import generate_password_hash, check_password_hash
import time

try:
    from flask import current_app as app
    logger = app.logger
except RuntimeError:
    import logging
    logger = logging.getLogger(__name__)


class Facebook(Document):
    '''Facebook connect credentials'''
    user_id = IntField(required=True, unique=True)
    access_token = StringField(required=True)
    expires_at = IntField(required=True)
    username = StringField()
    link = StringField()

    def is_expired(self):
        return int(time.time()) >= self.expires_at

    def __unicode__(self):
        return "Facebook user %s" % self.user_id


class Location(Document):

    name = StringField(required=True)
    location = GeoPointField(required=True)
    types = ListField()
    g_id = StringField()
    vicinity = StringField()

    def __unicode__(self):
        return "%s @ (%s, %s)" % (self.name, self.location[0], self.location[1])


class Driver(Document):
    '''A registered user who can sign up to be a driver'''
    email = EmailField(required=True, unique=True)
    name = StringField(required=True)
    password = StringField()
    phone = StringField()
    facebook = ReferenceField(Facebook) #unique=True, required=False)
    photo = FileField()

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, hashed):
        if self.password:
            return check_password_hash(self.password, hashed)
        return False

    def __unicode__(self):
        return "%s" % self.name


class Ride(Document):
    '''Defines a ride; this is figuratively a car that is travelling from
    `departure` to `destination`.
    '''
    driver = ReferenceField(Driver, required=True)
    departure = ReferenceField(Location)
    destination = ReferenceField(Location)
    depart_date = DateTimeField(required=True)
    people = IntField(required=True)

    def set_places(self, depart_name, destination_name):
        print 'dept: %s, dest: %s' % (depart_name, destination_name)
        geo = geocode.GoogleV3()

        place, (lat, lng) = geo.geocode(depart_name)
        matching_departure = Location.objects(location=(lat, lng))
        if matching_departure.count() > 0:
            self.departure = matching_departure.first()
        else:
            self.departure = Location()
            self.departure.name = depart_name
            self.departure.location = (lat, lng)
            self.departure.save()
        logger.debug("set dept: %s" % self.departure)

        place, (lat, lng) = geo.geocode(destination_name)
        matching_destination = Location.objects(location=(lat, lng))
        if matching_destination.count() > 0:
            self.destination = matching_destination.first()
        else:
            self.destination = Location()
            self.destination.name = destination_name
            self.destination.location = (lat, lng)
            self.destination.save()
        logger.debug("set dest: %s" % self.destination)

    def __unicode__(self):
        return "%s, %s->%s" % (self.driver, self.departure, self.destination)



