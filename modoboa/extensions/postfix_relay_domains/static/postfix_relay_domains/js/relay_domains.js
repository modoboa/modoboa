/**
 * @module relay_domains
 * @desc Utility class to manage relay domains.
 */

var RelayDomains = function(options) {
    this.initialize(options);
};

RelayDomains.prototype = {
    constructor: RelayDomains,

    defaults: {
    },

    initialize: function(options) {
        this.options = $.extend({}, this.defaults, options);
        admin.register_tag_handler("srv", this.srv_tag_handler);
    },

    launch_scan: function(e) {
        var $link = get_target(e);

        e.preventDefault();
        $.ajax({
            type: "POST",
            url: $link.attr("href")
        }).done(function(data) {
            var $widget = $('#id_service');

            $widget.empty();
            $.each(data, function(label, id) {
                $widget.append($('<option />', {
                    value: id,
                    html: label
                }));
            });
            $('.modal-body').prepend(
                build_success_alert(gettext('Services updated'))
            );
        }).fail(function(jqxhr) {
            if (jqxhr.getResponseHeader('Content-Type') != 'application/json') {
                return;
            }
            var result = $.parseJSON(jqxhr.responseText);
            $('.modal-body').prepend(
                build_error_alert(result[0])
            );
        });
    },

    domainform_cb: function() {
        $('#btnscan').click(this.launch_scan);
        $('input:text:visible:first').focus();
        $("#id_aliases").dynamic_input();
        $(".submit").on('click', $.proxy(function(e) {
            simple_ajax_form_post2(e, {
                formid: "rdomform",
                reload_on_success: false,
                success_cb: $.proxy(admin.reload_listing, admin)
            });
        }, this));
    },

    srv_tag_handler: function(tag, $link) {
        if (this.navobj.getparam(tag + "filter") == undefined && $link.hasClass(tag)) {
            var text = $link.attr("name");
            this.navobj
                .setparam("domfilter", "relaydomain")
                .setparam(tag + "filter", text)
                .update();
            if ($("a[name=dom]").length == 0) {
                $("#searchform").parent().after(this.make_tag("relaydomain", "dom"));
            }
            $("#searchform").parent().after(this.make_tag(text, tag));
            return true;
        }
        return false;
    }
};
