window.addEvent('domready', function() {
    SqueezeBox.assign($$('a.boxed'), {
        parse: 'rel',
        
    });

    if ($$("a[name=deletePerm]"))
        $$("a[name=deletePerm]").addEvent('click', function(event) {
	    if (!confirm(gettext("Remove this permission?")))
	        event.stop();
	});
});