from pymongo import MongoClient
from datetime import datetime, timedelta
import random


client = MongoClient()
db = client.carpools
rides = db.rides

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

for i in range(10):
    dep = random.choice(list(CITIES))

    now = datetime.now()
    timeoffset = timedelta(
        days = random.randint(-5, 40),
        hours = random.randint(-4, 10),
        minutes = random.randint(0, 60),
        seconds = random.randint(0, 60)
    )
    depart_time = now + timeoffset

    ride = {
        'driver'      : random.choice(list(NAMES)),
        'departure'   : dep,
        'destination' : random.choice(list(CITIES - set(dep))),
        'people'      : random.randint(2,6),
        'depart-time' : depart_time
    }
    rides.insert(ride)


