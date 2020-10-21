/**
 * Return an instance of Settings.
 *
 * @constructor
 * @param {Object} options - instance options
 */
/* global TwocolsNav */

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
        this.navobj.register_callback(
            "extensions", $.proxy(this.extensions_callback, this));
        $(document).on("click", "#toggle_extensions_sel", this.toggle_extensions_sel);
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
    },

    /**
     * Navigation callback: extensions.
     */
    extensions_callback: function(data) {
        this.select_left_menu();
        if (data.content) {
            $('#' + this.options.divid).html(data.content);
        }
        this.update_listing(data);
        if ($("tbody input[type=checkbox]:checked").length) {
            $("#toggle_extensions_sel").prop("checked", true);
        }
    },

    /**
     * Select or unselect all extensions in on click.
     */
    toggle_extensions_sel: function(evt) {
        var status = $(this).prop("checked");

        $("tbody input[type=checkbox]").prop("checked", status);
    }
};

Settings.prototype = $.extend({}, TwocolsNav.prototype, Settings.prototype);
