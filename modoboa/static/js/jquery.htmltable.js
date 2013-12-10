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
            $(document)
                .off("change", "tbody input[type=checkbox]")
                .on("change", "tbody input[type=checkbox]",
                    $.proxy(this.toggle_select, this));
            $(document).on("keydown", "body", $.proxy(this.keydown, this));
            $(document).on("keyup", "body", $.proxy(this.keyup, this));
        },

        /**
         * Effective change of a table row's state.
         */
        _toggle_select: function($tr) {
            if ($tr.hasClass(this.options.tr_selected_class)) {
                $tr.children('td[name=selection]').children('input').prop('checked', false);
                $tr.removeClass(this.options.tr_selected_class);
                if (this.options.tr_unselected_event != undefined) {
                    this.options.tr_unselected_event($tr);
                }
            } else {
                $tr.children('td[name=selection]').children('input').prop('checked', true);
                $tr.addClass(this.options.tr_selected_class);
                if (this.options.tr_selected_event != undefined) {
                    this.options.tr_selected_event($tr);
                }
            }
        },

        /**
         * Change the selection state of a given table row.
         *
         * Holding the shift key between two selections let users
         * select all rows between those two locations.
         *
         * Holding the ctrl key between two selections let users make
         * an additive selection.
         */
        toggle_select: function(e) {
            var $tr = $(e.target).parents('tr');

            if (this.shift_pressed && this.last_selection) {
                var start = this.last_selection;

                this.clear_selection();
                this.last_selection = start;
                var itfunc = ($tr.index() >= this.last_selection.index())
                    ? "next" : "prev";
                var $curtr = null;

                if (this.prev_dir && itfunc != this.prev_dir) {
                    $curtr = this.last_selection;
                } else {
                    $curtr = this.last_selection;
                }
                for (; $curtr.length; $curtr = $curtr[itfunc]("tr")) {
                    this._toggle_select($curtr);
                    if ($tr.attr("id") == $curtr.attr("id")) {
                        break;
                    }
                }
                this.prev_dir = itfunc;
                return;
            } else if (!this.ctrl_pressed && (!this.last_selection || !this.last_selection.is($tr))) {
                this.clear_selection();
            }
            this.last_selection = $tr;
            this._toggle_select($tr);
        },

        /**
         * Check if $row is selected or not.
         */
        is_selected: function($row) {
            return $row.hasClass(this.options.tr_selected_class);
        },

        /**
         * Return the current selection. (jQuery object)
         */
        current_selection: function() {
            return $("tr[class*=" + this.options.tr_selected_class + "]");
        },

        /**
         * Cancel the current selection.
         */
        clear_selection: function() {
            this.last_selection = null;
            this.current_selection().removeClass(this.options.tr_selected_class);
            $("tbody input[type=checkbox]").prop('checked', false);
            if (this.options.tr_unselected_event != undefined) {
                this.options.tr_unselected_event();
            }
        },

        /**
         * Manually select a table row.
         */
        select_row: function($row) {
            if (!this.last_selection) {
                this.last_selection = $row;
            }
            $row.addClass(this.options.tr_selected_class);
            if (this.options.tr_selected_event != undefined) {
                this.options.tr_selected_event($row);
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
        tr_selected_class: 'tr-selected'
    };
})(jQuery);