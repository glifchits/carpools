from datetime import datetime, timedelta
import random
import urllib
import json
import requests
import os
import sys

from mongoengine import *
from app.schema import *

from app.config import exported as CONFIG

connect(CONFIG.db_db, host = CONFIG.db_uri)


CITIES = set([
    "Waterloo", "Toronto", "Mississauga", "Kingston",
    "Hamilton", "Windsor", "Scarborough", "New York",
    "Winnipeg", "Ottawa", "Montreal", "Kitchener",
    "Burlington", "Sarnia", "Barrie"
])

NAMES = set([
    "George", "Stacey", "Natalia", "Chelsey",
    "Johnny", "Chuck", "Ann", "Matt",
    "Joey", "Tom", "Dallas", "Carlie",
    "Kira", "Brad", "Angela", "Kelsey",
    "Emily", "Bo", "Alex", "Phil",
    "Julia", "Lois", "Terry", "Monica",
    "Peggy", "Ved", "Sohail", "Mike",
    "Shaminda", "Dave", "Mitch", "Gianni"
])

EMAILS = set([
    "gmail.com", "hotmail.com", "yahoo.com", "mail.ru"
])

SKIP_USERS = '--no-users' in sys.argv
SKIP_RIDES = '--no-rides' in sys.argv

if not SKIP_USERS:
    if not os.path.exists('static/temp'):
        os.mkdir('static/temp')

    for i in range(20):
        name = random.choice(list(NAMES))
        email = name.lower() + '%s@' + random.choice(list(EMAILS))
        password = 'password'
        email_salt = ''

        found = False
        while not found:
            fb_id = random.randint(1000, 50000)
            res = urllib.urlopen('http://graph.facebook.com/%s' % fb_id).read()
            res = json.loads(res)
            found = 'error' not in res.keys()

        found = False
        while not found:
            email_salt = random.randint(0, 100)
            found = Driver.objects(email = email % email_salt).count() == 0

        facebook = Facebook(
            user_id = fb_id,
            access_token = "1z2x3c4v5b6n7m",
            expires_at = int(time.time())
        ).save()
        print "created %s" % facebook

        driver = Driver(
            name = name,
            email = email % email_salt,
            password = password,
            facebook = facebook
        )
        img_url = 'http://graph.facebook.com/%s/picture?width=300&height=300'
        image_request = requests.get(img_url % fb_id, stream=True)
        if image_request.status_code == 200:
            image_path = 'static/temp/profile_temp.jpg'
            image = open(image_path, 'wb')
            for chunk in image_request.iter_content():
                image.write(chunk)
            image.close()
            image = open(image_path, 'r')
            driver.photo.put(image, content_type='image/jpeg')
            image.close()
        driver.save()
        print "created %s" % driver

if not SKIP_RIDES:
    print """
    Creating rides
    """

    for i in range(100):
        dep = random.choice(list(CITIES))

        now = datetime.now()
        timeoffset = timedelta(
            days = random.randint(-5, 40),
            hours = random.randint(-4, 10),
            minutes = random.randint(0, 60),
            seconds = random.randint(0, 60)
        )
        depart_time = now + timeoffset

        driver = Driver.objects[random.randint(0, Driver.objects.count()-1)]

        ride = Ride(
            driver = driver,
            depart_date = depart_time,
            people = random.randint(2,6)
        )
        ride.set_places(dep, random.choice(list(CITIES - set(dep))))
        ride.save()
        print "created %s" % ride


