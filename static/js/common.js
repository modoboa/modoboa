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

get_iframe_body = function(id) {
    var saf = navigator.userAgent.match(/Safari/i);
    var safver = (saf ? parseFloat(navigator.userAgent.match(/[\d\.]+Safari/i)) : 0);
    var targetif = $(id);
    var data;

    if (targetif.contentDocument && (!saf || (saf && safver >= 3))) {
        // NS6 & Gecko & Opera & IE7+
        if (!saf || (saf && safver >= 3)) {
            data = targetif.contentDocument.defaultView.document.body;
        } else {
            data = targetif.document.body;
        }      
    } else if (targetif.contentWindow && !saf) {
        // IE 5.5 & 6.x
        data = targetif.contentWindow.document.body;
    }
    return (data);  
}

confirmation = function(question, action, callback) {
    SqueezeBox.initialize({
        size: {x: 300, y: 130},
	handler: 'iframe',
        onClose: function(content) {
            var ibody = get_iframe_body(this.asset);
            var elt = ibody.getElement("input[name=result]");

            if (elt.get("value") == "ok") {
                params = ""
                if (typeof callback != "undefined") {
                    params = callback(ibody);
                }
                new Request({
                    method: "get", 
                    url: action.get("href"),
                    onSuccess: function(res) {
                        window.location.reload();
                    }
                }).send(params);
            }
        }
    });
    SqueezeBox.open("/mailng/main/confirm/?question=" + question);
}
