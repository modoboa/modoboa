var TwocolsNav = function(options) {
    this.initialize(options);
};

TwocolsNav.prototype = {
    constructor: TwocolsNav,

    defaults: {
        deflocation: null,
        formid: "#form",
        divid: "#content",
        reload_exceptions: null
    },

    initialize: function(options) {
        this.options = $.extend({}, this.defaults, options);
        this.options.defcallback = $.proxy(this.default_cb, this);
        this.navobj = new History(this.options);
        this.listen();
    },

    listen: function() {
        $("a.ajaxlink").click($.proxy(this.load_page, this));
        $(document).on("click", "#update", $.proxy(function(e) {
            simple_ajax_form_post(e, {
                formid: this.options.formid,
                modal: false,
                reload_on_success: false,
                error_cb: $.proxy(this.update_content, this),
                success_cb: $.proxy(this.save_cb, this)
            });
        }, this));
    },

    update_content: function(data) {
        if (data.content) {
            $('#' + this.options.divid).html(data.content);
        }
        if (data.onload_cb) {
            eval(data.onload_cb + '()');
        }
        if (data.respmsg) {
            $("body").notify("error", data.respmsg);
        }
        $('#' + this.options.divid + ' select').change($.proxy(this.select_change, this));
        $(".help").popover().click(function(e) {e.preventDefault();});
        $('#' + this.options.divid + ' select').change();
    },

    propagate_change: function($node) {
        var $select = $node.find("select");
        if ($select.length) {
            $select.change();
        }
    },

    select_change: function(e) {
        var instance = this;
        var $target = $(e.target);
        var $parent = $target.parents("div.control-group");

        $('div[data-visibility-field="' + $target.attr("id") + '"]').each(function(idx) {
            var $this = $(this);

            if ($parent.attr("disabled") === undefined && 
                $this.attr("data-visibility-value") == $target.attr("value")) {
                $this.attr("disabled", null);
                $this.show();
                instance.propagate_change($this)
            } else {
                $this.hide();
                $this.attr("disabled", "disabled");
                instance.propagate_change($this);
            }
        });
    },

    save_cb: function(data) {
        if (this.options.reload_exceptions) {
            for (var i = 0; i < this.options.reload_exceptions.length; i++) {
                if (this.navobj.getbaseurl() == this.options.reload_exceptions[i]) {
                    window.location.reload();
                    break;
                }
            }
        }
        $("body").notify("success", data.respmsg, 2000);
    },

    load_page: function(e) {
        var $link = get_target(e);
        e.preventDefault();
        this.navobj.baseurl($link.attr("href")).update();
    },

    default_cb: function(data) {
        $("a.ajaxlink").parent().removeClass("active");
        $("a[name=" + this.navobj.getbaseurl() + "]").parent().addClass("active");
        this.update_content(data);
    }
};