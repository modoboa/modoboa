window.addEvent('domready', function() {
    if ($$("a[name=deletePerm]"))
        $$("a[name=deletePerm]").addEvent('click', function(event) {
	    if (!confirm(gettext("Remove this permission?")))
	        event.stop();
	});

    var tip = new Tips($$(".Tips"));

    var accordion = new Accordion('h3.atStart', 'div.atStart', {
	opacity: true,
	onActive: function(toggler, element){
	    toggler.setStyle('color', '#ff3300');
	},
        
	onBackground: function(toggler, element){
	    toggler.setStyle('color', '#222');
	}
    }, $('accordion'));
    saveparams("params_form", gettext("Parameters saved"));
});