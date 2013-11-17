var sendEmail = function() {
    console.log('sending email');
    var params = {
        'subject'   : 'subject',
        'message'   : 'message'
    };
    var path = window.location.pathname.split('/');
    var ride_id = path[path.length - 1];
    console.log(params);
    $.ajax({
        type: 'POST', 
        url: '/email/' + ride_id, 
        data: params, 
        success: function(data) {
            console.log('email sent');
        },
        error: function(data) {
            console.log("failed to send");
        }
    });
};

// show send button only when the textarea is non empty
var hideSend = function(hide) {
    if (hide) {
        $('#send-message').addClass('disabled');
    } else {
        $('#send-message').removeClass('disabled');
    };
};

$(function() {
    // textarea autoresize
    $('#message').autosize();

    $('#send-message').addClass('disabled');
    $('#send-message').click(function() {
        event.preventDefault();
        if ($(this).hasClass('disabled')) {
            console.log('disabled');
        } else {
            sendEmail();
        };
    });
    $('#message').keyup(function() {
        hideSend($(this).val() === '');
    })
});
