window.addEvent('domready', function(){
    parse_menubar('topmenubar');
    parse_menubar('menubar');
    SqueezeBox.assign($$('a.boxed'), {
        parse: 'rel',        
    });
});

parse_menubar = function(id) {
    if ($(id)) {
	$(id).getElements('li.dropdown').each( function( elem ){
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
}

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
        size: {x: 350, y: 140},
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

setContentSize = function(cellsize) {
    var contentsize = $(document.body).getSize().y - $("topmenubar").getSize().y
        - $("header").getSize().y;

    contentsize -= $("navbar").getSize().y * 2;
    contentsize -= contentsize % cellsize;
    $("listing").setStyle("height", contentsize + "px");
}

bindRows = function(rooturl, page) {
    $$("tr").addEvent("click", function(event) {
        if (event.target.parentNode.id) {
            var url = rooturl + event.target.parentNode.id + "?page=" + page;
            event.target.parentNode.setStyle("background", "#ffffcc");
            location.href = url;
        }
    });
}

toggleSelection = function(id, value) {
    $$("input[name=" + id + "]").each(function(obj) {
        obj.checked = value;
    });
}

checkSelection = function(id, text) {
    var getout = $$("input[name=" + id + "]").every(function(item, index) {
        return item.checked == false;
    });
    if (getout) {
        return false;
    }
    return confirm(text);
}