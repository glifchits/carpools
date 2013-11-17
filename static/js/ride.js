$(function() {

    // textarea autoresize
    $('#message').autosize();

    // show send button only when the textare is non empty
    var hideSend = function() {
        if ($('#message').val() === '') {
            $('#send-message').addClass('disabled');
        } else {
            $('#send-message').removeClass('disabled');
        };
    };
    $('#send-message').addClass('disabled');
    $('#message').keyup(function() {
        hideSend();
    })
});
