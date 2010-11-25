window.addEvent('domready', function() {
    var tip = new Tips($$(".Tips"));

    var addperm_url = "";
    var accordion = new Accordion('h3.atStart', 'div.atStart', {
	opacity: true,
	onActive: function(toggler, element){
	    toggler.setStyle('color', '#ff3300');
	    addperm_url = element.get("name");
	},

	onBackground: function(toggler, element) {
	    toggler.setStyle('color', '#222');
	}
    }, $('accordion'));

    $$("a[name=addperm]").addEvent("click", function(evt) {
	evt.stop();
	if (addperm_url == "") {
	    return;
	}
	SqueezeBox.initialize({
	    size: {x: 300, y: 280},
	    handler: 'iframe'
	});
	SqueezeBox.open(addperm_url);
    });
});