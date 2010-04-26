window.addEvent('domready', function(){
    parse_menubar('topmenubar');
    SqueezeBox.assign($$('a.boxed'), {
        parse: 'rel',        
    });

    
    infobox = new InfoBox({
        parent : $("menubar"),
        message : "Loading"
    });
});

callbacks = {};

register_callback = function(name, callback) {
    callbacks[name] = callback;
}

get_callback = function(name) {
    return callbacks[name];
}

current_anchor = null;

check_anchor = function() {
    if (current_anchor.serialized == location.hash 
        && !$defined(current_anchor.force)) {
        return;
    }
    delete(current_anchor.force);
    current_anchor.from_string(location.hash);
    if (!current_anchor.serialized) {
        query = current_anchor.deflocation;
    } else {
        query = current_anchor.serialized.substring(1);
    }
    infobox.show("Loading...", "gray");
    new Request.JSON({url: query, onSuccess: function(resp) {
        callback = ($defined(resp.callback)) ? resp.callback : "default";
        callbacks[callback](resp);
         infobox.notice("Done");
        infobox.hide(1);
    }}).get();
}

ajaxListener = function(deflocation, defcallback) {
    current_anchor = new HashWrapper(deflocation);
    register_callback("default", defcallback);
    check_anchor.periodical(300);
}

/*
*
*/
function HashWrapper(deflocation) {
    this.deflocation = deflocation;
    this.params = $H();
    this.base = '';
    this.serialized = null;

    this.reset = function() {
        this.base = null;
        this.params.empty();
        return this;
    };

    this.parse_string = function(value, reset) {
        var splits = (value.charAt(0) == '#') 
            ? value.substring(1).split('?') : value.split('?');
        
        if (splits.length == 0) {
            return this;
        }
        if (!$defined(reset)) {
            reset = false;
        }
        if (reset) {
            this.reset();
        }
        this.base = (splits[0] == "") ? this.deflocation : splits[0];
        if (this.base[this.base.length - 1] != '/') {
            this.base += '/';
        }
        if (splits.length > 1) {
            params = splits[1].split('&');
            for (var i = 0; i < params.length; i++) {
                tmp = params[i].split('=');
                this.setparam(tmp[0], tmp[1]);
            }
        }
        return this;
    };

    this.from_string = function(value, reset) {
        this.parse_string(value);
        this.serialized = value;
        return this;
    };

    this.serialize = function() {
        var res = this.base;

        if (this.params.getLength() != 0) {
            res += "?" + this.params.toQueryString();
        }
        return res;
    };

    this.update = function(force) {
        location.hash = this.serialize();
        if ($defined(force)) {
            this.force = force;
        }
    };

    this.updateparams = function(str) {
        if (str.charAt(0) == '?') {
            str = str.substring(1);
        }
        var elems = str.split('&');
        for (var i = 0; i < elems.length; i++) {
            this.setparamfromstring(elems[i]);
        }
    };

    this.setparamfromstring = function(str) {
        var def = str.split('=');
        this.params.set(def[0], def[1]);
    };

    this.setparam = function(name, value) {
        this.params.set(name, value);
        return this;
    };
    
    this.setparams = function(params) {
        this.params.extend(params);
        return this;
    };

    this.getparam = function(name) {
        if (!this.params.has(name)) {
            return "";
        }
        return this.params.get(name);
    }

    this.baseurl = function(value) {
        this.reset();
        this.base = value;
        if (this.base[this.base.length - 1] != '/') {
            this.base += '/';
        }
        return this;
    };

    this.getbaseurl = function() {
        return this.base.substr(0, this.base.length - 1);
    };

    this.delparam = function(name) {
        if (!this.params.has(name)) {
            return false;
        }
        this.params.erase(name);
        return this;
    };
};

parse_menubar = function(id) {
    if ($(id)) {
	$(id).getElements('li.dropdown').each(function(elem){
	    var list = elem.getElement('ul.links');
	    var myFx = new Fx.Slide(list, {
                duration: 200
            }).hide();

            myFx.addEvent("start", function() {
                this.wrapper.setStyle("clear", "both");
            });

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
        SqueezeBox.assign($$('a.boxed'), {
            parse: 'rel',        
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

setDivHeight = function(id, extrah, modulo) {
    var contentsize = $(document.body).getSize().y 
        - $("topmenubar").getSize().y
        - $("header").getSize().y
        - $("footer").getSize().y
        - extrah;

    if (modulo) {
        contentsize -= contentsize % modulo;
    }
    $(id).setStyle("height", contentsize + "px");
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

checkTableSelection = function(text) {
    if (!$$("tr[class*=table-tr-selected]").length) {
        return false;
    }
    return confirm(text);
}

searchbox_init = function() {
    var myFx = new Fx.Slide($("searchparams"));
    myFx.hide();
    $("searchopts").addEvent("click", function(event) {
        myFx.cancel();
        myFx.toggle();
    });
    $$("input[name=scriteria]").addEvent("click", function(event) {
        myFx.cancel();
        myFx.toggle();
    });
    $("searchfield").addEvent("change", function(event) {
        var criteria = "";
        $$("input[name=scriteria]:checked").each(function(obj) {
            criteria = obj.value;
        });
        var params = "pattern=" + $("searchfield").value
            + "&criteria=" + criteria;
        current_anchor.updateparams(params);
        current_anchor.update();
    });
    $("searchfield").addEvent("click", function(event) {
        $("searchfield").select();
    });
    
    $("searchfield").addEvent("blur", function(event) {
        if ($("searchfield").value == "") {
            $("searchfield").set("value", "Search...");
        }
    });
    $("searchbox").setStyle("float", "right");
}