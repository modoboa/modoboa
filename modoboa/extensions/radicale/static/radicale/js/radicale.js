/**
 * @module radicale
 * @desc Utility class for the radicale extension
 */
var Radicale = function(options) {
    Listing.call(this, options);
};

Radicale.prototype = {
    constructor: Radicale,

    defaults: {
        deflocation: "calendars/"
    },

    initialize: function(options) {
        Listing.prototype.initialize.call(this, options);
        this.options = $.extend({}, this.defaults, this.options);
        this.options.defcallback = $.proxy(this.list_cb, this);
        this.navobj = new History(this.options);
        this.register_tag_handler("cal", this.generic_tag_handler);
        $(document).on(
            "click", "a[name=delcalendar]", $.proxy(this.del_calendar, this)
        );
    },

    list_cb: function(data) {
        $("#listing").html(data.table);
        this.update_listing(data);
        $("a.filter").click($.proxy(this.filter_by_tag, this));
    },

    /**
     * Refresh the listing.
     *
     */
    reload_listing: function(data) {
        console.log("reload");
        this.navobj.update(true);
        if (data) {
            $("body").notify("success", data, 2000);
        }
    },

    /**
     * Rights form initialization.
     */
    rightsform_init: function() {
        $("#original_row").dynamicrule();
        $("#id_username").autocompleter({
            choices: $.proxy(this.get_username_list, this)
        });
    },

    add_calendar_cb: function() {
        this.rightsform_init();
        $("#wizard").cwizard({
            formid: "newcal_form",
            success_callback: $.proxy(this.reload_listing, this)
        });
    },

    /**
     * Retrieve a list of username from the server.
     */
    get_username_list: function() {
        var result;

        $.ajax({
            url: this.options.username_list_url,
            dataType: "json",
            async: false
        }).done(function(data) {
            result = data;
        });
        return result;
    },

    edit_calendar_cb: function() {
        this.rightsform_init();
        $('.submit').on('click', $.proxy(function(e) {
            simple_ajax_form_post(e, {
                formid: "ucal_form",
                reload_on_success: false,
                success_cb: $.proxy(this.reload_listing, this)
            });
        }, this));
    },

    shared_calendar_cb: function() {
        $('.submit').on('click', $.proxy(function(e) {
            simple_ajax_form_post(e, {
                formid: "sharedcal_form",
                reload_on_success: false,
                success_cb: $.proxy(this.reload_listing, this)
            });
        }, this));
    },

    /**
     * Delete a user calendar.
     */
    del_calendar: function(event) {
        event.preventDefault();
        var $link = get_target(event, "a");

        if (!confirm($link.attr("title"))) {
            return;
        }
        $.ajax({
            url: $link.attr("href"),
            type: "DELETE"
        }).done($.proxy(this.reload_listing, this));
    }
};

Radicale.prototype = $.extend({}, Listing.prototype, Radicale.prototype);
