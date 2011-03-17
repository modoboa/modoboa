var error_callbacks = {
    mbaliasform: function() {
	if ($("id_domain").value == 0) {
	    $("id_mboxes").set("html", "");
	}
	mbaliasform_init();
    },
    permform: function() {
	if ($defined($("id_domain"))) {
	    $("id_domain").options[0].setProperty("selected", "selected");
	    domadminform_init();
	}
    }
};

var extra_data_callbacks = {

};

function register_callback(hash, name, callback) {
    if ($defined(hash[name])) {
        return false;
    }
    hash[name] = callback;
    return true;
}

function register_error_callback(name, callback) {
    return register_callback(error_callbacks, name, callback);
}

function register_extra_data_callback(name, callback) {
    return register_callback(extra_data_callbacks, name, callback);
}

function ajax_submit(event) {
    var form = event.target;
    var myid = form.get("id");
    var data = form.toQueryString();
    
    event.stop();
    if ($defined(extra_data_callbacks[myid])) {
        if (data != "") {
            data += "&";
        }
        data += extra_data_callbacks[myid]();
    }

    new Request({
        method: form.get("method"),
        data: data,
        onSuccess: function(responseText) {
	    var response = JSON.decode(responseText);
            
            if (response.status == "ko") {
                $(document.body).set("html", response.content);
		$(document.body).addEvent("submit", ajax_submit);
		if ($defined(error_callbacks[myid])) {
		    error_callbacks[myid]();
		}
            } else {
                if ($defined(response.url) && response.url != "") {
                    parent.location.href = response.url;			
		}
                if ($defined(response.ajaxnav)) {
                    parent.current_anchor.update(1);
                }
                parent.SqueezeBox.close();
            }
        },
	onFailure: function(xhr) {
	    parent.document.getElement('iframe').setStyles({width: 800, height: 600});
	    $(document.body).set("html", xhr.responseText);
	}
    }).send();
}

window.addEvent("domready", function() {
    $(document.body).addEvent("submit", ajax_submit);

    $$("input[type!=submit]", "select").addEvents({
	focus: function(evt) {
	    var helpdiv = $(evt.target.name + "_helptext");
	    if (helpdiv) {
		var coords = evt.target.getCoordinates();
		helpdiv.setPosition({x: 10, y: coords['top'] + coords['height'] + 5});
		helpdiv.setStyle("display", "block");
	    }
	},
	blur: function(evt) {
	    var helpdiv = $(evt.target.name + "_helptext");
	    if (helpdiv) {
		helpdiv.setStyle("display", "none");
	    }
	}
    });
});
