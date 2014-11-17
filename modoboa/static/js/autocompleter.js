(function($) {
    "use strict";

    var Autocompleter = function(element, options) {
        this.initialize(element, options);
    };

    Autocompleter.prototype = {
        constructor: Autocompleter,

        initialize: function(element, options) {
            this.$element = $(element);
            this.options = $.extend({}, $.fn.autocompleter.defaults, options);
            if (typeof this.options.choices === "function") {
                this.choices = this.options.choices();
            } else {
                this.choices = this.options.choices;
            }
            this.$menu =
                $('<ul class="dropdown-menu autocompleter" data-toggle="dropdown" />');
            $("body").append(this.$menu);
            this.$menu.on("click", $.proxy(this.select_entry, this));

            this.$element.attr("autocomplete", "off");
            this.listen();
        },

        listen: function() {
            this.$element.keydown($.proxy(this.keydown, this));
            this.$element.keyup($.proxy(this.keyup, this));
            this.$element.blur($.proxy(this.hide_menu, this));
        },

        unbind: function() {
            this.$element.off("keydown keyup blur");
        },

        check_user_input: function() {
            var value = this.$element.val();
            var start = -1;
            var pattern = null;

            if (this.options.from_character) {
                start = value.indexOf(this.options.from_character);
                if (start == -1) {
                    return;
                }
                pattern = value.substr(start + 1);
            } else {
                pattern = value;
            }

            var exp = new RegExp("^" + pattern);

            this.$menu.empty();
            $.each(this.choices, $.proxy(function(index, value) {
                if (exp.test(value)) {
                    this.$menu.append(
                        $('<li><a href="#" name="' + value + '">' + value + '</a></li>')
                    );
                }
            }, this));

            var coords = this.$element.offset();

            this.$menu.css({
                position: "absolute",
                top: coords.top + this.$element.outerHeight(),
                left: coords.left,
                width: this.$element.outerWidth(),
                'z-index': 1051
            });
            if (this.$menu.children().length) {
                this.$menu.children().first().addClass("active");
                this.$menu.show();
            } else {
                this.$menu.hide();
            }
        },

        hide_menu: function() {
            setTimeout($.proxy(function() { this.$menu.hide(); }, this), 150);
        },

        select_entry: function(evt) {
            if (this.$menu.is(":visible")) {
                var $link;
                if (evt !== undefined) {
                    evt.preventDefault();
                    $link = $(evt.target);
                } else {
                    $link = this.$menu.find('.active > a');
                }
                var curvalue = this.$element.val();

                if (curvalue === undefined || curvalue === "") {
                    if (this.options.empty_choice) {
                        this.options.empty_choice();
                    }
                    return;
                }
                if ($link.length) {
                    this.$element.val(curvalue.substr(
                        0, curvalue.indexOf(this.options.from_character) + 1
                    ) + $link.attr("name"));
                }
                this.hide_menu();
            }
            if (this.options.choice_selected) {
                this.options.choice_selected(this.$element.val());
            }
        },

        activate_next: function() {
            var active = this.$menu.find('.active').removeClass('active'),
                next = active.next();

            if (!next.length) {
                next = $(this.$menu.find('li').first());
            }
            next.addClass('active');
        },

        activate_prev: function() {
            var active = this.$menu.find('.active').removeClass('active'),
                prev = active.prev();

            if (!prev.length) {
                prev = this.$menu.find('li').last();
            }

            prev.addClass('active');
        },

        keydown: function(evt) {
            evt.stopPropagation();

            switch (evt.which) {
                case 13:
                case 27:
                    evt.preventDefault();
                    break;
                case 38:
                    evt.preventDefault();
                    this.activate_prev();
                    break;
                case 40:
                    evt.preventDefault();
                    this.activate_next();
                    break;
            }
        },

        keyup: function(evt) {
            evt.stopPropagation();
            evt.preventDefault();

            switch (evt.which) {
            case 40:
            case 38:
                break;

            case 13:
                this.select_entry();
                break;

            case 27:
                this.hide_menu();
                break;

            default:
                this.check_user_input();
            }
        }
    };

    $.fn.autocompleter = function(option) {
        return this.each(function() {
            var $this = $(this),
                data = $this.data('autocompleter'),
                options = typeof option === "object" && option;

            if (!data) {
                $this.data('autocompleter', new Autocompleter(this, options));
            }
            if (typeof option === "string") {
                data[option]();
            }
        });
    };

    $.fn.autocompleter.defaults = {
        'choice_selected' : null,
        'empty_choice' : null
    };

})(jQuery);
