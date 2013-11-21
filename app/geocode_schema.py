
from mongoengine import *


class Location(Document):

    name = StringField(required=True)
    location = GeoPointField(required=True)
    types = ListField(required=True)
    timestamp_retrieved = DateTimeField(required=True)


