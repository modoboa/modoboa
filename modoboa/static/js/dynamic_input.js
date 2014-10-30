(function($) {

    /**
     * Creates an instance of DynamicInput.
     *
     * @constructor
     * @this DynamicInput
     * @param {Object} element -
     * @param {Object} options -
     */
    var DynamicInput = function(element, options) {
        this.$element = $(element);
        this.$input = (this.$element.is("input")) ? 
            this.$element : this.$element.find("input");
        this.options = $.extend({}, $.fn.dynamic_input.defaults, options);
        this.nextid = 1;
        this.baseid = this.$input.attr("id");
        this.basename = this.$input.attr("name").split("_")[0];

        this.$input.keyup($.proxy(this.checknotempty, this));

        for (var cpt = 1; true; cpt++) {
            var $input = $("#" + this.baseid + "_" + cpt);

            if (!$input.length) {
                break;
            }
            $input.parent().after(this.addrmlink($input));
            $input.focusout(this.checkempty);
            this.nextid++;
        }
    };

    DynamicInput.prototype = {
        constructor: DynamicInput,

        /**
         * Add a remove link right to an input.
         *
         * @this DynamicInput
         * @param {Object} input - target input
         * @return {Object} - created link
         */
        addrmlink: function(input) {
            var $rmlink = $(
                "<a href='#' id='{0}_rmbtn'>".format(input.attr("id")) +
                "<span class='fa fa-remove'></span></a>"
            );

            $rmlink.click($.proxy(this.removeinput, this));
            return $rmlink;
        },

        /**
         * Add a new input.
         *
         * @this DynamicInput
         */
        addinput: function() {
            var $clone = this.$element.clone();
            var id = this.baseid + '_' + this.nextid;
            var name = this.basename + '_' + this.nextid;

            $clone.insertAfter(this.$element);

            var $ninput = $clone.find("input").attr("id", id).attr("name", name);
            var $rmlink = this.addrmlink($ninput);

            $clone.append($rmlink);
            $ninput.focusout(this.checkempty);
            $ninput.val(this.$input.val());
            this.$input.val(this.options.emptylabel);
            this.nextid++;

            if (this.options.input_added) {
                this.options.input_added($clone);
            }
        },

        /**
         * Click event. Remove an input.
         *
         * @this DynamicInput
         * @param {Object} evt - event object
         * @param {boolean} force - force the removal if true
         */
        removeinput: function(evt, force) {
            evt.preventDefault();

            var $link = get_target(evt, "a");
            var id = "#" + $link.attr("id").replace("_rmbtn", "");
            var $input = $(id);

            if ($input.val() === "" && (force === undefined || !force)) {
                return;
            }
            if (this.options.input_removed && this.options.input_removed($input)) {
                return;
            }
            $input.remove();
            $link.remove();
        },

        /**
         * Check if input's value is not empty before adding a new input.
         *
         * @this DynamicInput
         * @param {Object} evt - event object
         */
        checknotempty: function(evt) {
            if (evt.keyCode != 13) {
                return;
            }
            if (this.$input.val() === "") {
                return;
            }
            this.addinput();
        },

        /**
         * Focus out event : remove the input if it's value is empty.
         *
         * @param {Object} evt - event object
         */
        checkempty: function(evt) {
            var $input = $(evt.target);

            if ($input.val() === "") {
                $("#" + $input.attr("id") + "_rmbtn").trigger("click", true);
            }
        }
    };

    $.fn.dynamic_input = function(method) {
        return this.each(function() {
            var $this = $(this),
                data = $this.data('dynamic_input'),
                options = typeof method === "object" && method;

            if (!data) {
                $this.data('dynamic_input', new DynamicInput(this, options));
            }
            if (typeof method === "string") {
                data[method]();
            }
        });
    };

    /*
     * Allow an external access to the constructor (for inheritance)
     */
    $.fn.dynamic_input.Constructor = DynamicInput;

    $.fn.dynamic_input.defaults = {
        emptylabel: "",
        input_added: null,
        input_removed: null
    };

})(jQuery);
