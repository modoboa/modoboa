/**
 * Return an instance of Quarantine.
 *
 * @constructor
 * @param {Object} options - instance options
 */
var Quarantine = function(options) {
    Listing.call(this, options);
};

Quarantine.prototype = {
    constructor: Quarantine,

    defaults: {
        deflocation: "listing",
        main_table_id: "emails",
        scroll_container: "#listing",
        navigation_params: ["sort_order", "pattern", "criteria", "msgtype"],
        eor_message: gettext("No more message to show")
    },

    initialize: function(options) {
        this.options = $.extend({}, this.defaults, options);
        this.options.defcallback = $.proxy(this.listing_cb, this);
        Listing.prototype.initialize.call(this, this.options);
        this.register_navcallbacks();
        this.listen();
        this.set_msgtype();

        $(document).on('click', '#selectall', this.toggle_selection);
        this.initialize_searchfield();
    },

    /**
     * Search field initialization.
     */
    initialize_searchfield: function() {
        $("#searchfield").searchbar({
            navobj: this.navobj,
            pattern_changed: function(navobj) {
                navobj.setparam("reset_page", "true");
            }
        });
    },

    /**
     * Activate the button corresponding to the current message type
     * filter. If no message type is found, the 'All' button is
     * selected.
     */
    set_msgtype: function() {
        var msgtype = this.navobj.getparam('msgtype');

        $("input[name*=msgtype]").attr("checked", false)
            .parent().removeClass('active');
        
        if (msgtype !== undefined) {
            $("input[name=msgtype_" + msgtype + "]").attr("checked", true)
                .parent().addClass('active');
        } else {
            $("button[name=msgtype_all]").attr("checked", true)
                .parent().addClass('active');
        }
    },

    /**
     * Update the main page content.
     *
     * @this Quarantine
     * @param {Object} data - new content
     */
    update_page: function(data) {
        if (data.menu !== undefined) {
            $("#menubar").html(data.menu);
            this.initialize_searchfield();
        }

        if (data.listing !== undefined) {
            $("#listing").html(data.listing);
        }
        if (this.navobj.getbaseurl() == "listing") {
            this.update_listing(data);
            $(this.options.scroll_container).scrollTop(10);
        } else {
            this.update_listing(data, false);
        }
    },

    listen: function() {
        $(document).on("click", "td[class*=openable]", $.proxy(this.viewmail_loader, this));
        $(document).on("click", "a[name=selectmsgs]", $.proxy(this.selectmsgs, this));
        $(document).on("click", "a[name=release-multi]",
            $.proxy(this.release_selection, this));
        $(document).on("click", "a[name=delete-multi]",
            $.proxy(this.delete_selection, this));
        $(document).on("click", "a[name=mark-as-spam-multi]",
            $.proxy(this.mark_selection_as_spam, this));
        $(document).on("click", "a[name=mark-as-ham-multi]",
            $.proxy(this.mark_selection_as_ham, this));
        $(document).on("click", "a[name=viewrequests]",
            $.proxy(this.view_requests, this));
        $(document).on("click", "a[name=release]", $.proxy(this.release, this));
        $(document).on("click", "a[name=delete]", $.proxy(this.delete, this));
        $(document).on("click", "a[name=mark-as-spam]",
            $.proxy(this.mark_as_spam, this));
        $(document).on("click", "a[name=mark-as-ham]",
            $.proxy(this.mark_as_ham, this));
        $(document).on("click", "a[name=headers]", $.proxy(this.headers, this));
        $(document).on("click", "td[name=type] span", $.proxy(this.filter_by_type, this));
        $(document).on("click", "#filters label", $.proxy(this.filter_by_type, this));
    },

    load_page: function(e) {
        Listing.prototype.load_page.apply(this, arguments);
        this.navobj.delparam("rcpt").update();
    },

    /**
     * Return extra arguments used to fetch a page.
     *
     * @this Listing
     */
    get_load_page_args: function() {
        var args = Listing.prototype.get_load_page_args.call(this);

        args.scroll = true;
        return args;
    },

    /**
     * Calculate the bottom position of the scroll container.
     *
     * @param {Object} $element - scroll container object
     */
    calculate_bottom: function($element) {
        var emails_height = $("#emails").height();

        if (!emails_height) {
            return undefined;
        }
        return $("#emails").height() - $element.height();
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

    /*
     * Toggle message selection when the top checkbox's state is
     * modified.
     *
     * If it is checked, all messages are selected. Otherwise, the
     * current selection is resetted.
     */
    toggle_selection: function(e) {
        if (!$('#selectall').prop('checked')) {
            $("#emails").htmltable("clear_selection");
            return;
        }
        $("td[name*=selection]").each(function() {
            var $input = $(this).children('input');
            $input.prop('checked', true);
            $('#emails').htmltable('select_row', $(this).parent());
        });
    },

    /*
     * Select all messages of a specific type.
     */
    selectmsgs: function(e) {
        e.preventDefault();
        var type = get_target(e, 'a').attr("href");
        var counter = 0;

        $("td[name=type]").each(function() {
            var $this = $(this);
            if ($this.find('span').html().trim() == type) {
                var $input = $this.parent().children('td[name=selection]').children('input');
                $input.prop('checked', true);
                $('#emails').htmltable('select_row', $this.parent());
                counter++;
            }
        });
        if (counter) {
            $("#selectall").prop('checked', true);
        }
    },

    /**
     * Filter listing by message type (spam, virus, etc.)
     *
     * @param {Object} evt - event object
     */
    filter_by_type: function(evt) {
        var $target = $(evt.target);
        var msgtype;

        if ($target.is("span")) {
            msgtype = $target.html().trim();
        } else {
            msgtype = $target.children("input").attr("name").replace("msgtype_", "");
        }

        if (msgtype != 'all') {
            this.navobj.setparam('msgtype', msgtype);
        } else {
            this.navobj.delparam('msgtype');
        }
        this.navobj.update();
    },

    /**
     * Return the list of currently selected messages.
     *
     * @return {Array} - list of message IDs
     */
    get_current_selection: function() {
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
        return selection;
    },

    _send_selection: function(e, name, message) {
        var $link = $(e.target);

        e.preventDefault();
        if (!this.htmltable.current_selection().length ||
            !confirm(message)) {
            return;
        }
        var selection = this.get_current_selection();

        $.ajax({
            url: $link.attr("href"),
            data: "action=" + name + "&selection=" + selection.join(","),
            type: 'POST',
            dataType: 'json'
        }).done(
            $.proxy(this.action_cb, this)
        ).fail(function(jqxhr) {
            var data = $.parseJSON(jqxhr.responseText);
            $("body").notify("error", data.message);
        });
    },

    release_selection: function(e) {
        this._send_selection(e, "release", gettext("Release this selection?"));
    },

    delete_selection: function(e) {
        this._send_selection(e, "delete", gettext("Delete this selection?"));
    },

    /**
     * Show the recipient selection form inside a modal box.
     *
     * @param {Object} evt - event object
     * @param {string} ltype - learning type (spam or ham)
     */
    show_select_rcpt_form: function(evt, ltype, selection) {
        if (selection === undefined) {
            selection = this.get_current_selection();
        }
        var url = this.options.learning_recipient_url +
            "?type=" + ltype + "&selection=" +
            selection.join(","); 
        var $this = this;

        modalbox(evt, null, url, function() {
            $(".submit").on("click", function(evt) {
                simple_ajax_form_post(evt, {
                    formid: "learning_recipient_form",
                    reload_on_success: false,
                    success_cb: $.proxy($this.action_cb, $this)
                });
            });
        });
    },

    /**
     * Mark the current selection as spam.
     *
     * @param {Object} e - event object
     */
    mark_selection_as_spam: function(e) {
        if (this.options.check_learning_rcpt &&
            this.htmltable.current_selection().length) {
            this.show_select_rcpt_form(e, "spam");
        } else {
            this._send_selection(
                e, "mark_as_spam", gettext("Mark this selection as spam?"));
        }
    },

    /**
     * Mark the current selection as ham.
     *
     * @param {Object} e - event object
     */
    mark_selection_as_ham: function(e) {
        if (this.options.check_learning_rcpt &&
            this.htmltable.current_selection().length) {
            this.show_select_rcpt_form(e, "ham");
        } else {
            this._send_selection(
                e, "mark_as_ham", gettext("Mark this selection as non-spam?"));
        }
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
            type: 'POST',
            data: {rcpt: get_parameter_by_name($link.attr("href"), 'rcpt')}
        }).done(
            $.proxy(this.action_cb, this)
        ).fail(function(jqxhr) {
            var data = $.parseJSON(jqxhr.responseText);
            $("body").notify("error", data.message);
        });
    },

    release : function(e) {
        this._send_action(e, gettext("Release this message?"));
    },

    delete: function(e) {
        this._send_action(e, gettext("Delete this message?"));
    },

    /**
     * Mark the current message as spam.
     *
     * @param {Object} e - event object
     */
    mark_as_spam: function(e) {
        if (this.options.check_learning_rcpt) {
            var $link = get_target(e, "a");
            var selection = get_parameter_by_name($link.attr("href"), "rcpt") +
                " " + $link.attr("data-mail-id");
            this.show_select_rcpt_form(e, "spam", [selection]);
        } else {
            this._send_action(e, gettext("Mark as spam?"));
        }
    },

    /**
     * Mark the current message as ham.
     *
     * @param {Object} e - event object
     */
    mark_as_ham: function(e) {
        if (this.options.check_learning_rcpt) {
            var $link = get_target(e, "a");
            var selection = get_parameter_by_name($link.attr("href"), "rcpt") +
                " " + $link.attr("data-mail-id");
            this.show_select_rcpt_form(e, "ham", [selection]);
        } else {
            this._send_action(e, gettext("Mark as non-spam?"));
        }
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
                global: false
            }).done($.proxy(function(data) {
                $mailcontent.find("#table-container").append($(data));
                this.show_rawheaders($mailcontent);
            }, this));
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

    activate_buttons: function($tr) {
        $("a[name*=-multi]").removeClass('disabled');
        $("#selectall").prop('checked', true);
    },

    deactivate_buttons: function($tr) {
        if (!this.htmltable || !this.htmltable.current_selection().length) {
            $("a[name*=-multi]").addClass('disabled');
            $("#selectall").prop('checked', false);
        }
    },

    /**
     * Navigation callback: listing.
     *
     * @this Quarantine
     * @param {Object} data - ajax call response (JSON)
     */
    listing_cb: function(data) {
        this.update_page(data);
        this.navobj.delparam("rcpt").update();
        this.set_msgtype();
        $("#emails").htmltable({
            row_selected_event: this.activate_buttons,
            row_unselected_event: $.proxy(this.deactivate_buttons, this)
        });
        this.htmltable = $("#emails").data("htmltable");
        this.deactivate_buttons();
        if (this.navobj.hasparam("reset_page")) {
            this.navobj.delparam("reset_page").update(false, true);
        }
        $("#listing").css("overflow", "auto");
    },

    viewmail_cb: function(data) {
        this.update_page(data);
        $("#listing").css("overflow", "hidden");
    },

    action_cb: function(data) {
        if (data.reload) {
            this.navobj.update(true);
        }
        if (data.url) {
            this.navobj.parse_string(data.url, true).update(true);
        }
        $("body").notify("success", data.message, 2000);
    }
};

Quarantine.prototype = $.extend({}, Listing.prototype, Quarantine.prototype);
