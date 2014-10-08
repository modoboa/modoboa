/**
 * Return an instance of Settings.
 *
 * @constructor
 * @param {Object} options - instance options
 */
var Settings = function(options) {
    TwocolsNav.call(this, options);
};

Settings.prototype = {
    defaults: {
        main_table_id: "logs_table",
        eor_message: gettext("No more log entry to show")
    },

    initialize: function(options) {
        this.options = $.extend({}, this.defaults, options);
        TwocolsNav.prototype.initialize.call(this, this.options);
        this.navobj.register_callback(
            "logs", $.proxy(this.logs_callback, this));
    },

    /**
     * Navigation callback: logs.
     *
     */
    logs_callback: function(data) {
        this.select_left_menu();
        if (data.content) {
            $('#' + this.options.divid).html(data.content);
        }
        this.update_listing(data);
    }
};

Settings.prototype = $.extend({}, TwocolsNav.prototype, Settings.prototype);
