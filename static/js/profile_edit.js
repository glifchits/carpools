var getFields = function() {
    var json = {};
    $('#profile input').each(function() {
        var id = this.id;
        json[id] = this.value;
    });
    return json;
};

var changeToInputs = function() {
    console.debug("changing spans to inputs");
    $('span[id^=profile]').each(function() {
        var newHTML = "<input type=text ";
        console.debug(this);
        var attrs = {
            "class" : this.className,
            "id" : $(this).attr('id'),
            "value" : $(this).html()
        };
        for (attr in attrs)
            newHTML += attr + '="' + attrs[attr] + '" ';
        newHTML += '>';
        console.debug('span changing to input', newHTML);
        this.outerHTML = newHTML;
    });
};

var changeToSpans = function() {
    console.debug("changing inputs to spans");
    $('input[id^=profile]').each(function() {
        console.debug(this);
        var newHTML = "<span ";
        var value = this.value;
        var attrs = {
            "class" : this.className,
            "id" : $(this).attr('id')
        };
        for (attr in attrs) 
            newHTML += attr + '="' + attrs[attr] + '" ';
        newHTML += '>' + value + '</span>';
        console.debug('input changing to span', newHTML);
        this.outerHTML = newHTML;
    });
};

var createLinks = function() {
    console.debug("creating links for linkable info");
    $('span[id^=profile]').each(function() {
        var type = this.id.substring(8, 20);
        var elem = '<a href="';
        console.debug('link type is', type);
        if (type === 'email')
            elem += 'mailto:';
        else if (type === 'phone')
            elem += 'tel:';
        else if (type == 'facebook')
            elem += 'http://';
        else
            return;

        elem += this.textContent;
        elem += '">' + this.textContent + '</a>';
        console.debug(this.innerHTML);
        console.debug(elem);
        this.innerHTML = elem;
    })
};

var removeLinks = function() {
    $('span[id^=profile]').each(function() {
        if (this.childNodes.length != 1)
            return;
        var child = this.childNodes[0];
        if (child.tagName !== 'A')
            return;
        this.textContent = child.textContent;
    })
};



$('#edit-button').click(function() {
    var profile = $('#profile');

    if (!(profile.hasClass('edit-mode'))) {
        // edits allowed
        console.log('edit clicked');
        removeLinks();
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
        createLinks();
    }
});

$(function() {
    createLinks();
});
