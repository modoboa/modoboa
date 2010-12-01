window.addEvent("domready", function() {
    sqbsubmit = function(obj, dest, id, callback, onerror) {
        obj.set('send', {
            onSuccess: function(responseText) {
                var decode = JSON.decode(responseText);
                if (decode.status == "ko") {
                    $(dest).set("html", decode.content);
                    $(id).addEvent("submit", callback);
                    if ($defined(onerror)) {
                        onerror();
                    }
                } else {
                    if (decode.url != "")
                        parent.location.href = decode.url;
                    parent.SqueezeBox.close();
                }
            },
	    onFailure: function(xhr) {
		parent.document.getElement('iframe').setStyles({width: 800, height: 600});
		$(dest).set("html", xhr.responseText);
	    }
        });
        obj.send();
    };

    generic_submit = function(obj, event, id, callback, onerror) {
        event.stop();
        sqbsubmit(obj, "content", id, callback, onerror);
    };
    domain_submit = function(event) {
        generic_submit(this, event, "domform", domain_submit);
    };
    domalias_submit = function(event) {
	generic_submit(this, event, "domaliasform", domalias_submit);
    };
    mailbox_submit = function(event) {
        generic_submit(this, event, "mboxform", mailbox_submit);
    };
    alias_submit = function(event) {
        generic_submit(this, event, "aliasform", alias_submit);
    };
    permission_submit = function(event) {
        generic_submit(this, event, "permform", permission_submit, function() {
	    if ($defined($("id_domain"))) {
		$("id_domain").options[0].setProperty("selected", "selected");
		domadminform_init();
	    }
	});
    };
    chpassword_submit = function(event) {
        generic_submit(this, event, "chpwdform", chpassword_submit);
    };

    arm_onerror = function() {
        new Calendar({id_untildate: "Y-m-d"}, {
            tweak: {x: -100, y:-100}
        });
    };
    arm_submit = function(event) {
        generic_submit(this, event, "armform", arm_submit, arm_onerror);
    };

    if ($("domform"))
        $("domform").addEvent("submit", domain_submit);

    if ($("domaliasform"))
	$("domaliasform").addEvent("submit", domalias_submit);

    if ($("mboxform"))
        $("mboxform").addEvent("submit", mailbox_submit);

    if ($("aliasform"))
        $("aliasform").addEvent("submit", alias_submit);

    if ($("permform"))
        $("permform").addEvent("submit", permission_submit);

    if ($("chpwdform"))
        $("chpwdform").addEvent("submit", chpassword_submit);

    if ($("armform"))
        $("armform").addEvent("submit", arm_submit);

    $$("input[type!=submit]", "select").each(function(elt) {
        if ($(elt.name + "_helptext")) {
            elt.store("tip:title", gettext("Help"));
            elt.store("tip:text", $(elt.name + "_helptext").get("html"));
        }
    });
    var tip = new Tips($$("input[type!=submit]", "select"));
});
