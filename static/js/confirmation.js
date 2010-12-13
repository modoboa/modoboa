var Confirmation = new Class({
    Implements: [Options, Events],
    options: {
	checkboxes: []
    },

    build_checkboxes: function() {
	var result = "";
	var cbhash = new Hash(this.options.checkboxes);

	cbhash.each(function(value, key, hash) {
	    result += "<input type='checkbox' name='" + key + "' value='' />";
	    result += "<label>" + value + "</label>";
	});
	return result;
    },

    initialize: function(url, urlparams, question, options) {
	this.setOptions(options);
	Confirmation.url = url;
	Confirmation.urlparams = urlparams;

	var content = new Element("div", {id: "confirmbox"});
	var icondiv = new Element("div", {
	    id: "dlg-iconbox",
	    html: "<img src='/static/pics/dialog-warning.png' alt='Warning' />"
	}).inject(content);
	
	this.textdiv = new Element("div", {
	    id: "dlg-textbox",
	    html: "<b>" + question + "</b>"
		+ "<p>" + this.build_checkboxes() + "</p>"
	}).inject(content);

	var buttonsdiv = new Element("div", {
	    id: "dlg-buttons"
	}).inject(content);
	new Element("input", {type: "button", name: "ok", id: "ok", value: "Ok"})
	    .addEvent("click", this.ok_handler)
	    .inject(buttonsdiv);
	new Element("input", {type: "button", name: "cancel", value: "Cancel"})
	    .addEvent("click", this.cancel_handler)
	    .inject(buttonsdiv);

	new Element("input", {type: "hidden", name: "result", id: "result", value: "cancel"})
	    .inject(content);

	SqueezeBox.initialize({
	    size: {x: 350, y: 140},
	    handler: "adopt",
	    onClose: this.close_handler
	});
	SqueezeBox.open(content);
    },

    close_handler: function(content) {
	var result = $("confirmbox").getElement("input[name=result]");
	if (result.get("value") != "ok") {
	    return;
	}

	var params = Confirmation.urlparams;
	$$("input[type=checkbox]:checked").each(function(item) {
	    if (params != "") {
		params += "&";
	    }
	    params += item.get("name") + "=true";
	});
	new Request.JSON({
	    method: "get",
	    url: Confirmation.url,
	    onSuccess: function(res) {
		if (res.status == "ok") {
		    window.location.reload();
		} else {
		    infobox.error(res.error);
		    infobox.hide(2);
		}
	    }
        }).send(params);
    },

    ok_handler: function(evt) {
	$("result").value = "ok";
	parent.SqueezeBox.close();
    },

    cancel_handler: function(evt) {
	parent.SqueezeBox.close();
    }
});