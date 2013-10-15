from datetime import datetime, timedelta
import random

from mongoengine import *
from schema import *

connect('carpools')


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

for i in range(40):
    name = random.choice(list(NAMES))
    email = name.lower() + '%s@' + random.choice(list(EMAILS))
    password = 'password'
    email_salt = ''

    added = False
    while not added:
        try:
            driver = Driver(
                name = name,
                email = email % email_salt,
                password = password
            ).save()
            added = True
        except NotUniqueError:
            email_salt = str(random.randint(0,99))


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
        departure = dep,
        destination = random.choice(list(CITIES - set(dep))),
        depart_date = depart_time,
        people = random.randint(2,6)
    )
    ride.save()


