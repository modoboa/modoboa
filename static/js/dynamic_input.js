(function($) {
    var DynamicInput = function(element, options) {
        console.log(element);
        this.$element = $(element);
        this.options = $.extend({}, $.fn.dynamic_input.defaults, options);
        this.nextid = 1;
        this.baseid = this.$element.attr("id");
        this.basename = this.$element.attr("name").split("_")[0];

        this.$element.keyup($.proxy(this.checknotempty, this));
        for (var cpt = 1; true; cpt++) {
            var $input = $("#" + this.baseid + "_" + cpt);

            if (!$input.length) {
                break;
            }
            $input.after(this.addrmlink($input));
            $input.focusout(this.checkempty);
            this.nextid++;
        }
    };

    DynamicInput.prototype = {
        constructor: DynamicInput,

        addrmlink: function(input) {
            var $rmlink = $('<a href="#"'
                + 'id="' + input.attr("id") + '_rmbtn' + '"'
                + '"><i class="icon-remove"></i></a>');

            $rmlink.click($.proxy(this.removeinput, $rmlink));
            return $rmlink;
        },

        addinput: function() {
            var id = this.baseid + '_' + this.nextid;
            var name = this.basename + '_' + this.nextid;
            var $ninput = $('<input type="text"'
                + 'id="' + id + '" '
                + 'name="' + name + '"'
                + '/>');
            var $rmlink = this.addrmlink($ninput);

            $ninput.focusout(this.checkempty);
            $ninput.attr("value", this.$element.attr("value"));
            this.$element.attr("value", this.options.emptylabel);
            this.$element.after($ninput, $rmlink);
            this.nextid++;
        },

        removeinput: function(evt, force) {
            evt.preventDefault();
            var id = "#" + this.attr("id").replace("_rmbtn", "");
            var $input = $(id);

            if ($input.attr("value") == "" && (force == undefined || !force)) {
                return;
            }
            $input.remove();
            this.remove();
        },

        checknotempty: function(evt) {
            if (evt.keyCode != 13) {
                return;
            }
            if (this.$element.attr("value") == "") {
                return;
            }
            this.addinput();
        },

        checkempty: function(evt) {
            var $input = $(evt.target);

            if ($input.attr("value") == "") {
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
        emptylabel: ""
    };

})(jQuery);