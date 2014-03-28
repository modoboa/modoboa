var Radicale = function() {
    this.initialize();
};

Radicale.prototype = {
    constructor: Radicale,

    initialize: function() {
        $(document).on(
            "click", "a[name=delcalendar]", this.del_calendar
        );
    },

    add_calendar_cb: function() {
        $("#wizard").cwizard({
            formid: "newcal_form"
        });
    },

    add_shared_calendar_cb: function() {
        $('.submit').on('click', $.proxy(function(e) {
            simple_ajax_form_post(e, {
                formid: "newsharedcal_form",
                reload_on_success: false
                /*success_cb: $.proxy(this.reload_listing, this)*/
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
        }).done(function(data) {
            $("body").notify("success", data, 2000);
        });
    }
};
