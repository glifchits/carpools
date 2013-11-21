
from config import CONFIG
from geopy.geocoders import GoogleV3
import requests
import urllib
import json


class Geocoder(object):

    def __init__(self):
        self.google = GoogleV3()

    def geocode(self, string):
        ''' Given some address, return its (latitude, longitude) '''
        address, lat, lon = self.google.geocode(string)
        return (lat, lon)

    def nearby_search(self, lat, lon, radius=10000, rankby='distance',
                      sensor='true', types='establishment', **kwargs):
        ''' Return the results of a place search nearby `lat` and `lon` '''
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
        params = {
            'key' : CONFIG.api_key,
            'location' : '%s,%s' % (lat, lon),
            'radius' : radius,
            'rankby' : rankby,
            'sensor' : sensor,
            'types'  : types
        }.update(dict(**kwargs))
        url = url + urllib.urlencode(params)
        return requests.get(url).json()

    def text_search(self, query, sensor='true', **kwargs):
        ''' Perform a text search with `query` '''
        url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?'
        params = {
            'key': CONFIG.api_key,
            'query': query,
            'sensor' : sensor
        }.update(dict(**kwargs))
        url = url + urllib.urlencode(params)
        return requests.get(url).json()

    def radar_search(self, lat, lon, sensor='true', radius=10000,
                     types='establishment', **kwargs):
        ''' Perform a radar search with `keyword`, `name`, or `types` '''
        url = 'https://maps.googleapis.com/maps/api/place/radarsearch/output?'
        params = {
            'key' : CONFIG.api_key,
            'location': '%s,%s' % (lat, lon),
            'radius' : radius,
            'sensor' : sensor,
            'types'  : types
        }
        params.update(dict(**kwargs))
        print params
        url = url + urllib.urlencode(params)
        return requests.get(url).json()


