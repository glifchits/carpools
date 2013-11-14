echo "db.ride.remove(); db.driver.remove(); db.facebook.remove();" > cleardb.js
mongo carpools cleardb.js
rm cleardb.js
