window.addEvent('domready', function(){
    parse_menubar('topmenubar');
    parse_menubar('menubar');

    infobox = new InfoBox({
        parent : $("menubar"),
        message : "Loading"
    });
});

callbacks = {};

register_callback = function(name, callback) {
    callbacks[name] = callback;
};

get_callback = function(name) {
    return callbacks[name];
};

current_anchor = null;

check_anchor = function() {
    if (current_anchor.serialized == location.hash
        && !$defined(current_anchor.force)) {
        return;
    }
    delete(current_anchor.force);
    current_anchor.from_string(location.hash);
    if (!current_anchor.serialized) {
        location.hash = current_anchor.deflocation;
        return;
    } else {
        query = current_anchor.serialized.substring(1);
    }
    infobox.show(gettext("Loading..."), {
        profile: "gray",
        spinner: true
    });
    new Request.JSON({url: query, noCache : true, onSuccess: function(resp) {
        callback = ($defined(resp.callback)) ? resp.callback : "default";
        callbacks[callback](resp);
        infobox.info(gettext("Done"));
        infobox.hide(1);
    }}).get();
};

ajaxListener = function(deflocation, defcallback) {
    current_anchor = new HashWrapper(deflocation);
    register_callback("default", defcallback);
    check_anchor.periodical(300);
};

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
        /*if (this.base[this.base.length - 1] != '/') {
            this.base += '/';
        }*/
	var re = new RegExp("/$");
	if (!this.base.match(re)) {
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
        window.fireEvent("pageRefresh");
        location.hash = this.serialize();
        if ($defined(force)) {
            this.force = force;
        }
    };

    this.deleteParam = function(str) {
        this.params.erase(str);
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
    };

    this.baseurl = function(value) {
        this.reset();
        this.base = value;
 	var re = new RegExp("/$");
	if (!this.base.match(re)) {
		this.base += '/';
	}
        return this;
    };

    this.addbaseurl = function(value) {
        newbase = this.base + value;
        return this.baseurl(newbase);
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
            });

            myFx.wrapper.setStyles({
                /*"clear" : "both",*/
                "position" : "absolute"
            });
            myFx.hide();

	    elem.addEvents({
		'mouseenter' : function(evt) {
		    myFx.cancel();
		    myFx.slideIn();
		},
		'mouseleave' : function() {
		    myFx.cancel();
		    myFx.slideOut();
		}
	    });
	});
        SqueezeBox.assign($(id).getElements('a[class=boxed]'), {
            parse: 'rel'
        });
    }
};

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
};

confirmation = function(question, action, callback) {
    SqueezeBox.initialize({
        size: {x: 350, y: 140},
	handler: 'iframe',
        onClose: function(content) {
            var ibody = get_iframe_body(this.asset);
            var elt = ibody.getElement("input[name=result]");

            if (elt.get("value") == "ok") {
                var params = "";
                if (typeof callback != "undefined") {
                    params = callback(ibody);
                }
                new Request.JSON({
                    method: "get",
                    url: action.get("href"),
                    onSuccess: function(res) {
			if (res.status == "ok") {
			    window.location.reload();
			} else {
			    infobox.error(res.error);
			    infobox.hide(2);
			}
                    }
                }).send(params);
            }
        }
    });

    /* FIXME: avoid using a hard coded address like this, maybe it
     could be fixed by creating a new class for "confirmation" and
     create one instance for each section/page using it (I mean
     directly inside the html template) */

    SqueezeBox.open("/modoboa/userprefs/confirm/?question=" + question);
};

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
};

bindRows = function(rooturl, page) {
    $$("tr").addEvent("click", function(event) {
        if (event.target.parentNode.id) {
            var url = rooturl + "?domid=" + event.target.parentNode.id;
	    if (page != "") {
		url += "?page=" + page;
	    }
            event.target.parentNode.setStyle("background", "#ffffcc");
            location.href = url;
        }
    });
};

toggleSelection = function(id, value) {
    $$("input[name=" + id + "]").each(function(obj) {
        obj.checked = value;
    });
};

checkTableSelection = function(text) {
    if (!$$("tr[class*=table-tr-selected]").length) {
        return false;
    }
    return confirm(text);
};

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
        var pattern = $("searchfield").get("value");
        if (pattern != "") {
            var params = "pattern=" + pattern + "&criteria=" + criteria;
            current_anchor.updateparams(params);
        } else {
            current_anchor.deleteParam("pattern");
            current_anchor.deleteParam("criteria");
        }
        current_anchor.update();
    });
    $("searchfield").addEvent("click", function(event) {
        $("searchfield").select();
    });

    $("searchfield").addEvent("blur", function(event) {
        if ($("searchfield").value == "") {
            $("searchfield").set("value", gettext("Search..."));
        }
    });
    $("searchbox").setStyle("float", "left");
    var frag = new URI(location.href).get("fragment");
    if (frag.indexOf('?') != -1) {
        var params = frag.substring(frag.indexOf('?') + 1).parseQueryString();
        if ($defined(params.pattern)) {
            $("searchfield").set("value", params.pattern);
        }
        if ($defined(params.criteria)) {
            $("crit_" + params.criteria).checked = true;
        }
    }
};

// The following code prevents a bug under IE7 because fullpath is
// returned instead of a relative one. (even if mootools uses
// getAttribute("href", 2), this is not working for AJAX requests)
gethref = function(obj) {
    var url = obj.get("href");
    var re = new RegExp("^(https?):");
    var scheme = re.exec(url);

    if (scheme != null) {
        var baseurl = scheme[0] + "://" + location.host + location.pathname;
        return url.replace(baseurl, "");
    }
    return url;
};

saveparams = function(id, message) {
    $$("input[name=update]").addEvent("click", function(evt) {
        evt.stop();
        $(id).set("send", {
            onSuccess: function(response) {
                var decode = JSON.decode(response);
                if (decode.status == "ok") {
                    infobox.info(message);
                    infobox.hide(1);
                }
            }
        }).send();
    });
};