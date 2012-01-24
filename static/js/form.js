var Form = new Class({
    Implements: [Options],

    options: {
        resptarget: null
    },

    callbacks: {
        error: {},
        success: {},
        extra_data: {}
    },

    initialize: function(options) {
        this.setOptions(options);

        $(document.body)
            .removeEvents("submit")
            .addEvent("submit", this.submit.bind(this));

        this.init_help_messages();
    },

    init_help_messages: function() {
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
    },

    register_callback: function(category, name, callback) {
        if (this.callbacks[category][name] == undefined) {
            return false;
        }
        this.callbacks[category][name] = callback;
        return true;
    },

    register_error_callback: function(name, callback) {
        return this.register_callback("error", name, callback);
    },

    register_success_callback: function(name, callback) {
        return this.register_callback("success", name, callback);
    },

    register_extra_data_callback: function(name, callback) {
        return this.register_callback("extra_data", name, callback);
    },

    submit: function(event) {
        var form = event.target;
        var myid = form.get("id");
        var data = form.toQueryString();

        event.stop();
        if (this.callbacks["extra_data"][myid] != undefined) {
            if (data != "") {
                data += "&";
            }
            data += this.callbacks["extra_data"][myid]();
        }

        new Request.JSON({
            url: form.get("action"),
            method: form.get("method"),
            data: data,
            onSuccess: function(response) {
                if (response.status == "ko") {
                    if (response.norefresh != undefined && response.norefresh == true) {
                        $$("div[class=error]").set("html", response.respmsg);
                    } else {
                        var target = (this.options.target)
                            ? $(this.options.target) : $(document.body);

                        target.set("html", response.content);
                        this.init_help_messages();
	                /*$(document.body).addEvent("submit", ajax_submit);*/
	                if (this.callbacks["error"][myid] != undefined) {
                            this.callbacks["error"][myid]();
	                }
                    }
                    return;
                }
                if ($defined(response.respmsg)) {
                    if ($defined(parent.current_anchor)) {
                        parent.current_anchor.loading_message = response.respmsg;
                        parent.current_anchor.loading_color = "green";
                    } else {
                        parent.infobox.info(response.respmsg);
                        parent.infobox.hide(1);
                    }
                }
                if ($defined(response.ajaxnav)) {
                    if ($defined(response.url)) {
                        parent.current_anchor.baseurl(response.url, 1);
                    }
                    parent.current_anchor.update(1);
                } else if ($defined(response.url)) {
                    parent.location.href = response.url;
                }
                if (this.callbacks["success"][myid] != undefined) {
                    this.callbacks["success"][myid](response);
	        }
                parent.SqueezeBox.close();
            }.bind(this),
            onFailure: function(xhr) {
                parent.document.getElement('iframe')
                    .setStyles({width: 800, height: 600});
                $(document.body).set("html", xhr.responseText);
            }
        }).send();
    }
});


var error_callbacks = {
    permform: function() {
	if ($defined($("id_domain"))) {
	    $("id_domain").options[0].setProperty("selected", "selected");
	    domadminform_init();
	}
    }
};

var success_callbacks = {

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

function register_success_callback(name, callback) {
    return register_callback(success_callbacks, name, callback);
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

    new Request.JSON({
        url: form.get("action"),
        method: form.get("method"),
        data: data,
        onSuccess: function(response) {
            if (response.status == "ko") {
                if (response.norefresh != undefined && response.norefresh == true) {
                    $$("div[class=error]").set("html", response.respmsg);
                } else {
                    var target = (resptarget != undefined)
                        ? $(resptarget) : $(document.body);

                    target.set("html", response.content);
	            /*$(document.body).addEvent("submit", ajax_submit);*/
	            if ($defined(error_callbacks[myid])) {
	                error_callbacks[myid]();
	            }
                }
                return;
            }
            if ($defined(response.respmsg)) {
                if ($defined(parent.current_anchor)) {
                    parent.current_anchor.loading_message = response.respmsg;
                    parent.current_anchor.loading_color = "green";
                } else {
                    parent.infobox.info(response.respmsg);
                    parent.infobox.hide(1);
                }
            }
            if ($defined(response.ajaxnav)) {
                if ($defined(response.url)) {
                    parent.current_anchor.baseurl(response.url, 1);
                }
                parent.current_anchor.update(1);
            } else if ($defined(response.url)) {
                parent.location.href = response.url;
            }
            if ($defined(success_callbacks[myid])) {
	        success_callbacks[myid](response);
	    }
            parent.SqueezeBox.close();
        },
        onFailure: function(xhr) {
            parent.document.getElement('iframe').setStyles({width: 800, height: 600});
            $(document.body).set("html", xhr.responseText);
        }
    }).send();
}

function initform() {
    $(document.body)
        .removeEvents("submit")
        .addEvent("submit", ajax_submit);

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
}

/*window.addEvent("domready", function() {
    initform();
});*/
