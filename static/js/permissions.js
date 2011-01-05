window.addEvent('domready', function() {
    var tip = new Tips($$(".Tips"));

    var current_role = "";
    var current_sizes = "";
    var accordion = new Accordion('h3.atStart', 'div.atStart', {
	opacity: true,
	onActive: function(toggler, element){
	    toggler.setStyle('color', '#ff3300');
	    current_role = element.get("id");
	    current_sizes = element.get("rel");
	},

	onBackground: function(toggler, element) {
	    toggler.setStyle('color', '#222');
	}
    }, $('accordion'));

    $$("a[name=addperm]").addEvent("click", function(evt) {
	evt.stop();
	var sizes = current_sizes.split(" ");
	SqueezeBox.initialize({
	    size: {x: sizes[0], y: sizes[1]},
	    handler: 'iframe'
	});
	var addperm_url = evt.target.get("href") + "?role=" + current_role;
	SqueezeBox.open(addperm_url);
    });

    $$("a[name=delperms]").addEvent("click", function(evt) {
	evt.stop();
	var selection = $(current_role).getElements("input[id=selection]:checked");
	if (selection.length == 0) {
	    return;
	}
	if (!confirm(gettext("Remove this selection?"))) {
	    return;
	}
	var sr_selection = "";
	selection.each(function(item) {
	    if (sr_selection != "") {
		sr_selection += ",";
	    }
	    sr_selection += item.get("value");
	});
	new Request.JSON({
	    url : evt.target.get("href"),
	    onSuccess: function(response) {
		if (response.status == "ok") {
		    $(current_role).set("html", response.content);
		    infobox.info(response.message);
		} else {
		    infobox.error(response.message);
		}
		infobox.hide(2);

	    }
	}).send({
	    method: "get",
	    data: "role=" + current_role + "&selection=" + sr_selection
	});
    });
});