window.addEvent('domready', function(){
    if ($('menu2')) {
	$('menu2').getElements('li.dropdown').each( function( elem ){
	    var list = elem.getElement('ul.links');
	    var myFx = new Fx.Slide(list).hide();
	    elem.addEvents({
		'mouseenter' : function(){
		    myFx.cancel();
		    myFx.slideIn();
		},
		'mouseleave' : function(){
		    myFx.cancel();
		    myFx.slideOut();
		}
	    });
	});
    }
});

var toggleModal = function(backgroundColour, options) {
    // modal view for the whole screen
    // ver 2.02 17/10/2008 03:42:06
    if ($("modal")) {
        $("modal").dispose();
        return false;
    }
    
    var options = $merge({
        zIndex: 10000000,
        opacity: .8,
        events: $empty()
    }, options);

    if (!$type(backgroundColour) && !$("modal"))
        return false;

    return new Element("div", {
        id: "modal",
        styles: {
            position: "absolute",
            top: 0,
            left: 0,
            width: window.getScrollWidth(),
            height: window.getScrollHeight(),
            background: backgroundColour,
            "z-index": options.zIndex
        },
        opacity: options.opacity,
        events: options.events
    }).inject(document.body);
}

confirmation = function(question) {
    SqueezeBox.initialize({
        size: {x: 300, y: 150},
	handler: 'iframe'
    });
    SqueezeBox.open("/mailng/main/confirm/?question=" + question);
}
