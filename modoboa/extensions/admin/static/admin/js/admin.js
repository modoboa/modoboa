/**
 * @module admin
 * @desc Utility classes for the admin application
 */

var Admin = function(options) {
    Listing.call(this, options);
};
    
Admin.prototype = {
    defaults: {
        deflocation: "list/",
        squery: null
    },

    initialize: function(options) {
        this.options = $.extend({}, this.defaults, options);
        this.options.defcallback = $.proxy(this.list_cb, this);
        Listing.prototype.initialize.call(this, this.options);
        this.listen();
    },

    list_cb: function(data) {
        $("#listing").html(data.table);
        this.update_listing(data);
        $("a.filter").click($.proxy(this.filter_by_tag, this));
    },

    /**
     * Children must override this method.
     */
    listen: function() {
    },

    importform_cb: function() {
        $(".submit").one('click', function(e) {
            e.preventDefault();
            if ($("#id_sourcefile").val() === "") {
                return;
            }
            $("#import_status").css("display", "block");
            $("#import_result").html("").removeClass("alert alert-error");
            $("#importform").submit();
        });
    },

    importdone: function(status, msg) {
        $("#import_status").css("display", "none");
        if (status == "ok") {
            $("#modalbox").modal('hide');
            this.reload_listing(msg);
        } else {
            $("#import_result").addClass("alert alert-error");
            $("#import_result").html(msg);
            this.importform_cb();
        }
    },

    exportform_cb: function() {
        $(".submit").one('click', function(e) {
            e.preventDefault();
            $("#exportform").submit();
            $("#modalbox").modal('hide');
        });
    },

    reload_listing: function(data) {
        this.navobj.update(true);
        if (data) {
            $("body").notify("success", data, 2000);
        }
    }
};

Admin.prototype = $.extend({}, Listing.prototype, Admin.prototype);

/*
 * Domains
 */
var Domains = function(options) {
    Admin.call(this, options);
};

Domains.prototype = {
    initialize: function(options) {
        Admin.prototype.initialize.call(this, options);
        this.register_tag_handler("dom", this.generic_tag_handler);
    },

    list_cb: function(data) {
        Admin.prototype.list_cb.call(this, data);
        var deloptions = (data.handle_mailboxes)
            ? {keepdir: gettext("Do not delete domain directory")}
            : {};
        var warnmsg = (data.auto_account_removal && data.auto_account_removal == "yes")
            ? gettext("This operation will remove ALL data associated to this domain.")
            : gettext("This operation will remove all data associated to this domain, excepting accounts.");

        $("a[name=deldomain]").confirm({
            question: function() { return this.$element.attr('title'); },
            method: "POST",
            warning: warnmsg,
            checkboxes: deloptions,
            success_cb: $.proxy(this.reload_listing, this)
        });
        $(document).trigger('domain_listing_refresh');
    },

    change_inputs_state: function(value) {
        $("#id_dom_admin_username").attr("disabled", value);
        $("input[name=create_aliases]").attr("disabled", value);
    },

    create_dom_admin_changed: function(e) {
        var $target = $(e.target);
        this.change_inputs_state(($target.val() == "yes") ? false : true);
    },

    generalform_init: function() {
        $('input:text:visible:first').focus();
        $("#id_aliases").dynamic_input();
    },

    optionsform_init: function() {
        $("input[name=create_dom_admin]").click($.proxy(this.create_dom_admin_changed, this));
        this.change_inputs_state(
            $("input[name=create_dom_admin]:checked").val() == "yes" ? false : true
        );
        this.optionsform_prefill();
    },

    optionsform_prefill: function() {
        var $span = $("#id_dom_admin_username").next("span");
        $span.html("@" + $("#id_name").val());
    },

    domadminsform_init: function() {
        $("a[name=removeperm]").click(function(e) {
            var $tr = $(this).parents('tr');
            simple_ajax_request.apply(this, [e, {
                ok_cb: function(resp) {
                    $tr.remove();
                    if (!$("#domadmins").find("tr").length) {
                        $("#admins").html('<div class="alert alert-info">'
                            + gettext("No domain administrator defined") + "</div>");
                    }
                }
            }]);
        });
    },

    newdomain_cb: function() {
        this.generalform_init();
        this.optionsform_init();
        $("#wizard").cwizard({
            formid: "domform",
            transition_callbacks: {
                1: this.optionsform_prefill
            },
            error_callbacks: {
                2: $.proxy(this.optionsform_init, this)
            },
            success_callback: $.proxy(this.reload_listing, this)
        });
    },

    domainform_cb: function() {
        this.generalform_init();
        this.domadminsform_init();
        $(".submit").one('click', $.proxy(function(e) {
            simple_ajax_form_post(e, {
                formid: "domform",
                error_cb: $.proxy(this.domainform_cb, this),
                reload_on_success: false,
                success_cb: $.proxy(this.reload_listing, this)
            });
        }, this));
        $(document).trigger('domform_init');
    }
};

Domains.prototype = $.extend({}, Admin.prototype, Domains.prototype);

/*
 * Identities
 */
var Identities = function(options) {
    Admin.call(this, options);
};

Identities.prototype = {
    initialize: function(options) {
        Admin.prototype.initialize.call(this, options);
        this.domain_list = [];
        this.register_tag_handler("idt", this.generic_tag_handler);
        this.register_tag_handler("grp", this.grp_tag_handler);
    },

    listen: function() {
        Admin.prototype.listen.call(this);
        $(document).on("click", "a.ajaxlink", $.proxy(this.page_loader, this));
    },

    page_loader: function(e) {
        var $link = get_target(e);
        e.preventDefault();
        this.navobj.baseurl($link.attr("href")).update();
    },

    list_cb: function(data) {
        Admin.prototype.list_cb.call(this, data);
        var deloptions = {};

        if (data.handle_mailboxes == "yes") {
            deloptions = {keepdir: gettext("Do not delete mailbox directory")};
        }

        $("a[name=delaccount]").confirm({
            question: function() { return this.$element.attr('title'); },
            method: "POST",
            checkboxes: deloptions,
            success_cb: $.proxy(this.reload_listing, this)
        });
        $("a[name=delalias]").confirm({
            question: function() { return this.$element.attr('title'); },
            method: "DELETE",
            success_cb: $.proxy(this.reload_listing, this)
        });
    },

    grp_tag_handler: function(tag, $link) {
        if (this.navobj.getparam(tag + "filter") === undefined && $link.hasClass(tag)) {
            var text = $link.attr("name");
            this.navobj
                .setparam("idtfilter", "account")
                .setparam(tag + "filter", text)
                .update();
            if ($("a[name=idt]").length === 0) {
                $("#searchform").parent().after(this.make_tag("account", "idt"));
            }
            $("#searchform").parent().after(this.make_tag(text, tag));
            return true;
        }
        return false;
    },

    /**
     * Retrieve a list of domain from the server.
     *
     * @this Identities
     * @return {Array} a list of domain names
     */
    get_domain_list: function() {
        if (!this.domain_list.length) {
            $.ajax({
            url: this.options.domain_list_url,
                dataType: "json",
                async: false
            }).done($.proxy(function(data) {
                this.domain_list = data;
            }, this));
        }
        return this.domain_list;
    },

    simpleuser_mode: function() {
        $("#id_username").autocompleter({
            from_character: "@",
            choices: $.proxy(this.get_domain_list, this)
        });
        $("#id_email").addClass("disabled")
            .attr("readonly", "")
            .autocompleter("unbind");
    },

    normal_mode: function() {
        $("#id_email").removeClass("disabled")
            .attr("readonly", null)
            .autocompleter("listen");
    },

    generalform_init: function(notrigger) {
        $("#id_role").change($.proxy(function(e) {
            var $this = $(e.target);
            var value = $this.val();

            if (value == "SimpleUsers" || value === "") {
                this.simpleuser_mode();
            } else {
                this.normal_mode();
            }
        }, this));
        if (notrigger !== undefined && notrigger) {
            return;
        }
        $("#id_role").trigger("change");
    },

    mailform_init: function() {
        $("#id_aliases").autocompleter({
            from_character: "@",
            choices: $.proxy(this.get_domain_list, this)
        }).dynamic_input();
        $("#id_email").autocompleter({
            from_character: "@",
            choices: $.proxy(this.get_domain_list, this)
        });
        if ($("#id_role").length) {
            $("#id_role").trigger("change");
        } else {
            this.simpleuser_mode();
        }
        $("#id_domains")
            .autocompleter({
                choices: $.proxy(this.get_domain_list, this)
            })
            .dynamic_input();
        activate_widget.call($("#id_quota_act"));
    },

    accountform_init: function() {
        this.generalform_init(true);
        this.mailform_init();
    },

    mailform_prefill: function() {
        var $role = $("#id_role");
        if (!$role.length || $role.val() === "" || $role.val() == "SimpleUsers") {
            $("#id_email").val($("#id_username").val());
        }
    },

    newaccount_cb: function() {
        this.accountform_init();
        $("#wizard").cwizard({
            formid: "newaccount_form",
            transition_callbacks: {
                1: this.mailform_prefill
            },
            success_callback: $.proxy(this.reload_listing, this)
        });
    },

    editaccount_cb: function() {
        this.accountform_init();
        $('.submit').on('click', $.proxy(function(e) {
            simple_ajax_form_post(e, {
                formid: "accountform",
                reload_on_success: false,
                success_cb: $.proxy(this.reload_listing, this)
            });
        }, this));
    },

    aliasform_cb: function() {
        $("#id_email").autocompleter({
            from_character: "@",
            choices: $.proxy(this.get_domain_list, this)
        });
        $("#id_recipients").dynamic_input();
        $(".submit").on('click', $.proxy(function(e) {
            simple_ajax_form_post(e, {
                formid: "aliasform",
                reload_on_success: false,
                success_cb: $.proxy(this.reload_listing, this)
            });
        }, this));
    }

};

Identities.prototype = $.extend({}, Admin.prototype, Identities.prototype);
