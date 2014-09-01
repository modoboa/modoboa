/*
 * The javascript code that brings the webmail to life!
 */
var Webmail = function(options) {
    this.initialize(options);
};

Webmail.prototype = {
    constructor: Webmail,

    defaults: {
        poller_interval: 300, /* in seconds */
        poller_url: "",
        move_url: "",
        submboxes_url: "",
        delattachment_url: "",
        ro_mboxes: ["INBOX"],
        trash: "",
        hdelimiter: '.',
        mboxes_col_width: 200
    },



    initialize: function(options) {
        this.options = $.extend({}, this.defaults, options);
        this.rtimer = null;
        this.editorid = "id_body";

        this.navobject = new History({
            deflocation: "?action=listmailbox",
            defcallback: $.proxy(this.listmailbox_callback, this)
        });
        this.poller = new Poller(this.options.poller_url, {
            interval: this.options.poller_interval * 1000,
            success_cb: $.proxy(this.poller_cb, this),
            args: this.get_visible_mailboxes
        });
        this.record_unseen_messages();


        $("#mboxactions").css({
            bottom: $("#bottom-bar").outerHeight(true) + "px"
        });

        /* Responsive -> on resizing folders (leftcol) */
        $("#folders").resizable({
            start: function(event, ui) {
                $('#listing iframe').css('pointer-events','none');
            },
            handles: "e",
            minWidth: parseInt($("#folders").css("width").replace("px", "")),
            maxWidth: 400,
            stop: function(event, ui) {
                $('#listing iframe').css('pointer-events','auto');
            }
        });

        $("#folders").resizable({
            resize: function(event, ui) {
                if ($(window).width() > 1198) {
                    var width = ui.size.width;
                    /*$("#rightcol").css({
                        marginLeft: width + 'px'
                    });*/
                    $("#folders").css({
                        width : width + 'px'
                    });
                    /*$("#rightcol").css({
                        paddingRight: width - 110 + 'px'
                    });
                    if ($(window).width() < 1800) {
                        $("#rightcol").css({
                            paddingRight: width - 110 + 'px'
                        });
                    }*/
                }
            }
        });
        /* end Responsive */

        this.resize();

        this.init_droppables();
        this.register_navcallbacks();
        this.listen();
    },

    register_navcallbacks: function() {
        this.navobject.register_callback("listmailbox", $.proxy(this.listmailbox_callback, this));
        this.navobject.register_callback("compose", $.proxy(this.compose_callback, this));
        this.navobject.register_callback("viewmail", $.proxy(this.viewmail_callback, this));

        this.navobject.register_callback("reply", $.proxy(this.compose_callback, this));
        this.navobject.register_callback("replyall", $.proxy(this.compose_callback, this));
        this.navobject.register_callback("forward", $.proxy(this.compose_callback, this));
    },

    listen: function() {
        $(window).resize($.proxy(this.resize, this));

        $(document).on("click", "a[name=compose]", $.proxy(this.compose_loader, this));
        $(document).on("click", "a[name=totrash]", $.proxy(this.delete_messages, this));
        $(document).on("click", "a[name*=mark-]", $.proxy(this.send_mark_request, this));
        $(document).on("click", "a[name=compress]", $.proxy(this.compress, this));
        $(document).on("click", "a[name=empty]", $.proxy(this.empty, this));
        $(document).on("click", "#bottom-bar a", $.proxy(this.getpage_loader, this));

        $(document).on("click", "a[name=loadfolder]", $.proxy(this.listmailbox_loader, this));
        $(document).on("click", "a[name=selectfolder]", this.select_parent_mailbox);
        $(document).on("click", "div[class*=clickbox]", $.proxy(this.mbox_state_callback, this));
        $(document).on("click", "a[name=newmbox]", $.proxy(this.new_mailbox, this));
        $(document).on("click", "a[name=editmbox]", $.proxy(this.edit_mbox, this));
        $(document).on("click", "a[name=removembox]", $.proxy(this.remove_mbox, this));

        $(document).on("click", "td[class*=openable]", $.proxy(this.viewmail_loader, this));

        $(document).on("click", "a[name=reply]", $.proxy(this.reply_loader, this));
        $(document).on("click", "a[name=replyall]", $.proxy(this.reply_loader, this));
        $(document).on("click", "a[name=forward]", $.proxy(this.reply_loader, this));
        $(document).on("click", "a[name=delete]", $.proxy(this.delete_message, this));
        $(document).on("click", "a[name=activate_links]", $.proxy(function(e) { this.display_mode(e, "1"); }, this));
        $(document).on("click", "a[name=disable_links]", $.proxy(function(e) { this.display_mode(e, "0"); }, this));

        $(document).on("click", "a[name=sendmail]", $.proxy(this.sendmail, this));

        $(document).on("click", "#attachments", $.proxy(function(e) {
            modalbox(e, undefined, $("#attachments").attr("name"),
                $.proxy(this.attachments_init, this));
        }, this));
    },

    record_unseen_messages: function() {
        var unseen_counters = {};

        $("#folders").find("a.unseen").each(function() {
            var $this = $(this);
            unseen_counters[$this.attr("href")] = parseInt($this.attr("data-toggle"));
        });
        this.unseen_counters = unseen_counters;
    },

    /**
     * Global resize event callback.
     */
    resize: function() {
        /*$("#mboxes_container").height(
            $("#folders").height() - $("#mboxactions").height());*/
        var $window = $(window);
        var current_action = this.navobject.getparam("action");

        if ($window.width() > 1198) {
            $("#folders").css({
                /*bottom: $("#bottom-bar").outerHeight(true) + 10,*/
                width: this.options.mboxes_col_width + 'px'
            });
        }
        if (current_action == "listmailbox") {
            this.resize_listing("auto");
        } else if (current_action == "viewmail") {
            this.resize_listing("hidden");
        } else if (current_action == "compose") {
            this.resize_compose_body();
        }
    },

    /**
     * Resize the "listing" div.
     */
    resize_listing: function(overflow) {
        $("#listing").css("overflow", overflow);
        $("#listing").height(
            $("#bottom-bar").offset().top - 
            ($("#menubar").offset().top + $("#menubar").outerHeight())
        );
    },

    /**
     * Resize the textarea used to write plain/text messages.
     */
    resize_compose_body: function() {
        var $container = $("#body_container");

        if ($container.length) {
            var top = $container.offset().top;
            var bottom = $("#bottom-bar").offset().top;

            $("#body_container").innerHeight(bottom - top - 10);
        }
    },

    /*
     * Callback of the 'compose' action.
     *
     * It is also shared with other similar actions : reply, forward.
     */
    resize_editor: function() {
        CKEDITOR.instances[this.editorid].resize("100%",
            $("#body_container").outerHeight(true));
    },

    /*
     * Simple helper to retrieve the currently selected mailbox.
     */
    get_current_mailbox: function() {
        return this.navobject.getparam("mbox", "INBOX");
    },

    /*
     * Keep track of interesting navigation parameters in order to
     * restore them later.
     */
    store_nav_params: function() {
        var params = new Array("page", "order", "pattern", "criteria");

        this.navparams = {};
        for (var idx in params) {
            this.navparams[params[idx]] = this.navobject.getparam(params[idx]);
        }
    },

    /*
     * Restore navigation parameters previously stored via
     * store_nav_params.
     */
    restore_nav_params: function() {
        if (this.navparams === undefined) {
            return;
        }
        var navobject = this.navobject;
        $.each(this.navparams, function(key, value) {
            if (value === undefined) {
                return;
            }
            navobject.setparam(key, value);
        });
    },

    go_back_to_listing: function() {
        var curmb = this.get_current_mailbox();
        this.navobject.reset()
            .setparams({action: "listmailbox", mbox: curmb});
        this.restore_nav_params();
        this.navobject.update(true);
    },

    /*
     * Enable or disable edit and remove actions for the currently
     * selected mailbox.
     */
    enable_mb_actions: function(state) {
        if (state === undefined) {
            state = true;
        }
        if (state) {
            $("a[name=editmbox], a[name=removembox]").removeClass("disabled");
        } else {
            $("a[name=editmbox], a[name=removembox]").addClass("disabled");
        }
    },

    page_update: function(response) {
        var curmb = this.get_current_mailbox();

        if (!$('li[name="' + curmb + '"]').hasClass("active")) {
            this.load_and_select_mailbox(curmb);
        }
        this.enable_mb_actions();
        for (var idx in this.options.ro_mboxes) {
            if (curmb == this.options.ro_mboxes[idx]) {
                this.enable_mb_actions(false);
                break;
            }
        }
        if (response.menu !== undefined) {
            $("#menubar").html(response.menu);
            $("#searchfield").searchbar({navobj: this.navobject});
        }
        if (response.navbar) {
            $("#bottom-bar-right").html(response.navbar);
            $("#pagination-responsive").html(response.navbar);
        }
        $("#listing").html(response.listing);
    },

    /*
     *  Set the *unseen messages* counter for a particular mailbox in
     *  the list. If the mailbox is currently selected, we update the
     *  listing.
     */
    set_unseen_messages: function(mailbox, value) {
        if (this.poller.running_request) {
            return;
        }
        if (this.unseen_counters[mailbox] !== undefined &&
            value == this.unseen_counters[mailbox]) {
            return;
        }

        if (this.navobject.params.action == "listmailbox") {
            var curmb = this.get_current_mailbox();
            if (curmb == mailbox) {
                this.navobject.update(true);
            }
        }

        var $link = $('a[href="' + mailbox + '"]');
        var parts = mailbox.split(this.options.hdelimiter);
        var dname = " " + parts[parts.length - 1];
        var $i = $link.children("i:visible");

        this.unseen_counters[mailbox] = value;
        if (value) {
            $link.html(dname + " (" + value + ")");
            $link.addClass("unseen");
        } else {
            $link.html(dname);
            $link.removeClass("unseen");
        }
        $link.prepend($i);
    },

    /*
     * Increment or decrement the *unseen messages* counter of the
     * given mailbox.
     */
    change_unseen_messages: function(mailbox, offset) {
        if (this.unseen_counters[mailbox] === undefined) {
            this.unseen_counters[mailbox] = 0;
        }
        this.set_unseen_messages(mailbox, this.unseen_counters[mailbox] + offset);
    },

    /*
     * Returns a list containing the currently visible mailboxes (in
     * the left tree).
     */
    get_visible_mailboxes: function() {
        var res = [];

        $("#folders").find("ul:visible").children("li.droppable").each(function() {
            res.push(encodeURIComponent($(this).attr("name")));
        });
        return "mboxes=" + res.join(",");
    },

    /*
     * Poller callback.
     */
    poller_cb: function(data) {
        for (var mb in data) {
            this.set_unseen_messages(mb, parseInt(data[mb]));
        }
    },

    /*
     * Inject a new *clickbox* somewhere in the tree
     */
    inject_clickbox: function($container) {
        $container.prepend($("<div />", {'class' : 'clickbox collapsed'}));
    },

    /*
     * Injects a single mailbox somewhere in the tree
     */
    inject_mailbox: function($parent, mailbox, linkname, unseen) {
        var $li = $("<li />", {
            name: mailbox,
            'class': "droppable"
        });
        var $link = $("<a />", {
            name: linkname,
            'class': "block",
            href: mailbox
        });
        var parts = mailbox.split(this.options.hdelimiter);
        var linkcontent = "<span class='glyphicon glyphicon-folder-close'></span> ";
        var displayname = linkcontent + parts[parts.length - 1];

        $li.append($link);
        $parent.append($li);

        if (unseen !== undefined) {
            $link.addClass("unseen");
            $link.html(displayname + " (" + unseen + ")");
            this.unseen_counters[$link.attr("href")] = unseen;
        } else {
            $link.html(displayname);
        }
        return $li;
    },

    /*
     * Inject new mailboxes under a given parent in the tree.
     */
    inject_mailboxes: function($parent, mboxes) {
        var $ul = $("<ul />", {
            name: $parent.attr("name"),
            'class': "hidden nav nav-sidebar"
        });
        var $plink = $parent.children("a");

        $parent.append($ul);
        if (!$parent.children("div").length) {
            this.inject_clickbox($parent);
        }
        for (var i = 0; i < mboxes.length; i++) {
            if ($parent.find('li[name="' + mboxes[i].name + '"]').length) {
                continue;
            }
            this.inject_mailbox($ul, mboxes[i].name, $plink.attr("name"), mboxes[i].unseen);
            if (mboxes[i].sub !== undefined) {
                this.inject_clickbox($('li[name="' + mboxes[i].name + '"]'));
            }
        }
        this.init_droppables($ul.find(".droppable"));
        this.toggle_mbox_state($parent.children("div"), $ul);
    },

    /*
     * Download sub-mailboxes from the server
     */
    get_mailboxes: function(parent, async) {
        if (async === undefined) {
            async = true;
        }
        $.ajax({
            url: this.options.submboxes_url,
            dataType: 'json',
            async: async,
            data: "topmailbox=" + parent.parents("li").attr("name")
        }).done($.proxy(function(data) {
            this.inject_mailboxes(parent, data);
        }, this));
    },

    /*
     * Open/Close a mailbox with children
     */
    toggle_mbox_state: function($div, $ul) {
        if ($ul.hasClass("hidden")) {
            $div.removeClass("collapsed").addClass("expanded");
            $ul.removeClass("hidden").addClass("visible");
        } else {
            $div.removeClass("expanded").addClass("collapsed");
            $ul.removeClass("visible").addClass("hidden");
        }
    },

    mbox_state_callback: function(e) {
        e.preventDefault();
        var $div = $(e.target);
        var $parent = $div.parent();
        var $ul = $parent.find('ul[name="' + $parent.attr("name") + '"]');

        if (!$ul.length) {
            this.get_mailboxes($parent);
            return;
        }
        this.toggle_mbox_state($div, $ul);
    },

    /*
     * Unselect every selected mailbox
     */
    reset_mb_selection: function() {
        $("a[name=loadfolder]").parent().removeClass("active").addClass("droppable");
    },

    /*
     * Select a particular mailbox (one already present in the DOM)
     */
    select_mailbox: function(obj) {
        var $obj = (typeof obj != "string") ? $(obj) : $('a[href="' + obj + '"]');

        this.reset_mb_selection();
        $obj.parents("ul").addClass("visible");
        $obj.parent().removeClass("droppable");
        $obj.parent().addClass("active");
    },

    /*
     * Tries to select a particular sub-mailbox and loads it from the
     * server if it's not present in the DOM. (nb: all parents needed
     * to access this mailbox are also loaded)
     */
    load_and_select_mailbox: function(mailbox) {
        if (mailbox.indexOf(this.options.hdelimiter) == -1) {
            this.select_mailbox(mailbox);
            return;
        }
        this.reset_mb_selection();

        var parts = mailbox.split(this.options.hdelimiter);
        var curmb = parts[0], lastmb = "";

        for (var i = 1; i < parts.length; i++) {
            lastmb = curmb;
            curmb += this.options.hdelimiter + parts[i];

            var $link = $('a[href="' + curmb + '"]');
            var $container = $('li[name="' + lastmb + '"]');

            if ($link.length) {
                if ($container.children("div").hasClass("collapsed")) {
                    this.toggle_mbox_state($container.children("div"), $container.children("ul"));
                }
                continue;
            }

            this.get_mailboxes($container, false);
            $container.children("div").addClass("expanded");
            $container.children("ul").addClass("visible");
        }
        $('li[name="' + mailbox + '"]').addClass("active");
    },

    select_parent_mailbox: function(e) {
        e.preventDefault();
        var $this = $(this);
        var $parent = $this.parent();
        var is_selected = $parent.hasClass("active");

        $("a[name=selectfolder]").parent().removeClass("active");
        if (!is_selected) {
            $parent.addClass("active");
        }
    },

    new_mailbox: function(e) {
        this.poller.pause();
    },

    /*
     * Edit the currently selected mailbox. Opens a modal box that
     * permits to change mailbox's name and more.
     */
    edit_mbox: function(e) {
        this.poller.pause();

        var $link = get_target(e, "a");
        if ($link.hasClass("disabled")) {
            e.preventDefault();
            return;
        }
        var $selected = $("#folders li.active").children("a");

        modalbox(e, undefined, $link.attr("href") + "?name=" + $selected.attr("href"),
            $.proxy(this.mboxform_cb, this), $.proxy(this.mboxform_close, this));
    },

    /*
     * Remove the currently selected mailbox.
     */
    remove_mbox: function(e) {
        var $link = get_target(e, "a");
        e.preventDefault();
        if ($link.hasClass("disabled")) return;
        if (!confirm(gettext("Remove the selected mailbox?"))) {
            return;
        }

        this.poller.pause();
        var $selected = $("#folders li.active").children("a");

        $.ajax({
            url: $link.attr("href") + "?name=" + $selected.attr("href"),
            dataType: 'json'
        }).done($.proxy(function(data) {
            this.remove_mbox_from_tree(this.navobject.getparam("mbox"));
            this.poller.resume();
            $("body").notify("success", gettext("Mailbox removed"), 2000);
        }, this));
    },

    /*
     * Remove a mailbox from the tree.
     *
     * It is a client-side action, no request is sent to the server.
     */
    remove_mbox_from_tree: function(mailbox) {
        var $container = (typeof mailbox === "string") ? $('li[name="' + mailbox + '"]') : mailbox;
        var $parent = $container.parent("ul");

        if ($parent.children("li").length == 1) {
            $parent.siblings("div").remove();
            $parent.remove();
        } else {
            $container.remove();
        }
        if (this.navobject.getparam("action") == "listmailbox") {
            this.select_mailbox($("a[href=INBOX]"));
            this.navobject.setparam("mbox", "INBOX").update();
        }
    },

    /*
     * Add a new mailbox into the tree. We check if the parent is
     * present before adding. If it's not present, we do nothing.
     */
    add_mailbox_to_tree: function(parent, mailbox) {
        var $parent;

        if (parent) {
            $parent = $("#folders").find('li[name="' + parent + '"]');
            if (!$parent.length) {
                return;
            }
            if (!$parent.children("div").length) {
                this.inject_clickbox($parent);
            }
            var $ul = $parent.children("ul");
            if (!$ul.length) {
                return;
            }
            $parent = $ul;
            mailbox = $parent.attr("name") + this.options.hdelimiter + mailbox;
        } else {
            $parent = $("#mboxes_container").children("ul");
        }
        var $li = this.inject_mailbox($parent, mailbox, "loadfolder");
        this.init_droppables($li);
    },

    /*
     * Rename a mailbox (client-side)
     * If needed, the mailbox will be moved to its new location.
     */
    rename_mailbox: function(oldname, newname, oldparent, newparent) {
        var oldpattern = (oldparent) ? oldparent + this.options.hdelimiter + oldname : oldname;
        var newpattern = (newparent) ? newparent + this.options.hdelimiter + newname : newname;
        var $link = $("#folders").find('a[href="' + oldpattern + '"]');

        if (oldname != newname) {
            var $i = $link.children("i");

            $link.html(newname);
            $link.parent("li").attr("name", newpattern);
            $link.prepend($i);
            $link.attr("href", newpattern);
            this.navobject.setparam("mbox", newpattern).update(false, true);
        }
        if (oldparent != newparent) {
            this.remove_mbox_from_tree($link.parent("li"));
            this.add_mailbox_to_tree(newparent, newname);
            if (this.navobject.getparam("action") == "listmailbox") {
                this.navobject.setparam("mbox", newpattern).update();
            } else {
                this.select_mailbox("INBOX");
            }
        }
    },

    send_mark_request: function(e) {

        e.preventDefault();
        if (!this.htmltable.current_selection().length) {
            return;
        }
        var $link = $(e.target);
        var selection = [];

        this.htmltable.current_selection().each(function() {
            selection.push($(this).attr("id"));
        });
        $.ajax({
            url: $link.attr("href"),
            data: "ids=" + selection.join(","),
            dataType: 'json'
        }).done($.proxy(this.mark_callback, this));
    },

    send_mb_action: function(url, cb) {
        $.ajax({
            url: url,
            dataType: 'json'
        }).done($.proxy(function(data) {
            if (cb !== undefined) {
                cb.apply(this, [data]);
            }
        }, this));
    },

    empty: function(e) {
        e.preventDefault();
        var $link = $(e.target);

        this.send_mb_action($link.attr("href"), function(data) {
            this.page_update(data);
            this.set_unseen_messages(data.mailbox, 0);
        });
    },

    compress: function(e) {
        e.preventDefault();
        var $link = $(e.target);
        this.send_mb_action($link.attr("href"));
    },

    delete_message: function(e) {
        var $link = get_target(e, "a");
        e.preventDefault();
        $.ajax({
            url: $link.attr("href"),
            dataType: 'json'
        }).done($.proxy(this.delete_callback, this));
    },

    delete_messages: function(e) {
        e.preventDefault();
        var $link = get_target(e, "a");
        if ($link.hasClass("disabled")) {
            return;
        }
        var msgs = this.htmltable.current_selection();
        var selection = [];
        var unseen_cnt = 0;

        if (!msgs.length) {
            return;
        }
        $link.addClass("disabled");
        $.each(msgs, function(idx, item) {
            var $tr = $(item);
            selection.push($tr.attr("id"));
            if ($tr.hasClass("unseen")) {
                unseen_cnt++;
            }
        });
        this.change_unseen_messages(this.get_current_mailbox(), -unseen_cnt);
        this.change_unseen_messages(this.options.trash, unseen_cnt);
        $.ajax({
            url: $link.attr("href"),
            data: {mbox: this.get_current_mailbox(), selection: selection}
        }).done($.proxy(this.delete_callback, this));
    },

    display_mode: function(e, value) {
        e.preventDefault();
        this.navobject.setparam("links", value).update();
    },

    /*
     * Action loaders
     */

    /*
     * Onclick callback used to load the content of a particular
     * mailbox. (activated when clicking on a mailbox's name)
     */
    _listmailbox_loader: function(event, obj) {
        if (event) {
            event.preventDefault();
        }
        if (obj === undefined) {
            obj = $(event.target);
        }
        this.navobject.reset().setparams({
           action: "listmailbox",
           mbox: obj.attr("href")
        }).update();
    },

    listmailbox_loader: function(event) {
        var $target = get_target(event, "a");

        if ($target.parent().hasClass("disabled")) {
            event.preventDefault();
            return;
        }
        this.select_mailbox(event.target);
        this._listmailbox_loader(event, $target);
    },

    /*
     * Special loader used for pagination links as we only need to
     * update the 'page' parameter.
     */
    getpage_loader: function(e) {
        var $link = $(e.target).parent();
        e.preventDefault();
        this.navobject.updateparams($link.attr("href")).update();
    },

    /*
     * Loader of the 'compose' action (called when the associated button
     * is clicked)
     */
    compose_loader: function(e) {
        var $link = get_target(e, 'a');

        e.preventDefault();
        this.navobject.reset().setparam("action", $link.attr("href")).update();
    },

    reply_loader: function(e) {
        var $link = get_target(e, "a");
        e.preventDefault();
        this.navobject.reset().updateparams($link.attr("href")).update();
    },

    sendmail: function(e) {
        var $link = $(e.target);
        var $form = $("#composemail");

        e.preventDefault();
        $link.attr("disabled", "disabled");
        if (this.editormode == "html") {
            CKEDITOR.instances[this.editorid].updateElement();
        }
        var args = $form.serialize();

        $.ajax({
            url: $form.attr("action"),
            data: args,
            dataType: 'json',
            type: 'POST',
            global: false
        }).done($.proxy(function(data) {
            this._listmailbox_loader(null, $("#folders").find("li[class*=active]").children("a"));
            $("body").notify("success", gettext("Message sent"), 2000);
        }, this)).fail($.proxy(function(jqxhr) {
            var data = $.parseJSON(jqxhr.responseText);
            if (data != undefined) {
                this.compose_callback(data);
            }
            $("a[name=sendmail]").attr("disabled", null);
        }, this));
    },

    /*
     * Loader of the 'viewmail' action
     */
    viewmail_loader: function(e) {
        var $tr = $(e.target).parent();
        var curmb = this.get_current_mailbox();

        e.preventDefault();
        if ($tr.hasClass("disabled")) {
            return;
        }
        $tr.addClass("disabled");
        if ($tr.hasClass("unseen")) {
            var mb = this.get_current_mailbox();
            this.change_unseen_messages(mb, -1);
        }
        this.navobject.reset().setparams({
            action: "viewmail",
            mbox: curmb,
            mailid: $tr.attr("id")
        }).update();
    },

    /*
     * Ajax navigation callbacks
     */

    /*
     * 'listmailbox' callback
     */
    listmailbox_callback: function(resp) {
        this.store_nav_params();
        this.page_update(resp);
        $("#emails").htmltable();
        this.htmltable = $("#emails").data("htmltable");
        this.init_draggables();
        this.resize_listing("auto");
    },

   

    add_field: function(e, name) {
        e.preventDefault();
        $("label[for=id_" + name + "]").parent().show();
        $(e.target).hide();
        this.resize_compose_body();
        if (this.editormode == "html") {
            this.resize_editor();
        }
    },

    /**
     * Compose form loading and initialization.
     */
    compose_callback: function(resp) {
        this.page_update(resp);
        $("#add_cc").click($.proxy(function(e) { this.add_field(e, "cc"); }, this));
        $("#add_cci").click($.proxy(function(e) { this.add_field(e, "cci"); }, this));
        this.editormode = resp.editor;
        if (resp.editor == "html") {
            var instance = CKEDITOR.instances[this.editorid];

            $(window).resize($.proxy(this.resize_editor, this));
            if (instance) {
                CKEDITOR.remove(instance);
            }
            CKEDITOR.replace(this.editorid, {
                customConfig: get_static_url("js/editor_config.js")
            });
            CKEDITOR.on("instanceReady", $.proxy(function(evt) {
                this.resize_editor();
            }, this));
        }
        if (resp.id !== undefined) {
            this.navobject.setparam("id", resp.id).update(false, true);
        }
        this.resize_compose_body();
    },

    /*
     * Callback of the 'viewmail' action
     */
    viewmail_callback: function(resp) {
        this.page_update(resp);
        this.resize_listing("hidden");
        $("a[name=back]").click($.proxy(function(e) {
            e.preventDefault();
            this.go_back_to_listing();
        }, this));
    },

    mark_callback: function(data) {
        if (data.action == "read") {
            this.htmltable.current_selection().removeClass("unseen");
        } else {
            this.htmltable.current_selection().addClass("unseen");
        }
        if (data.unseen !== undefined && data.mbox) {
            this.set_unseen_messages(data.mbox, data.unseen);
        }
    },

    delete_callback: function(data) {
        this.go_back_to_listing();
        if (this.get_current_mailbox() != this.options.trash) {
            $("a[name=totrash]").removeClass("disabled");
        }
        $("body").notify("success", data, 2000);
    },

    /*
     * Mailbox form initialization
     */
    mboxform_cb: function() {
        $("#mboxform").find("input").keypress(function(e) {
            if (e.which == 13) e.preventDefault();
        });
        $(".submit").on('click', $.proxy(function(e) {
            var $link = $("#folders2 li.active").children("a");

            simple_ajax_form_post(e, {
                reload_on_success: false,
                formid: "mboxform",
                extradata: ($link.length) ? "parent_folder=" + $link.attr("href") : "",
                success_cb: $.proxy(this.mboxform_success, this)
            });
        }, this));
    },

    mboxform_success: function(data) {
        $("body").notify('success', data.respmsg, 2000);
        if (data.oldmb === undefined) {
            this.add_mailbox_to_tree(data.parent, data.newmb);
        } else if (data.newmb) {
            this.rename_mailbox(data.oldmb, data.newmb, data.oldparent, data.newparent);
        }
        this.poller.resume();
    },

    /*
     * Just a simple 'onclose' callback to check if the poller has
     * been resumed (useful when the user has cancelled the action)
     */
    mboxform_close: function() {
        if (this.poller.paused) {
            this.poller.resume();
        }
    },

    /*
     * Attachments form
     */
    attachments_init: function() {
        $("#submit").click(function(e) {
            e.preventDefault();
            if ($("#id_attachment").val() == "") {
                return;
            }
            $("#upload_status").css("display", "block");
            $("#submit").attr("disabled", "disabled");
            $("#uploadfile").submit();
        });
        $("a[name=delattachment]").click(this.del_attachment);
        $(".modal").one("hide", this.close_attachments);
    },

    _reset_upload_form: function() {
        $("#upload_status").css("display", "none");
        $("#submit").attr("disabled", null);
    },

    upload_success: function(fname, tmpname) {
        this._reset_upload_form();
        var $delbtn = $("<a />", {
            name: "delattachment",
            href: this.options.delattachment_url + "?name=" + tmpname,
            html: "<i class='glyphicon glyphicon-remove'></i>"
        });
        var $label = $("<label />", {html: fname});
        var $div = $("<div />", {'class': "row"}).append($delbtn, $label);

        $delbtn.click(this.del_attachment);
        $("#id_attachment").val("");
        $("#attachment_list").append($div);
    },

    upload_error: function(msg) {
        this._reset_upload_form();
        $(".modal-header").notify('error', msg);
    },

    del_attachment: function(e) {
        e.preventDefault();
        var $this = $(this);

        $.ajax({
            url: $this.attr("href")
        }).done(function() {
            $this.parent().remove();
        });
    },

    close_attachments: function() {
        var nfiles = 0;
        var shortlist = "";
        var html;

        $("a[name=delattachment]").each(function() {
            var $this = $(this);
            var $label = $this.next("label");

            nfiles++;
            if (nfiles <= 2) {
                if (shortlist != "") {
                    shortlist += ", ";
                } else {
                    shortlist = "(";
                }
                shortlist += $label.html();
                return;
            }
            if (nfiles == 3) {
                shortlist += ", ...";
            }
        });
        if (shortlist != "") {
            shortlist += ")";
        }
        html = interpolate(ngettext("%s file", "%s files", nfiles), [nfiles]);
        html += " <span class='shortlist'>" + shortlist + "</span>";
        $("#list").html(html);
    },

    /*
     * Drag & Drop feature to move message(s) between mailboxes
     */
    init_draggables: function() {
        var plug = this;

        $("td[name=drag]").draggable({
            opacity: 0.8,
            helper: function(e) {
                var $this = $(this);
                var $tr = $this.parent();

                if (!plug.htmltable.is_selected($tr)) {
                    var $input = $tr.find('#selection');
                    plug.htmltable.select_row($tr);
                    $input.prop('checked', true);
                }

                var nmsgs = plug.htmltable.current_selection().length;

                var $dragbox = $("<div />", {
                    id: "draggeditems",
                    'class': "well dragbox"
                })
                .appendTo($(document.body))
                .offset({
                    top: $this.offset().top,
                    left: $this.offset().left
                });
                $dragbox.html(interpolate(ngettext("Moving %s message",
                    "Moving %s messages", nmsgs), [nmsgs]));
                return $dragbox;
            }
        });
    },

    init_droppables: function(set) {
        var plug = this;
        var $set = (set === undefined) ? $(".droppable") : set;

        $set.droppable({
            greedy: true,
            hoverClass: "active",

            drop: function(e, ui) {
                var $this = $(this);
                var selection = new Array();
                var unseen_cnt = 0;
                var from = plug.get_current_mailbox();
                var to = gethref($this.find("a"));

                plug.htmltable.current_selection().each(function() {
                    var $this = $(this);
                    selection.push($this.attr("id"));
                    if ($this.hasClass("unseen")) {
                        unseen_cnt++;
                    }
                });
                $.ajax({
                    url: plug.options.move_url,
                    data: "msgset=" + selection.join() + "&to=" + to,
                    dataType: 'json'
                }).done(function(data) {
                    if (unseen_cnt) {
                        plug.change_unseen_messages(from, -unseen_cnt);
                        plug.change_unseen_messages(to, unseen_cnt);
                    }
                    plug.listmailbox_callback(data);
                });
            }
        });
    }
};
