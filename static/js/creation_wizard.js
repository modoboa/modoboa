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
            $('input:text:visible:first').focus();
        },

        listen: function() {
            $(".next").on("click", $.proxy(this.next, this));
            $(".prev").on("click", $.proxy(this.prev, this));
            $(".submit").on("click", $.proxy(this.submit, this));
        },

        post: function(last) {
            var $form = (this.options.formid) ? $('#' + this.options.formid) : $('form');
            var data = $form.serialize() + "&stepid=" + $(".item.active").attr("id");

            $.post($form.attr("action"), data, $.proxy(function(resp) {
                if (resp.status == "ok") {
                    if (!last) {
                        var stepid = resp.stepid + 1;
                        $('input:text:visible:first').focus();
                        $(".modal-header").find("small").html(resp.title);
                        if (this.options.transition_callbacks[stepid] != undefined) {
                            this.options.transition_callbacks[stepid]();
                        }
                        this.$element.carousel('next');
                    } else {
                        $("#modalbox").modal('hide').remove();
                        window.location.reload();
                    }
                    return;
                }
                if (resp.stepid != undefined && resp.form != undefined) {
                    var stepid = resp.stepid + 1;                    
                    $("#step" + stepid).html(resp.form);
                    if (this.options.error_callbacks[stepid] != undefined) {
                        this.options.error_callbacks[stepid]();
                    }
                    $('input:text:visible:first').focus();
                }
                if (resp.respmsg) {
                    $(".modal-body").prepend(build_error_alert(resp.respmsg));
                }
            }, this));
        },

        update_buttons: function() {
            $('.bset.active').removeClass("active");
            $("#" + $(".item.active").attr("id") + "_buttons").addClass("active");
        },

        next: function(evt) {
            evt.preventDefault();
            this.$element.on('slid', this.update_buttons);
            this.post(false);
        },

        prev: function(evt) {
            evt.preventDefault();
            this.$element.on('slid', this.update_buttons);
            this.$element.carousel('prev');
            this.listen();
        },

        submit: function(evt) {
            evt.preventDefault();
            this.post(true);
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

    };

})(jQuery);