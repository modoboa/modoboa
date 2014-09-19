(function($) {
    var Notify = function(element, options) {
        this.$element = $(element);
        this.options = $.extend({}, $.fn.notify.defaults, options);
    };

    Notify.prototype = {
        constructor: Notify,

        build_box: function(bid) {
            if (bid === undefined) {
                bid = "notifybox";
            }
            var div = $("<div class='alert alert-dismissible' role='alert' />", {
                id: bid,
                click: $.proxy(this.destroy_box, this)
            }).css({
                position: "fixed"
            });

            return div;
        },

        destroy_box: function(evt) {
            evt.preventDefault();
            this.$element.hide().remove();
        },

        set_position: function(box) {
            box.css({
                'z-index': 100,
                top: this.options.top_position,
                left: "50%",
                'margin-left': -box.outerWidth(true) / 2
            });
        },

        set_message: function(box, value) {
            var content = '<button type="button" class="close" data-dismiss="alert"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>' + value;

            box.html(content);
        },

        show: function(klass, message, timer) {
            var nbox = this.build_box();

            if (klass != "normal") {
                nbox.addClass("alert-" + klass);
            }
            this.set_message(nbox, message);
            this.$element.append(nbox);
            this.set_position(nbox);
            if (timer !== undefined) {
                window.setTimeout(function() {
                    nbox.alert('close');
                }, timer);
            }
            return this;
        },

        success: function(message, timer) {
            return this.show.apply(this, ["success", message, timer]);
        },

        info: function(message, timer) {
            return this.show.apply(this, ["info", message, timer]);
        },

        error: function(message, timer) {
            return this.show.apply(this, ["danger", message, timer]);
        },

        warning: function(message, timer) {
            return this.show.apply(this, ["warning", message, timer]);
        },

        hide: function() {

        }
    };

    $.fn.notify = function(method) {
        var args = arguments;

        return this.each(function() {
            var $this = $(this),
                data = $this.data('notify'),
                options = typeof method === "object" && method;

            if (!data) {
                $this.data('notify', new Notify(this, options));
                data = $this.data('notify');
            }
            if (typeof method === "string") {
                data[method].apply(data, Array.prototype.slice.call(args, 1));
            }
        });
    };

    $.fn.notify.defaults = {
        top_position: 50
    };

})(jQuery);
