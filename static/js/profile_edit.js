$('#edit-button').click(function() {
    var profile = $('#profile');

    if (!(profile.hasClass('edit-mode'))) {
        // edits allowed
        console.log('edit clicked');
        profile.addClass('edit-mode');
        $('#edit-button').text('Save').addClass('save-button');
        $('#profile input').each(function() {
            $(this).removeAttr('disabled');
        });

    } else {
        // save changes
        console.debug('save clicked');
        profile.removeClass('edit-mode');
        $('#edit-button').text('Edit').removeClass('save-button');
        $('#profile input').each(function() {
            $(this).prop('disabled', true);
        });
    }
});

