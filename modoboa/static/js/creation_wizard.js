(function($) {
    var Cwizard = function(element, options)  {
        this.initialize(element, options);
    };

    Cwizard.prototype = {
        constructor: Cwizard,

        initialize: function(element, options) {
            this.$element = $(element);
            this.options = $.extend({}, $.fn.cwizard.defaults, options);
            this.$element.carousel({pause: true});
            this.$element.carousel("pause");
            this.listen();
            this.titles = {};
            $('input:text:visible:first').focus();
        },

        listen: function() {
            $(".next").on("click", $.proxy(this.next, this));
            $(".prev").on("click", $.proxy(this.prev, this));
            $(".submit").on("click", $.proxy(this.submit, this));
        },

        get_current_step_id: function() {
            return $(".item.active").attr("id");
        },

        get_current_title: function() {
            return $(".modal-header").find("small").html();
        },

        set_current_title: function(title) {
            $(".modal-header").find("small").html(title);
        },

        post: function(last, target) {
            var $form = (this.options.formid) ? $('#' + this.options.formid) : $('form');
            var data = $form.serialize() + "&stepid=" + this.get_current_step_id() + "&target=" + target;

            $.ajax({
                type: 'POST', url: $form.attr("action"), data: data, global: false
            }).done($.proxy(function(resp) {
                if (!last) {
                    $('input:text:visible:first').focus();
                    this.set_current_title(resp.title);
                    if (this.options.transition_callbacks[resp.id] !== undefined) {
                        this.options.transition_callbacks[resp.id]();
                    }
                    $(".carousel-inner").css("overflow", "hidden");
                    this.$element.carousel(resp.stepid);
                } else {
                    $("#modalbox").modal('hide');
                    if (this.options.success_callback !== undefined) {
                        this.options.success_callback(resp);
                    } else {
                        window.location.reload();
                    }
                }
            }, this)).fail($.proxy(function(jqxhr) {
                var resp = $.parseJSON(jqxhr.responseText);
                if (resp.stepid !== undefined) {
                    var stepid = resp.stepid;
                    display_form_errors("step" + stepid, resp);
                    if (this.options.error_callbacks[stepid] !== undefined) {
                        this.options.error_callbacks[stepid]();
                    }
                    $('input:text:visible:first').focus();
                    if (resp.respmsg) {
                        $(".modal-body").prepend(build_error_alert(resp.respmsg));
                    }
                    return;
                }
                $(".modal-body").prepend(build_error_alert(resp));
            }, this));
        },

        update_buttons: function() {
            $(".carousel-inner").css("overflow", "visible");
            $('.bset.active').removeClass("active");
            $("#" + $(".item.active").attr("id") + "_buttons").addClass("active");
        },

        next: function(evt) {
            evt.preventDefault();
            var step_id = this.get_current_step_id();
            this.titles[step_id] = this.get_current_title();
            this.$element.on('slid.bs.carousel', this.update_buttons);
            this.post(false, "next");
        },

        /**
         * Go back to the previous step.
         */
        prev: function(evt) {
            var stepid = this.get_current_step_id();

            evt.preventDefault();
            this.$element.on('slid.bs.carousel', this.update_buttons);
            this.post(false, "prev", stepid);
        },

        submit: function(evt) {
            evt.preventDefault();
            this.post(true, "next");
        }
    };

    $.fn.cwizard = function(method) {
        return this.each(function() {
            var $this = $(this),
                data = $this.data('cwizard'),
                options = typeof method === "object" && method;

            if (!data) {
                $this.data('cwizard', new Cwizard(this, options));
            }
            if (typeof method === "string") {
                data[method]();
            }
        });
    };

    $.fn.cwizard.defaults = {
        transition_callbacks: {},
        error_callbacks: {}
    };

})(jQuery);
