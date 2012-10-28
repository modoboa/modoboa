var Stats = function(options) {
    this.initialize(options);
};

Stats.prototype = {
    constructor: Stats,

    defaults: {
        deflocation: "graphs/?view=global"
    },

    initialize: function(options) {
        this.options = $.extend({}, this.defaults, options);
        this.options.defcallback = $.proxy(this.graphs_cb, this);

        var navobj = new History(this.options);
        this.navobj = navobj;

        if (navobj.params.view != undefined) {
            $("#searchquery").attr("value", navobj.params.view);
        }
        $("#searchquery").focus(function() {
            $(this).attr("value", "");
        }).blur(function() {
            var $this = $(this);
            if ($this.attr("value") == "") {
                if (navobj.params["view"] == "global") {
                    $this.attr("value", gettext("Search a domain"));
                } else {
                    $this.attr("value", navobj.params.view);
                }
            }
        });
        if (navobj.params.start) {
            $("#id_from").attr("value", navobj.params.start);
        }
        if (navobj.params.end) {
            $("#id_to").attr("value", navobj.params.end);
        }
        $("#custom-period input").datepicker({
            format: 'yyyy-mm-dd'
        });

        this.register_nav_callbacks();
        this.listen();
    },

    listen: function() {
        $("#searchform").on("keypress", $.proxy(this.search_domain, this));
        $(".period_selector").click($.proxy(this.change_period, this));
        $("#customsend").on("click", $.proxy(this.customgraphs, this));
    },

    register_nav_callbacks: function() {
        this.navobj.register_callback("graphs",
            $.proxy(this.graphs_cb, this));
    },

    change_period: function(e) {
        e.preventDefault();
        var $link = $(e.target);

        this.navobj.delparam("start").delparam("end");
        this.navobj.setparam("period", $link.attr("data-period")).update();
    },

    graphs_cb: function(data) {
        if (data.status == "ko") {
            $("body").notify("error", data.respmsg);
            return;
        }
        $("#graphs_mailstats").html(data.content);
    },

    search_domain: function(e) {
        var $input = $(e.target);

        switch (e.which) {
        case 13:
            e.preventDefault();
            var domain = ($input.attr("value") == "") ? "global" : $input.attr("value");
            this.navobj.setparam("view", domain).update();
            break;
        }
    },

    customgraphs: function(e) {
        e.preventDefault();
        var $fromdate = $("#id_from");
        var $todate = $("#id_to");

        if ($fromdate.attr("value") == "" || $todate.attr("value") == "") {
            return;
        }
        this.navobj.setparams({
            period: "custom",
            start: $fromdate.attr("value"),
            end: $todate.attr("value")
        }).update();
    }
};
