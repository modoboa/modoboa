/*
 * Global javascript utilities
 */

var static_url = "";

/*
 * A simple function to initialize the value of the global variable
 * 'media_url' (corresponding to django's MEDIA_URL variable).
 */
function set_static_url(url) {
    static_url = url;
}

/*
 * Shortcut function that construct an url from the media_url and the
 * given value.
 */
function get_static_url(value) {
    return static_url + value;
}

function modalbox(e, css, defhref, defcb, defclosecb) {
    e.preventDefault();
    var $this = $(this);
    var href = (defhref != undefined) ? defhref : $this.attr('href');
    var modalcb = (defcb != undefined) ? defcb : $this.attr('modalcb');
    var closecb = (defclosecb != undefined) ? defclosecb : $this.attr("closecb");

    if (href.indexOf('#') == 0) {
        $(href).modal('open');
        return;
    }
    $.get(href, function(data) {
        if (typeof data === "object") {
            if (data.status == "ko" && data.respmsg) {
                $("body").notify("error", data.respmsg);
            }
            return;
        }
        var $div = $('<div />', {
            id: "modalbox", 'class': "modal", html: data
        });

        $div.modal({show: false});
        $div.one('shown', function() {
            $(".help").popover({
                container: "#modalbox"
            }).click(function(e) {e.preventDefault();});
            if (modalcb != undefined) {
                if (typeof modalcb === "function") modalcb(); else eval(modalcb + '()');
            }
        })
        .on('hidden', function(e) {
            var $target = $(e.target);

            if (!$target.is($(this))) {
                return;
            }
            $("#modalbox").remove();
            if (closecb != undefined) {
                if (typeof closecb === "function") closecb(); else eval(closecb + '()');
            }
        });
        $div.modal('show');

        if (css != undefined) {
            $div.css(css);
        }
    });
}

function modalbox_autowidth(e) {
    modalbox.apply(this, [e, {
        width: 'auto',
        'margin-left': function() { return -($(this).width() / 2); }
    }]);
}

/*
 * Simple shorcut do create a bootstrap alert box (error mode)
 */
function build_error_alert(msg) {
    return $('<div class="alert alert-error"> \
<a class="close" data-dismiss="alert" href="#">&times;</a>' + msg + "</div>");
}

/*
 * '.keys()' method support for old browsers :p
 */
if (!Object.keys) {
    Object.keys = function (obj) {
        var keys = [],
            k;
        for (k in obj) {
            if (Object.prototype.hasOwnProperty.call(obj, k)) {
                keys.push(k);
            }
        }
        return keys;
    };
}

/*
 * Simple function that sends a form using an 'ajax' post request.
 *
 * The function is intended to be used in a modal environment.
 */
function simple_ajax_form_post(e, options) {
    e.preventDefault();
    var $form = (options.formid !== undefined) ? $("#" + options.formid) : $("form");
    var defaults = {reload_on_success: true, reload_mode: 'full', modal: true};
    var opts = $.extend({}, defaults, options);
    var args = $form.serialize();

    if (options.extradata != undefined) {
        args += "&" + options.extradata;
    }
    $.post($form.attr("action"), args, function(data) {
        if (data.status == "ok") {
            $("#modalbox").modal('hide');
            if (opts.success_cb != undefined) {
                opts.success_cb(data);
                return;
            }
            if (opts.reload_on_success) {
                if (opts.reload_mode == 'full') {
                    window.location.reload();
                } else {
                    history.update(true);
                }
            }
            if (data.respmsg) {
                $("body").notify('success', data.respmsg, 2000);
            }
        } else {
            if (opts.modal) {
                if (data.content != "") {
                    $('.modal').html(data.content);
                }
                if (data.respmsg) {
                    $('.modal-body').prepend(build_error_alert(data.respmsg));
                }
            }
            if (opts.error_cb != undefined) {
                opts.error_cb(data);
            }
        }
    });
}

/*
 * The following code prevents a bug under IE7 because fullpath is
 * returned instead of a relative one. (even if mootools uses
 * getAttribute("href", 2), this is not working for AJAX requests)
 */
function gethref(obj) {
    var url = $(obj).attr("href");
    var re = new RegExp("^(https?):");
    var scheme = re.exec(url);

    if (scheme != null) {
        var baseurl = scheme[0] + "://" + location.host + location.pathname;
        return url.replace(baseurl, "");
    }
    return url;
};

/*
 * Extract the current URL parameters into a dictionnary.
 *
 * Ref:
 * http://stackoverflow.com/questions/901115/get-query-string-values-in-javascript
 */
function parse_qs(raw) {
    if (raw == "") return {};
    var res = {};

    for (var i = 0; i < raw.length; i++) {
        var p = raw[i].split('=');

        if (p.length != 2) continue;
        res[p[0]] = decodeURIComponent(p[1].replace(/\+/g, " "));
    }
    return res;
}

/*
 * Return the target associated to an event object.
 */
function get_target(e, tag) {
    var $target = $(e.target);

    if (tag === undefined || $target.is(tag)) {
        return $target;
    }
    return $target.parent();
}

/*
 * Send a simple AJAX request.
 */
function simple_ajax_request(e, uoptions) {
    var $this = $(this);
    var defaults = {};
    var options = $.extend({}, defaults, uoptions);

    if (e != undefined) e.preventDefault();
    $.ajax({
        url: $this.attr("href"),
        dataType: 'json',
        success: function(data) {
            if (data.status == "ok") {
                if (options.ok_cb) options.ok_cb(data);
                if (data.respmsg) {
                    $("body").notify("success", data.respmsg, 2000);
                }
            } else {
                $("body").notify("error", data.respmsg);
            }
        }
    });
}

/*
 * Simple function that redirect ajax requests to the login page if
 * the status code received with a response is equal to 278.
 */
function ajax_login_redirect(xhr) {
    if (xhr.status != 278) {
        return;
    }
    var params = "?next=" + window.location.pathname;

    window.location.href =
        xhr.getResponseHeader("Location").replace(/\?.*$/, params);
}

function activate_widget(e) {
    var $this = $(this);
    var widget_id = $this.attr("id").substr(0, $this.attr("id").length - 4);
    var $widget = $('#' + widget_id);

    if ($this.attr("checked") && $this.attr("checked") == "checked") {
        $widget.attr('disabled', true);
    } else {
        $widget.attr('disabled', false);
    }
}

$(document).ready(function() {
    $(document).ajaxSuccess(function(e, xhr, settings) { ajax_login_redirect(xhr); });
    $(document).on('click', 'a[data-toggle="ajaxmodal"]', modalbox);
    $(document).on('click', 'a[data-toggle="ajaxmodal-autowidth"]', modalbox_autowidth);
    $(document).on('click', '.activator', activate_widget);
    $(".help").popover().click(function(e) {e.preventDefault();});
});