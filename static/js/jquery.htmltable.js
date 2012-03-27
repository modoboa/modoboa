(function($) {
    var HtmlTable = function(element, options) {
        this.initialize(element, options);
    };

    HtmlTable.prototype = {
        constructor: HtmlTable,

        initialize: function(element, options) {
            this.$element = $(element);
            this.options = $.extend({}, $.fn.htmltable.defaults, options);
            this.shift_pressed = false;
            this.last_selection = null;
            this.prev_dir = null;
            this.listen();

            this.$element.css({
                "-moz-user-select": "-moz-none",
                "-khtml-user-select": "none",
                "-webkit-user-select": "none",
                "-ms-user-select": "none",
                "user-select": "none"
            });
            this.$element.attr("unselectable", "on");
        },

        listen: function() {
            $(document).on("click", "tbody>tr",
                $.proxy(this.toggle_select, this));
            $(document).on("keydown", "body", $.proxy(this.keydown, this));
            $(document).on("keyup", "body", $.proxy(this.keyup, this));
        },

        _toggle_select: function($tr) {
            this.last_selection = $tr;
            if ($tr.hasClass(this.options.tr_selected_class)) {
                $tr.removeClass(this.options.tr_selected_class);
            } else {
                $tr.addClass(this.options.tr_selected_class);
            }
        },

        toggle_select: function(e) {
            e.preventDefault();
            var $tr = $(e.target).parent();

            if (this.shift_pressed && this.last_selection) {
                var itfunc = ($tr.index() >= this.last_selection.index())
                    ? "next" : "prev";
                var $curtr = null;

                if (this.prev_dir && itfunc != this.prev_dir) {
                    $curtr = this.last_selection;
                } else {
                    $curtr = this.last_selection[itfunc]("tr");
                }
                for (; $curtr.length; $curtr = $curtr[itfunc]("tr")) {
                    this._toggle_select($curtr);
                    if ($tr.attr("id") == $curtr.attr("id")) {
                        break;
                    }
                }
                this.prev_dir = itfunc;
                return;
            }
            this._toggle_select($tr);
        },

        current_selection: function() {
            return $("tr[class*=" + this.options.tr_selected_class + "]");
        },

        /*
         * Cancel the current selection
         */
        clear_selection: function() {
            this.current_selection().removeClass(this.options.tr_selected_class);
        },

        /*
         * Manually select a table row
         */
        select_row: function($row) {
            $row.addClass(this.options.tr_selected_class);
        },

        keydown: function(e) {
            switch (e.which) {
            case 16:
                e.preventDefault();
                this.shift_pressed = true;
                break;
            }
        },

        keyup: function(e) {
            switch (e.which) {
            case 16:
                e.preventDefault();
                this.shift_pressed = false;
                break;
            }
        }
    };

    $.fn.htmltable = function(method) {
        var args = arguments;

        return this.each(function() {
            var $this = $(this),
                data = $this.data('htmltable'),
                options = typeof method === "object" && method;

            if (!data) {
                $this.data('htmltable', new HtmlTable(this, options));
                data = $this.data('htmltable');
            }
            if (typeof method === "string") {
                data[method].apply(data, Array.prototype.slice.call(args, 1));
            }
        });
    };

    $.fn.htmltable.defaults = {
        tr_selected_class: 'tr-selected'
    };
})(jQuery);