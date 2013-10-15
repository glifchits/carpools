'''schema.py

This contains the schemas for `carpools`
'''

from mongoengine import *

class Ride(Document):
    '''Defines a ride; this is figuratively a car that is travelling from
    `departure` to `destination`.
    '''
    driver = StringField(required=True)
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


class Driver(Document):
    '''A registered user who can sign up to be a driver'''
    email = EmailField(required=True, unique=True)
    password = StringField(required=True)
    name = StringField(required=True)

    def __unicode__(self):
        return "%s" % self.name



