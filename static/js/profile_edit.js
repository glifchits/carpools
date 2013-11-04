var getFields = function() {
    var json = {};
    $('#profile input').each(function() {
        var id = this.id;
        json[id] = this.value;
    });
    return json;
};

var changeToInputs = function() {
    $('span[id^=profile]').each(function() {
        var newHTML = "<input type=text ";
        console.debug(this);
        var attrs = {
            "class" : $(this).attr('class'),
            "id" : $(this).attr('id'),
            "value" : $(this).html()
        };
        for (attr in attrs)
            newHTML += attr + '="' + attrs[attr] + '" ';
        newHTML += '>';
        console.debug('html changed to', newHTML);
        this.outerHTML = newHTML;
    });
};

var changeToSpans = function() {
    $('input[id^=profile]').each(function() {
        console.debug(this);
        var newHTML = "<span ";
        var value = $(this).attr('value');
        var attrs = {
            "class" : $(this).attr('class'),
            "id" : $(this).attr('id')
        };
        for (attr in attrs) 
            newHTML += attr + '="' + attrs[attr] + '" ';
        newHTML + '>' + value + '</span>';
        console.debug(newHTML);
        this.outerHTML = newHTML;
    });
};


$('#edit-button').click(function() {
    var profile = $('#profile');

    if (!(profile.hasClass('edit-mode'))) {
        // edits allowed
        console.log('edit clicked');
        profile.addClass('edit-mode');
        $('#edit-button').text('Save').addClass('save-button');
        changeToInputs();
    } else {
        // save changes
        console.debug('save clicked');
    
        /* save profile logic */
        var fieldsOnSave = getFields();
        $.post('/profile/save_changes', fieldsOnSave);

        /* restore page to non-edit mode */
        profile.removeClass('edit-mode');
        $('#edit-button').text('Edit').removeClass('save-button');
        changeToSpans();
    }
});

