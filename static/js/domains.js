window.addEvent('domready', function() {
    var handlers = new Array();

    if ($defined($("domcontent"))) {
        SqueezeBox.assign($("domcontent").getElements('a[class=boxed]'), {
            parse: 'rel'
        });
    }
    if ($defined($("subcontent"))) {
        SqueezeBox.assign($("subcontent").getElements('a[class=boxed]'), {
            parse: 'rel'
        });
    }

    if ($$("a[name=deleteDom]"))
      $$("a[name=deleteDom]").addEvent('click', function(event) {
	  if (!confirm(gettext("Delete this domain?")))
	    event.stop();
	});

    if ($$("a[name=deleteAlias]"))
        $$("a[name=deleteAlias]").addEvent('click', function(event) {
            if (!confirm(gettext("Delete this alias?")))
                event.stop();
        });

    $(document.body).addEvent('click', function(event) {
	var target = event.target;
	if (target.get('tag') == 'a') {
	    var name = target.get('name');
	    if (name == 'undefined')
		return;
	    if (typeof(handlers[name]) != 'undefined') {
		if (!handlers[name](target, target.get('href'))) {
		    new Event(event).stop();
                }
	    }
	}
    });

    $(document.body).addEvent('submit', function(event) {
	target = event.target;
	if (target.get('tag') == 'form') {
	    name = target.get('name');
	    if (name == 'undefined')
		return;
	    if (typeof(handlers[name]) != 'undefined') {
		new Event(event).stop();
		handlers[name](target);
	    }
	}
    });
    setDivHeight("content", 20, 0);
		    
    objtable = new HtmlTable($("objects_table"), {
	selectable: true
    });
});

loadPage = function(url, destination, callback) {
    destination = (destination == null) ? "page" : destination;

    if (callback)
	new Request({url: url, method: "get", onSuccess: callback}).send();
    else
	new Request({url: url, method: "get", onSuccess: function(data) {
	    $(destination).set('html', data);
	}}).send();
};
