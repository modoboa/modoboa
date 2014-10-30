/**
 * Creates an instance of Radicale.
 *
 * @constructor
 * @param {Object} options - instance options
 * @classdesc This class contains a set of methods used by the
 * Radicale application.
 */
var Radicale = function(options) {
    Listing.call(this, options);
};

Radicale.prototype = {
    constructor: Radicale,

    defaults: {
        deflocation: "list/",
        main_table_id: "calendar_table",
        eor_message: gettext("No more calendar to show")
    },

    initialize: function(options) {
        this.options = $.extend({}, this.defaults, options);
        this.options.defcallback = $.proxy(this.list_cb, this);
        Listing.prototype.initialize.call(this, this.options);
        this.options.navigation_params.push("calfilter");
        this.register_tag_handler("cal", this.generic_tag_handler);
        $(document).on(
            "click", "a[name=delcalendar]", $.proxy(this.del_calendar, this)
        );
    },

    list_cb: function(data) {
        $("#{0} tbody".format(this.options.main_table_id)).html(data.rows);
        this.update_listing(data);
    },

    /**
     * Refresh the listing.
     *
     * @this Radicale
     * @param {Object} data - the ajax call response (JSON)
     */
    reload_listing: function(data) {
        this.navobj.update(true);
        if (data) {
            $("body").notify("success", data, 2000);
        }
    },

    /**
     * Rights form initialization.
     *
     * @this Radicale
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
