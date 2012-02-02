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
        if (this.callbacks[category] == undefined) {
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
                        var target = (this.options.resptarget)
                            ? $(this.options.resptarget) : $(document.body);

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
