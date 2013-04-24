var Admin = function(options) {
    this.initialize(options);
};

Admin.prototype = {
    constructor: Admin,

    defaults: {
        deflocation: "list/",
        squery: null
    },

    initialize: function(options) {
        this.options = $.extend({}, this.defaults, options);
        this.options.defcallback = $.proxy(this.list_cb, this);

        this.navobj = new History(this.options);

        $("#searchquery").focus(function() {
            $(this).attr("value", "");
        }).blur($.proxy(function(e) {
            var $this = $(e.target);
            if ($this.attr("value") == "") {
                if (this.options.squery && this.options.squery == "") {
                    $this.attr("value", this.options.squery);
                } else {
                    $this.attr("value", gettext("Search"));
                }
            }
        }, this));
        if (this.navobj.getparam("searchquery") != undefined) {
            $("#searchquery").attr("value", this.navobj.getparam("searchquery"));
        }

        this.listen();
    },

    list_cb: function(data) {
        $("#listing").html(data.table);
        $(".sortable").sortable({
            onSortOrderChange: $.proxy(this.change_sort_order, this)
        });
        this.set_sort_order();
        $("#bottom-bar-right").html(data.paginbar);
        $("#pagination_bar").find(".disabled a").click(function(e) {
            e.preventDefault();
        });
        if (data.page != this.navobj.getparam("page")) {
            this.navobj.setparam("page", data.page).update(false, false);
        }
    },

    listen: function() {
        $(document).on("click", "#bottom-bar-right a",
            $.proxy(this.getpage_loader, this));
        $("#searchform").submit($.proxy(this.do_search, this));
    },

    set_sort_order: function() {
        var sort_order = this.navobj.getparam("sort_order");
        var sort_dir;

        if (!sort_order) {
            return;
        }
        if (sort_order[0] == '-') {
            sort_dir = "desc";
            sort_order = sort_order.substr(1);
        } else {
            sort_dir = 'asc';
        }
        $("th[data-sort_order=" + sort_order + "]").sortable('select', sort_dir);
    },

    change_sort_order: function(sort_order, dir) {
        if (dir == "desc") {
            sort_order = "-" + sort_order;
        }
        this.navobj.setparam("sort_order", sort_order).update();
    },

    do_search: function(e) {
        e.preventDefault();
        var squery = $("#searchquery").attr("value");
        if (squery != "") {
            this.navobj.setparam("searchquery", squery);
        } else {
            this.navobj.delparam("searchquery");
        }
        this.navobj.update();
    },

    getpage_loader: function(e) {
        var $link = $(e.target).parent();
        e.preventDefault();
        this.navobj.updateparams($link.attr("href")).update();
    },

    importform_cb: function() {
        $(".submit").one('click', function(e) {
            e.preventDefault();
            if ($("#id_sourcefile").attr("value") == "") {
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
            this.reload_listing({respmsg: msg});
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
        if (data.respmsg) {
            $("body").notify("success", data.respmsg, 2000);
        }
    }
};

/*
 * Domains
 */
var Domains = function(options) {
    Admin.call(this, options);
};

Domains.prototype = {
    list_cb: function(data) {
        Admin.prototype.list_cb.call(this, data);
        var deloptions = (data.handle_mailboxes)
            ? {keepdir: gettext("Do not delete domain directory")}
            : {};
        var warnmsg = (data.auto_account_removal && data.auto_account_removal == "yes")
            ? gettext("This operation will remove ALL data associated to this domain.")
            : gettext("This operation will remove all data associated to this domain, excepting accounts.");

        $("a[name=deldomain]").confirm({
            question: gettext("Delete this domain?"),
            warning: warnmsg,
            checkboxes: deloptions,
            success_cb: $.proxy(this.reload_listing, this)
        });
    },

    domainform_cb: function() {
        $('input:text:visible:first').focus();
        $("#id_aliases").dynamic_input();
        $(".submit").one('click', $.proxy(function(e) {
            simple_ajax_form_post(e, {
                formid: "domform",
                error_cb: $.proxy(this.domainform_cb, this),
                reload_on_success: false,
                success_cb: $.proxy(this.reload_listing, this)
            });
        }, this));
        $("a[name=removeperm]").click(function(e) {
            var $tr = $(this).parent().parent();
            simple_ajax_request.apply(this, [e, {
                ok_cb: function(resp) {
                    $tr.remove();
                    if (!$("#domadmins").children("tr").length) {
                        $("#admins").html('<div class="alert alert-info">'
                            + gettext("No domain administrator defined") + "</div>");
                    }
                }
            }]);
        });
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

        if (this.navobj.getparam("idtfilter") != undefined) {
            var text = this.navobj.getparam("idtfilter");
            $("#searchform").parent().after(this.make_tag(text, "idt"));
        }
        if (this.navobj.getparam("grpfilter") != undefined) {
            var text = this.navobj.getparam("grpfilter");
            $("#searchform").parent().after(this.make_tag(text, "grp"));
        }
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

        if (data.handle_mailboxes) {
            deloptions = {keepdir: gettext("Do not delete mailbox directory")};
        }
        $("a.filter").click($.proxy(this.filter_by_tag, this));

        $("a[name=delaccount]").confirm({
            question: gettext("Delete this account?"),
            checkboxes: deloptions,
            success_cb: $.proxy(this.reload_listing, this)
        });
        $("a[name=deldlist]").confirm({
            question: gettext("Delete this list?"),
            success_cb: $.proxy(this.reload_listing, this)
        });
        $("a[name=delforward]").confirm({
            question: gettext("Delete this forward?"),
            success_cb: $.proxy(this.reload_listing, this)
        });
        $("a[name=delalias]").confirm({
            question: gettext("Delete this alias?"),
            success_cb: $.proxy(this.reload_listing, this)
        });
    },

    make_tag: function(text, type) {
        var $tag = $("<a />", {"name": type, "class" : "btn btn-mini", "html": text});
        var $i = $("<i />", {"class" : "icon-remove"}).prependTo($tag);

        $tag.click($.proxy(this.remove_tag, this));
        return $tag;
    },

    remove_tag: function(e) {
        var $tag = $(e.target);

        if ($tag.is("i")) {
            $tag = $tag.parent();
        }
        e.preventDefault();
        this.navobj.delparam($tag.attr("name") + "filter").update();
        $tag.remove();
    },

    filter_by_tag: function(e) {
        var $link = $(e.target);
        e.preventDefault();

        if (this.navobj.getparam("idtfilter") == undefined && $link.hasClass("idt")) {
            var text = $link.attr("name");
            this.navobj.setparam("idtfilter", text).update();
            $("#searchform").parent().after(this.make_tag(text, "idt"));
            return;
        }
        if (this.navobj.getparam("grpfilter") == undefined && $link.hasClass("grp")) {
            var text = $link.attr("name");
            this.navobj
                .setparam("idtfilter", "account")
                .setparam("grpfilter", text)
                .update();
            if ($("a[name=idt]").length == 0) {
                $("#searchform").parent().after(this.make_tag("account", "idt"));
            }
            $("#searchform").parent().after(this.make_tag(text, "grp"));
        }
    },

    simpleuser_mode: function() {
        $("#id_username").autocompleter({
            from_character: "@",
            choices: get_domains_list
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

    generalform_init: function() {
        $("#id_role").change($.proxy(function(e) {
            var $this = $(e.target);
            if ($this.attr("value") == "SimpleUsers") {
                this.simpleuser_mode();
            } else {
                this.normal_mode();
            }
        }, this));
    },

    mailform_init: function() {
        $("#id_aliases").autocompleter({
            from_character: "@",
            choices: get_domains_list
        }).dynamic_input();
        $("#id_email").autocompleter({
            from_character: "@",
            choices: get_domains_list
        });
        if ($("#id_role").length) {
            $("#id_role").trigger("change");
        } else {
            this.simpleuser_mode();
        }
        $("#id_domains")
            .autocompleter({
                choices: get_domains_list
            })
            .dynamic_input();
        activate_widget.call($("#id_quota_act"));
    },

    accountform_init: function() {
        this.generalform_init();
        this.mailform_init();
    },

    mailform_prefill: function() {
        if (!$("#id_role").length || $("#id_role").attr("value") == "SimpleUsers") {
            $("#id_email").attr("value", $("#id_username").attr("value"));
        }
    },

    newaccount_cb: function() {
        this.accountform_init();
        $("#wizard").cwizard({
            formid: "newaccount_form",
            transition_callbacks: {
                1: this.mailform_prefill
            },
            error_callbacks: {
                1: this.generalform_init,
                2: this.mailform_init
            },
            success_callback: $.proxy(this.reload_listing, this)
        });
    },

    editaccount_cb: function() {
        this.accountform_init();
        $('.submit').one('click', $.proxy(function(e) {
            simple_ajax_form_post(e, {
                formid: "accountform",
                error_cb: $.proxy(this.editaccount_cb, this),
                reload_on_success: false,
                success_cb: $.proxy(this.reload_listing, this)
            });
        }, this));
    },

    aliasform_cb: function() {
        $("#id_email").autocompleter({
            from_character: "@",
            choices: get_domains_list
        });
        $("#id_recipients").dynamic_input();
        $("#id_int_recipient").autocompleter({
            choices: get_mboxes_list
        });
        $(".submit").one('click', $.proxy(function(e) {
            simple_ajax_form_post(e, {
                formid: "aliasform",
                error_cb: $.proxy(this.aliasform_cb, this),
                reload_on_success: false,
                success_cb: $.proxy(this.reload_listing, this)
            });
        }, this));
    }

};

Identities.prototype = $.extend({}, Admin.prototype, Identities.prototype);
