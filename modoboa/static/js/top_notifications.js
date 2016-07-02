/**
 * Top notifications poller.
 */

var TopNotifications = function(options) {
    this.initialize(options);
};

TopNotifications.prototype = {
    constructor: TopNotifications,

    defaults: {
        container_id: "#top_notifications",
        global_counter_id: "#alerts-counter",
        url: null,
        interval: 1000
    },

    /**
     * Constructor.
     */
    initialize: function(options) {
        this.options = $.extend({}, this.defaults, options);
        this.poller = new Poller(this.options.url, {
            interval: this.options.interval,
            success_cb: $.proxy(this.update, this)
        });
        this.$container = $(this.options.container_id);
    },

    /**
     * Build a notification entry content.
     */
    build_link_content: function(data) {
        var content = "";

        if (data.counter) {
            content = "<span class='label label-" +
                data.level + "'>" + data.counter + "</span> " +
                data.text;
        } else {
            content = "<span class='fa fa-info-circle'></span> " + data.text;
        }
        return content;
    },

    /**
     * Append an entry to the notification list.
     */
    append_entry: function(data) {
        if ((data.counter !== undefined && data.counter === 0) ||
            (data.counter === undefined && data.text === undefined)) {
            return;
        }

        var $li = $("<li />");

        $li.append(
            $("<a />", {
                id: data.id, href: data.url,
                html: this.build_link_content(data)
            })
        );
        this.$container.find(".dropdown-menu").append($li);
    },

    /**
     * Update an existing entry in the notification list.
     */
    update_entry: function(data) {
        var $link = $("#" + data.id);

        if ((data.counter !== undefined && data.counter === 0) ||
            (data.counter === undefined && data.text === undefined)) {
            $link.parent().remove();
            return;
        }
        $link.html(this.build_link_content(data));
    },

    /**
     * Poller callback.
     */
    update: function(data) {
        for (var cpt = 0; cpt < data.length; cpt++) {
            var $link = $("#" + data[cpt].id);
            if (!$link.length) {
                this.append_entry(data[cpt]);
            } else {
                this.update_entry(data[cpt]);
            }
        }
        var $entries = this.$container.find(".dropdown-menu li");
        if ($entries.length) {
            this.$container.removeClass("hidden");
            $(this.options.global_counter_id).html($entries.length);
        } else {
            this.$container.addClass("hidden");
        }
    }
};
