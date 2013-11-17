'''schema.py

This contains the schemas for `carpools`
'''

from mongoengine import *
from werkzeug.security import generate_password_hash, check_password_hash
import time


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
        return check_password_hash(self.password, hashed)

    def __unicode__(self):
        return "%s" % self.name


class Ride(Document):
    '''Defines a ride; this is figuratively a car that is travelling from
    `departure` to `destination`.
    '''
    driver = ReferenceField(Driver, required=True)
    departure = StringField(required=True)
    destination = StringField(required=True)
    depart_date = DateTimeField(required=True)
    people = IntField(required=True)

    def set_lat_long(self):
        place, (lat, lng) = geo.geocode(self.departure)
        self.depart_loc = (lat, lng)
        place, (lat, lng) = geo.geocode(self.destination)
        self.destination_loc = (lat, lng)

    def __unicode__(self):
        return "%s, %s->%s" % (self.driver, self.departure, self.destination)


