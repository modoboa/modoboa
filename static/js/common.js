window.addEvent('domready', function(){
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
    })
});