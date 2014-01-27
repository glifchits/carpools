echo "db.ride.remove(); db.driver.remove(); db.facebook.remove(); db.location.remove();" > cleardb.js
mongo carpools cleardb.js
rm cleardb.js
rm -rf static/hosted static/temp
