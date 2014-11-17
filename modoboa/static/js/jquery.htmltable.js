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
            this.ctrl_pressed = false;
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
            this.$element
                .off("change", "input[type=checkbox]")
                .on("change", "input[type=checkbox]",
                    $.proxy(this.toggle_select, this));
            $(document).on("keydown", "body", $.proxy(this.keydown, this));
            $(document).on("keyup", "body", $.proxy(this.keyup, this));
        },

        /**
         * Effective change of a row's state.
         */
        _toggle_select: function($row) {
            var $input = $row.find(this.options.input_selector);

            if ($row.hasClass(this.options.row_selected_class)) {
                $input.prop('checked', false);
                $row.removeClass(this.options.row_selected_class);
                if (this.options.row_unselected_event !== undefined) {
                    this.options.row_unselected_event($row);
                }
            } else {
                $input.prop('checked', true);
                $row.addClass(this.options.row_selected_class);
                if (this.options.row_selected_event !== undefined) {
                    this.options.row_selected_event($row);
                }
            }
        },

        /**
         * Change the selection state of a given row.
         *
         * Holding the shift key between two selections let users
         * select all rows between those two locations.
         *
         * Holding the ctrl key between two selections let users make
         * an additive selection.
         */
        toggle_select: function(e) {
            var $row = $(e.target).parents(this.options.row_selector);

            if (this.shift_pressed && this.last_selection) {
                var start = this.last_selection;

                this.clear_selection();
                this.last_selection = start;

                var itfunc = ($row.index() >= this.last_selection.index()) ? 
                    "next" : "prev";
                var $cur_row = null;

                if (this.prev_dir && itfunc != this.prev_dir) {
                    $cur_row = this.last_selection;
                } else {
                    $cur_row = this.last_selection;
                }
                for (; $cur_row.length; $cur_row = $cur_row[itfunc](this.options.row_selector)) {
                    this._toggle_select($cur_row);
                    if ($row.attr("id") == $cur_row.attr("id")) {
                        break;
                    }
                }
                this.prev_dir = itfunc;
                return;
            } else if (!this.ctrl_pressed && (!this.last_selection || !this.last_selection.is($row))) {
                this.clear_selection();
            }
            this.last_selection = $row;
            this._toggle_select($row);
        },

        /**
         * Check if $row is selected or not.
         */
        is_selected: function($row) {
            return $row.hasClass(this.options.row_selected_class);
        },

        /**
         * Return the current selection. (jQuery object)
         */
        current_selection: function() {
            return this.$element.find("." + this.options.row_selected_class);
        },

        /**
         * Cancel the current selection.
         */
        clear_selection: function() {
            this.last_selection = null;
            this.current_selection().removeClass(this.options.row_selected_class);
            this.$element.find(this.options.input_selector).prop('checked', false);
            if (this.options.row_unselected_event !== undefined) {
                this.options.row_unselected_event();
            }
        },

        /**
         * Manually select a row.
         */
        select_row: function($row) {
            if (!this.last_selection) {
                this.last_selection = $row;
            }
            $row.addClass(this.options.row_selected_class);
            if (this.options.row_selected_event !== undefined) {
                this.options.row_selected_event($row);
            }
        },

        keydown: function(e) {
            switch (e.which) {
            case 16:
                e.preventDefault();
                this.shift_pressed = true;
                break;
            case 17:
                this.ctrl_pressed = true;
                break;
            }
        },

        keyup: function(e) {
            switch (e.which) {
            case 16:
                e.preventDefault();
                this.shift_pressed = false;
                break;
            case 17:
                this.ctrl_pressed = false;
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
        row_selector: 'tr',
        input_selector: "input[type=checkbox]",
        row_selected_class: 'tr-selected'
    };
})(jQuery);
