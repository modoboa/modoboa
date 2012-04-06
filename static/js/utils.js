/*
 * Collection of functions that are accessible to every page.
 */

function modalbox(e, css, defhref, defcb) {
    e.preventDefault();
    var href = (defhref != undefined) ? defhref : $(this).attr('href');
    var modalcb = (defcb != undefined) ? defcb : $(this).attr('modalcb');

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
        var $div = $('<div id="modalbox" class="modal" >' + data + '</div>')
            .modal()
            .one('shown', function() {
                if (modalcb != undefined) {
                    if (typeof modalcb === "function") {
                        modalcb();
                    } else {
                        eval(modalcb + '()');
                    }
                }
            })
            .on('hidden', function() {
                $("#modalbox").remove();
            });

        if (css != undefined) {
            $div.css(css);
        }
    });
}

function modalbox_autowidth(e) {
    modalbox.apply(this, [e, {width: 'auto'}]);
}

/*
 * Simple function that redirect ajax requests to the login page if
 * the status code received with a response is equal to 278.
 */
function ajax_login_redirect() {
    if (this.status != 278) {
        return;
    }
    var params = "?next=" + window.location.pathname;

    window.location.href =
        this.xhr.getResponseHeader("Location").replace(/\?.*$/, params);
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
    var $form = (options.formid != undefined) ? $("#" + options.formid) : $("form");
    var defaults = {reload_on_success: true, reload_mode: 'full'};
    var opts = $.extend({}, defaults, options);
    var args = $form.serialize();

    if (options.extradata != undefined) {
        args += "&" + options.extradata;
    }
    $.post($form.attr("action"), args, function(data) {
        if (data.status == "ok") {
            if (opts.success_cb != undefined) {
                opts.success_cb(data);
            }
            $("#modalbox").modal('hide');
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
            if (data.content != "") {
                $('.modal').html(data.content);
            }
            if (data.respmsg) {
                $('.modal-body').prepend(build_error_alert(data.respmsg));
            }
            if (opts.error_cb != undefined) {
                opts.error_cb();
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
 * Simple wrapper around Request.JSON. We just ensure that
 * redirections are correctly catched. (on session timeout for
 * example)
 */
// Request.JSON.mdb = new Class({
//     Extends: Request.JSON,

//     options: {
//         format: "json",
//         onComplete: ajax_login_redirect,
//         onFailure: function(xhr) {
//             $(document.body).setStyle("overflow", "auto");
//             $(document.body).set("html", xhr.responseText);
//         }
//     }
// });

/*
 * 'Change password' form initialization.
 */
function chpasswordform_cb() {
    $(".submit").one('click', function(e) {
        simple_ajax_form_post(e, {
            error_cb: chpasswordform_cb
        });
    });
}

/*
 * Send a simple AJAX request.
 */
function simple_ajax_request(e) {
    var $this = $(this);
    e.preventDefault();
    $.ajax({
        url: $this.attr("href"),
        dataType: 'json',
        success: function(data) {
            if (data.status == "ok") {
                $("body").notify("success", data.respmsg, 2000);
            } else {
                $("body").notify("error", data.respmsg);
            }
        }
    });
}