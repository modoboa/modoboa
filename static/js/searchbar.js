(function($) {
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
                if ($this.attr("value") == "") {
                    $this.attr("value", gettext("Search..."));
                }
            });
            if (this.options.navobj.params.pattern != undefined) {
                this.$element.attr("value", this.options.navobj.params.pattern);
            }
            if (this.options.navobj.params.criteria != undefined) {
                $("#crit_" + this.options.navobj.params.criteria).attr("checked", "checked");
            }
        },

        pattern_change: function(e) {
            var $input = $(e.target);
            var criteria = $("input[name=scriteria]:checked").attr("value");
            var pattern = $input.attr("value");

            if (pattern != "") {
                this.options.navobj.setparams({
                    pattern: pattern,
                    criteria: criteria
                });
            } else {
                this.options.navobj.deleteParam("pattern");
                this.options.navobj.deleteParam("criteria");
                this.options.navobj.deleteParam("page");
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
        navobj: null
    };
})(jQuery);