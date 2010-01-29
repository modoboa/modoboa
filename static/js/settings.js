window.addEvent('domready', function() {
    SqueezeBox.assign($$('a.boxed'), {
        parse: 'rel',
        
    });

    if ($$("a[name=deletePerm]"))
        $$("a[name=deletePerm]").addEvent('click', function(event) {
	    if (!confirm(gettext("Remove this permission?")))
	        event.stop();
	});

    var tip = new Tips($$(".Tips"));

    var accordion = new Accordion('h3.atStart', 'div.atStart', {
	opacity: false,
	onActive: function(toggler, element){
	    toggler.setStyle('color', '#ff3300');
	},
        
	onBackground: function(toggler, element){
	    toggler.setStyle('color', '#222');
	}
    }, $('accordion'));

});