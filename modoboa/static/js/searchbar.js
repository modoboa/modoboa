(function($) {

    /**
     * Return an instance of SearchBar.
     *
     * @constructor
     * @param {Object} element - 
     * @param {Object} options - instance options
     */
    var SearchBar = function(element, options) {
        this.initialize(element, options);
    };

    SearchBar.prototype = {
        constructor: SearchBar,

        initialize: function(element, options) {
            this.$element = $(element);
            this.options = $.extend({}, $.fn.searchbar.defaults, options);

            this.$element.change($.proxy(this.pattern_change, this));
            this.$element.click(function(e) {
                $(this).select();
            });
            this.$element.blur(function(e) {
                var $this = $(this);
                if ($this.val() === "") {
                    $this.val(gettext("Search..."));
                }
            });
            if (this.options.navobj.params.pattern !== undefined) {
                this.$element.val(this.options.navobj.getparam("pattern"));
            }
            if (this.options.navobj.params.criteria !== undefined) {
                $("#crit_" + this.options.navobj.params.criteria).attr("checked", "checked");
            }
        },

        /**
         * Change event: apply search criterion.
         *
         * @this SearchBar
         * @param {Object} e - event object
         */
        pattern_change: function(e) {
            var $input = $(e.target);
            var criteria = $("input[name=scriteria]:checked").val();
            var pattern = $input.val();

            if (pattern !== "") {
                this.options.navobj.setparams({
                    pattern: pattern,
                    criteria: criteria
                });
            } else {
                this.options.navobj.delparam("pattern");
                this.options.navobj.delparam("criteria");
                this.options.navobj.delparam("page");
            }
            if (this.options.pattern_changed) {
                this.options.pattern_changed(this.options.navobj);
            }
            this.options.navobj.update();
        }
    };

    $.fn.searchbar = function(method) {
        return this.each(function() {
            var $this = $(this),
                data = $this.data('searchbar'),
                options = typeof method === "object" && method;

            if (!data) {
                $this.data('searchbar', new SearchBar(this, options));
            }
            if (typeof method === "string") {
                data[method]();
            }
        });
    };

    $.fn.searchbar.defaults = {
        navobj: null,
        pattern_changed: null
    };
})(jQuery);
