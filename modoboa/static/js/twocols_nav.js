var TwocolsNav = function(options) {
    Listing.call(this, options);
};

TwocolsNav.prototype = {
    defaults: {
        deflocation: null,
        formid: "#form",
        divid: "#content",
        reload_exceptions: null
    },

    initialize: function(options) {
        Listing.prototype.initialize.call(this, options);
        this.options = $.extend({}, this.defaults, this.options);
        this.options.defcallback = $.proxy(this.default_cb, this);
        this.navobj = new History(this.options);
        this.listen();
    },

    listen: function() {
        $("a.ajaxlink").click($.proxy(this.load_section, this));
        $(document).on("click", "#update", $.proxy(function(e) {
            simple_ajax_form_post(e, {
                formid: this.options.formid,
                modal: false,
                reload_on_success: false,
                success_cb: $.proxy(this.save_cb, this)
            });
        }, this));
    },

    update_content: function(data) {
        if (data.content) {
            $('#' + this.options.divid).html(data.content);
        }
        this.update_listing(data);
        if (data.onload_cb) {
            eval(data.onload_cb + '()');
        }
        if (data.respmsg) {
            $("body").notify("error", data.respmsg);
        }
        $('#' + this.options.divid + ' select').change($.proxy(this.select_change, this));
        $('#' + this.options.divid + ' input[type=radio]').click($.proxy(this.radio_clicked, this));
        $(".help").popover({
            placement: 'bottom',
            trigger: 'hover'
        }).click(function(e) {e.preventDefault();});
        $('#' + this.options.divid + ' select').change();
        $('#' + this.options.divid + ' input[type=radio]:checked').click();
    },

    propagate_change: function($node) {
        var $select = $node.find("select");
        var $radio = $node.find("input[type=radio]");
        if ($select.length) {
            $select.change();
        }
        if ($radio.length) {
            $radio.click();
        }
    },

    toggle_field_visibility: function($field, $parent, value) {
        if ($parent.attr("disabled") === undefined &&
            $field.attr("data-visibility-value") == value) {
            $field.attr("disabled", null);
            $field.show();
            this.propagate_change($field);
        } else {
            $field.hide();
            $field.attr("disabled", "disabled");
            this.propagate_change($field);
        }
    },

    select_change: function(e) {
        var instance = this;
        var $target = $(e.target);
        var $parent = $target.parents("div.control-group");

        $('div[data-visibility-field="' + $target.attr("id") + '"]').each(function(idx) {
            instance.toggle_field_visibility($(this), $parent, $target.val());
        });
        $('h5[data-visibility-field="' + $target.attr("id") + '"]').each(function(idx) {
            instance.toggle_field_visibility($(this), $parent, $target.val());
        });
    },

    radio_clicked: function(e) {
        var instance = this;
        var $target = $(e.target);
        var $parent = $target.parents("div.control-group");
        var realid = $target.attr("id");

        realid = realid.substr(0, realid.length - 2);
        $('div[data-visibility-field="' + realid + '"]').each(function(idx) {
            instance.toggle_field_visibility($(this), $parent, $target.val());
        });
        $('h5[data-visibility-field="' + realid + '"]').each(function(idx) {
            instance.toggle_field_visibility($(this), $parent, $target.val());
        });
    },

    save_cb: function(data) {
        clean_form_errors(this.options.formid);
        if (this.options.reload_exceptions) {
            for (var i = 0; i < this.options.reload_exceptions.length; i++) {
                if (this.navobj.getbaseurl() == this.options.reload_exceptions[i]) {
                    window.location.reload();
                    break;
                }
            }
        }
        $("body").notify("success", data, 2000);
    },

    load_section: function(e) {
        var $link = get_target(e);
        e.preventDefault();
        this.navobj.parse_string($link.attr("href"), true).update();
    },


    default_cb: function(data) {
        $("a.ajaxlink").parent().removeClass("active");
        $("a[name=" + this.navobj.getbaseurl() + "]").parent().addClass("active");
        this.update_content(data);
    }
};

TwocolsNav.prototype = $.extend({}, Listing.prototype, TwocolsNav.prototype);
