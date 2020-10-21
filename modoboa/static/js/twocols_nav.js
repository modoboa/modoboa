/**
 * Return an instance of TwocolsNav.
 *
 * @constructor
 */

/* global Listing */

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
        this.options = $.extend({}, this.defaults, options);
        this.options.defcallback = $.proxy(this.default_cb, this);
        Listing.prototype.initialize.call(this, this.options);
        this.listen();
        this.navobj.register_callback(
            "security", $.proxy(this.security_callback, this));
    },

    listen: function() {
        $("a.ajaxnav").click($.proxy(this.load_section, this));
        $(document).on("click", "#update", $.proxy(function(e) {
            var $form = $("form").first();
            simple_ajax_form_post(e, {
                formid: $form.attr("id"),
                modal: false,
                reload_on_success: false,
                success_cb: $.proxy(this.save_cb, this)
            });
        }, this));
        var formId = 'parameters_form';
        $(document).on('submit', '#' + formId, $.proxy(function(evt) {
            simple_ajax_form_post(evt, {
                formid: formId,
                modal: false,
                reload_on_success: false,
                success_cb: $.proxy(this.save_cb, this),
                error_cb: function(data) {
                    window.scrollTo(0, 0);
                    $('a[data-app="' + data.prefix + '"]').tab('show');
                }
            });
        }, this));
    },

    update_content: function(data) {
        if (data.content) {
            $('#' + this.options.divid).html(data.content);
        }
        this.update_listing(data, false);
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
            $field.attr("data-visibility-value") === value) {
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
        var $parent = $target.parents("div.form-group");

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
        var $parent = $target.parents("div.form-group");
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

    /**
     * Select an entry in the left menu based on current url.
     */
    select_left_menu: function() {
        $("a.ajaxnav").parent().removeClass("active");
        $("a[name=" + this.navobj.getbaseurl() + "]").parent().addClass("active");
    },

    default_cb: function(data) {
        this.select_left_menu();
        this.update_content(data);
    },

    /**
     * Navigation callback: security.
     */
    security_callback: function (data) {
        this.select_left_menu();
        this.update_content(data);
        $('#start-tfa-setup').click(this.startTFASetup);
        $('#finalize-tfa-setup').click(this.finalizeTFASetup);
        $('#deactivate-tfa').confirm({
            question: gettext('Are you sure?'),
            warning: gettext('This will invalidate your registered application.'),
            method: 'POST'
        });
        $('#tfa-refresh-codes').click(this.resetTFARecoveryCodes);
    },

    startTFASetup: function (evt) {
        evt.preventDefault();
        $.ajax({
            url: '/api/v1/account/tfa/setup/',
            type: 'post',
            contentType: 'application/json'
        }).done(function (resp) {
            window.location.reload();
        });
    },

    finalizeTFASetup: function (evt) {
        evt.preventDefault();
        var data = {
            pin_code: $('#pin-code').val()
        };
        $.ajax({
            url: '/api/v1/account/tfa/setup/check/',
            type: 'post',
            global: false,
            data: JSON.stringify(data),
            contentType: 'application/json'
        }).done(function (resp) {
            window.location.reload();
        }).fail(function (jqxhr) {
            var errors = JSON.parse(jqxhr.responseText);
            display_field_error($('#pin-code'), errors.pin_code.join(' '));
        });
    },

    resetTFARecoveryCodes: function (evt) {
        evt.preventDefault();
        $.ajax({
            url: $(this).attr('href'),
            type: 'post',
            contentType: 'application/json'
        }).done(function (resp) {
            var $container = $('#tfa-codes-area');
            var $ul = $('<ul>');
            $.each(resp.tokens, function (index, value) {
                var $li = $('<li />', { html: value });
                $ul.append($li);
            });
            $container.append($ul);
            $('#codes-modal').modal();
        });
    }
};

TwocolsNav.prototype = $.extend({}, Listing.prototype, TwocolsNav.prototype);
