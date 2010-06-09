window.addEvent('domready', function() {
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

});
