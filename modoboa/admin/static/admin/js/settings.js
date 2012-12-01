var Settings = function(options) {
    this.initialize(options);
};

Settings.prototype = {
    constructor: Settings,

    defaults: {
        deflocation: "parameters/"
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
                formid: "settings_form",
                reload_on_success: false,
                success_cb: $.proxy(this.save_cb, this)
            });
        }, this));
    },

    save_cb: function(data) {
        if (this.navobj.getbaseurl() == 'extensions') {
            window.location.reload();
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
        $("#settings_content").html(data.content);
    }
};