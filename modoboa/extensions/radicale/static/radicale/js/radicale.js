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
        $(document).on(
            "click", "a[name=delcalendar]", this.del_calendar
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
        this.navobj.update(true);
        if (data) {
            $("body").notify("success", data, 2000);
        }
    },

    add_calendar_cb: function() {
        $("#wizard").cwizard({
            formid: "newcal_form",
            success_callback: $.proxy(this.reload_listing, this)
        });
    },

    edit_calendar_cb: function() {
        $("#original_row").dynamicrule();
    },

    add_shared_calendar_cb: function() {
        $('.submit').on('click', $.proxy(function(e) {
            simple_ajax_form_post(e, {
                formid: "newsharedcal_form",
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
        var $link = $(this);

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
