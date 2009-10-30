window.addEvent("domready", function() {
    sqbsubmit = function(obj, dest, id, callback) {
        obj.set('send', {
            onSuccess: function(responseText) {
                var decode = JSON.decode(responseText);
                if (decode.status == "ko") {
                    $(dest).set("html", decode.content);
                    $(id).addEvent("submit", callback);
                } else {
                    if (decode.url != "")
                        parent.location.href = decode.url;
                    parent.SqueezeBox.close();
                }
            }
        });
        obj.send();
    }

    generic_submit = function(obj, event, id, callback) {
        event.stop();
        sqbsubmit(obj, "content", id, callback);
    }
    domain_submit = function(event) { 
        generic_submit(this, event, "domform", domain_submit); 
    }
    mailbox_submit = function(event) { 
        generic_submit(this, event, "mboxform", mailbox_submit); 
    }
    alias_submit = function(event) { 
        generic_submit(this, event, "aliasform", alias_submit); 
    }
    permission_submit = function(event) {
        generic_submit(this, event, "permform", permission_submit);
    }
    chpassword_submit = function(event) {
        generic_submit(this, event, "chpwdform", chpassword_submit);
    }

    if ($("domform"))
        $("domform").addEvent("submit", domain_submit);

    if ($("mboxform"))
        $("mboxform").addEvent("submit", mailbox_submit);

    if ($("aliasform"))
        $("aliasform").addEvent("submit", alias_submit);

    if ($("permform"))
        $("permform").addEvent("submit", permission_submit);

    if ($("chpwdform"))
        $("chpwdform").addEvent("submit", chpassword_submit);

    $$("input[type!=submit]", "select").each(function(elt) {
        elt.store("tip:title", gettext("Help"));
        if ($(elt.name + "_helptext")) {
            elt.store("tip:text", $(elt.name + "_helptext").get("html"));
        }
    });
    var tip = new Tips($$("input[type!=submit]", "select"));
});
