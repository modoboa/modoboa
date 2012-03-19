$(document).ready(function() {
    $(document).on('click', 'a[data-toggle="ajaxmodal"]', modalbox);
    $(document).on('click', 'a[data-toggle="ajaxmodal-autowidth"]', modalbox_autowidth);

    //parse_menubar('#topmenubar');
    //parse_menubar('#menubar');

    /*infobox = new InfoBox({
        parent : $("menubar"),
        message : "Loading"
    });*/

    /* Specific javascript code for the demo... not the best place */
    /*$$("a[name=sendspam], a[name=sendvirus]").addEvent("click", function(evt) {
        evt.stop();
        new Request.JSON({
            url: this.get("href"),
            onSuccess: function(response) {
                if (response.status == "ok") {
                    infobox.info(gettext("Message sent"));
                    infobox.hide(1);
                } else {
                    infobox.error(response.respmsg);
                }
            }
        }).get();
    });*/
});

var media_url = "";

/*
 * A simple function to initialize the value of the global variable
 * 'media_url' (corresponding to django's MEDIA_URL variable).
 */
function set_media_url(url) {
  media_url = url;
}

/*
 * Shortcut function that construct an url from the media_url and the
 * given value.
 */
function static_url(value) {
  return media_url + value;
}

/*
 * Easy way to deactivate a link (ie. clicking on it does nothing)
 */
function disable_link(link) {
    link.removeEvents("click")
        .addEvent("click", function(evt) {
            evt.stop();
        });
}

/*
 * Easy way to re-activate a link that was previously disabled. An
 * extra argument can be passed to specify a new "click" event
 * callback.
 */
function enable_link(link, callback) {
    link.removeEvents("click");
    if ($defined(callback)) {
        link.addEvent("click", callback);
    }
}

function parse_menubar(id) {
    var $menubar = $(id);

    if ($menubar == undefined) {
        return;
    }
    $menubar.find('.dropdown-toggle').dropdown();
    $menubar.find('a[data-toggle="modal"]').click(function(e) {
        console.log(this);
        e.preventDefault();
        var href = $(this).attr('href');

        if (href.indexOf('#') == 0) {
            $(href).modal('open');
        } else {
            $.get(href, function(data) {
                $('<div class="modal" >' + data + '</div>').modal();
            }).success(function() {
                $('input:text:visible:first').focus();
            });
        }
    });

        /*.each(function(elem){
      var list = elem.getElement('ul.links');
      var myFx = new Fx.Slide(list, {
        duration: 200
      });

      var coords = elem.getCoordinates();

      myFx.wrapper.setStyles({
          position : "absolute",
          left : coords['left']
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
    });*/
    /*SqueezeBox.assign($(id).getElements('a[class=boxed]'), {
      parse: 'rel'
    });*/

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
	$$("tr").addEvent("dblclick", function(event) {
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

/*function saveparams(id, message) {
    $("#update").click(function(evt) {
        evt.preventDefault();
        var $form = $("form");

        $.post($form.attr("action"), $form.serialize(), function(data) {
            if (data.status == "ok") {
                $("body").notify("success", message, 2000);
            }
        });
    });
};*/

