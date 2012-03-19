/*
 * Collection of functions that are accessible to every page.
 */

function modalbox(e, css) {
    e.preventDefault();
    var href = $(this).attr('href');
    var modalcb = $(this).attr('modalcb');

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
        var $div = $('<div id="modalbox" class="modal fade" >' + data + '</div>')
            .modal()
            .one('shown', function() {
                if (modalcb != undefined) {
                    eval(modalcb + '()');
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
    var $form = $("form");
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