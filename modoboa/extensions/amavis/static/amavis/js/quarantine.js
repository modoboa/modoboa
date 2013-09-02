var Quarantine = function(options) {
    this.initialize(options);
};

Quarantine.prototype = {
    constructor: Quarantine,

    defaults: {
        deflocation: "listing",
        defcallback: "listing_cb",
        sortable_selector: '.sortable'
    },

    initialize: function(options) {
        this.options = $.extend({}, this.defaults, options);
        this.navobj = new History(this.options);

        this.register_navcallbacks();
        this.listen();
    },

    update_page: function(data) {
        if (data.menu != undefined) {
            $("#menubar").html(data.menu);
            $("#searchfield").searchbar({navobj: this.navobj});
        }
        if (data.navbar) {
            $("#bottom-bar-right").html(data.navbar);
        }
        if (data.listing != undefined) {
            $("#listing").html(data.listing);
            $("#listing").css({
                top: $("#menubar").outerHeight() + 60 + "px",
                bottom: $("#bottom-bar").outerHeight() + "px",
                overflow: "auto"
            });
        }
        var $sortables = $(this.options.sortable_selector);
        if ($sortables.length) {
            $(this.options.sortable_selector).sortable({
                onSortOrderChange: $.proxy(this.change_sort_order, this)
            });
            this.set_sort_order();
        }

    },

    set_sort_order: function() {
        var sort_order = this.navobj.getparam("order");
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
        this.navobj.setparam("order", sort_order).update();
    },

    listen: function() {
        $(document).on("dblclick", "tbody>tr", $.proxy(this.viewmail_loader, this));
        $(document).on("click", "a[name=selectmsgs]", $.proxy(this.selectmsgs, this));
        $(document).on("click", "a[name=release-multi]",
            $.proxy(this.release_selection, this));
        $(document).on("click", "a[name=delete-multi]",
            $.proxy(this.delete_selection, this));
        $(document).on("click", "a[name=viewrequests]",
            $.proxy(this.view_requests, this));
        $(document).on("click", "#bottom-bar a", $.proxy(this.load_page, this));

        $(document).on("click", "a[name=release]", $.proxy(this.release, this));
        $(document).on("click", "a[name=delete]", $.proxy(this.delete, this));
        $(document).on("click", "a[name=headers]", $.proxy(this.headers, this));
    },

    load_page: function(e) {
        e.preventDefault();
        var $link = $(e.target).parent();

        this.navobj.delparam("rcpt");
        this.navobj.parse_string($link.attr("href")).update();
    },

    view_requests: function(e) {
        e.preventDefault();
        this.navobj.setparam("viewrequests", "1").update();
    },

    viewmail_loader: function(e) {
        e.preventDefault();
        var $tr = $(e.target).parent();
        var $to = $tr.find("td[name=to]");

        this.navobj.baseurl($tr.attr("id"));
        if ($to.length) {
            this.navobj.setparam("rcpt", $to.html().trim());
        }
        this.navobj.update();
    },

    selectmsgs: function(e) {
        e.preventDefault();
        var type = $(e.target).attr("href");

        if (type == "") {
            $("#emails").htmltable("clear_selection");
            return;
        }
        $("td[name=type]").each(function() {
            var $this = $(this);
            if ($this.html().trim() == type) {
                $("#emails").htmltable("select_row", $this.parent());
            }
        });
    },

    _send_selection: function(e, name, message) {
        var $link = $(e.target);

        e.preventDefault();
        if (!this.htmltable.current_selection().length ||
            !confirm(message)) {
            return;
        }
        var selection = [];

        this.htmltable.current_selection().each(function() {
            var $tr = $(this);
            var $to = $tr.find("td[name=to]");

            if ($to.length) {
                selection.push($to.html().trim() + " " + $tr.attr("id"));
            } else {
                selection.push($tr.attr("id"));
            }
        });
        $.ajax({
            url: $link.attr("href"),
            data: "action=" + name + "&selection=" + selection.join(","),
            type: 'POST',
            dataType: 'json',
            success: $.proxy(this.action_cb, this)
        });
    },

    release_selection: function(e) {
        this._send_selection(e, "release", gettext("Release this selection?"));
    },

    delete_selection: function(e) {
        this._send_selection(e, "delete", gettext("Delete this selection?"));
    },

    _send_action: function(e, message) {
        var $link = get_target(e, "a");

        e.preventDefault();
        if (!confirm(message)) {
            return;
        }
        $.ajax({
            url: $link.attr("href"),
            dataType: 'json',
            success: $.proxy(this.action_cb, this)
        });
    },

    release: function(e) {
        this._send_action(e, gettext("Release this message?"));
    },

    delete: function(e) {
        this._send_action(e, gettext("Delete this message?"));
    },

    show_rawheaders: function($mailcontent) {
        $mailcontent.find("#rawheaders").removeClass("hidden");
        $mailcontent.find("#emailheaders").addClass("hidden");
    },

    headers: function(e) {
        e.preventDefault();

        var $link = get_target(e, "a");
        var $mailcontent = $("#mailcontent").contents();
        var $headers = $mailcontent.find("#emailheaders");
        var $rawheaders = $mailcontent.find("#rawheaders");

        if ($headers.hasClass("hidden")) {
            $link.html(gettext("View full headers"));
            $headers.removeClass("hidden");
            $rawheaders.addClass("hidden");
            return;
        }
        $link.html(gettext("Hide full headers"));
        if (!$rawheaders.length) {
            $.ajax({
                url: $link.attr("href"),
                success: $.proxy(function(data) {
                    $mailcontent.find("#table-container").append($(data));
                    this.show_rawheaders($mailcontent);
                }, this)
            });
            return;
        }
        this.show_rawheaders($mailcontent);
    },

    update_params: function(e) {
        var $link = $(e.target);
        e.preventDefault();
        this.navobj.updateparams($link.attr("href")).update();
    },

    register_navcallbacks: function() {
        this.navobj.register_callback("_listing",
            $.proxy(this.listing_cb, this));
        this.navobj.register_callback("viewmail",
            $.proxy(this.viewmail_cb, this));
    },

    listing_cb: function(data) {
        this.update_page(data);
        $("#emails").htmltable();
        this.htmltable = $("#emails").data("htmltable");
    },

    viewmail_cb: function(data) {
        this.update_page(data);
        $("#listing").css("overflow", "hidden");
    },

    action_cb: function(data) {
        if (data.status == "ok") {
            this.navobj.parse_string(data.url, true).update(true);
            $("body").notify("success", data.respmsg, 2000);
        } else {
            $("body").notify("error", data.respmsg);
        }
    }
};