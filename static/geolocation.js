$(document).ready(function(){
    console.log("ready");
    var setLatLon = function(position) {
        console.log("position is", position);
        var pos = {
            lat: position.coords.latitude,
            lon: position.coords.longitude
        };
        $.post('/submit_location', pos);
    }

    var getPosition = function() {
        navigator.geolocation.getCurrentPosition(setLatLon);
    }
    getPosition();
});
