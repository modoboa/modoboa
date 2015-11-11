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
        $(document).bind('domform_init', $.proxy(this.domain_form_init_cb, this));
    },

    domain_form_init_cb: function() {
        $('#btnscan').click(this.launch_scan);
    },

    launch_scan: function(e) {
        var $link = get_target(e);

        e.preventDefault();
        $.ajax({
            type: "POST",
            url: $link.attr("href"),
            global: false
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
            var result = $.parseJSON(jqxhr.responseText);
            $('.modal-body').prepend(
                build_error_alert(result[0])
            );
        });
    },

    srv_tag_handler: function(tag, $link) {
        if (this.navobj.getparam(tag + "filter") === undefined && $link.hasClass(tag)) {
            var text = $link.attr("name");
            this.navobj
                .setparam("domfilter", "relaydomain")
                .setparam(tag + "filter", text)
                .update();
            if ($("a[name=dom]").length === 0) {
                $("#taglist").append(this.make_tag("relaydomain", "dom"));
            }
            $("#taglist").append(this.make_tag(text, tag));
            return true;
        }
        return false;
    }
};
