/**
 * @module jquery.dynamicrule
 */

(function($) {
    var DynamicRule = function(element, options) {
        this.initialize(element, options);
    };

    DynamicRule.prototype = {
        constructor: DynamicRule,

        /**
         * Creates an instance of DynamicRule.
         *
         * @constructor
         * @this {DynamicRule}
         * @param {object} element -
         * @param {dictionary} options - instance options
         */
        initialize: function(element, options) {
            this.$element = $(element);
            this.options = $.extend({}, $.fn.dynamicrule.defaults, options);
            this.rules_counter = 1;

            $(document).on(
                "click", "a[class=addrule]", $.proxy(this.add_rule, this)
            );
            $(document).on(
                "click", "a[class=delrule]", $.proxy(this.delete_rule, this)
            );
        },

        /**
         * Reset the current rule to default values.
         */
        reset_original_rule: function() {
            this.$element.find("#id_username").prop("value", "");
            this.$element.find("#id_read_access").prop("checked", "");
            this.$element.find("#id_write_access").prop("checked", "");
        },

        /**
         * Save the current rule to a new set of elements and reset
         * the original ones.
         */
        add_rule: function(event) {
            var rulename = $("#id_username").prop("value");
            
            event.preventDefault();
            if (rulename === "") {
                return;
            }
            var $clone = this.$element.clone();
            var $btn = $clone.find("a");

            $clone.attr("id", "");
            $btn.find("span").removeClass("fa-plus").addClass("fa-trash");
            $btn.removeClass("addrule").addClass("delrule");
            $clone.find("#id_username")
                .attr("id", "id_username_" + this.rules_counter)
                .attr("name", "username_" + this.rules_counter);
            $clone.find("#id_read_access")
                .attr("id", "id_read_access_" + this.rules_counter)
                .attr("name", "read_access_" + this.rules_counter);
            $clone.find("#id_write_access")
                .attr("id", "id_write_access_" + this.rules_counter)
                .attr("name", "write_access_" + this.rules_counter);
            $clone.insertAfter(this.$element);
            this.rules_counter++;
            this.reset_original_rule();
        },

        /**
         * Delete a given rule.
         *
         * @param {object} event - event object
         */
        delete_rule: function(event) {
            event.preventDefault();
            var $link = get_target(event, "a");

            $link.parent().remove();
        }
    };

    $.fn.dynamicrule = function(method) {
        return this.each(function() {
            var $this = $(this),
                data = $this.data('dynamicrule'),
                options = typeof method === "object" && method;

            if (!data) {
                $this.data('dynamicrule', new DynamicRule(this, options));
            }
            if (typeof method === "string") {
                data[method]();
            }
        });
    };

    $.fn.dynamicrule.defaults = {
    };

})(jQuery);
