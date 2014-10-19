/**
 * Create an instance of Stats.
 *
 * @constructor
 */
var Stats = function(options) {
    this.initialize(options);
};

Stats.prototype = {
    constructor: Stats,

    defaults: {
        deflocation: "graphs/",
        language: "en",
        domain_list_url: null
    },

    initialize: function(options) {
        this.options = $.extend({}, this.defaults, options);
        this.options.defcallback = $.proxy(this.charts_cb, this);

        var navobj = new History(this.options);
        this.navobj = navobj;

        if (navobj.params.searchquery !== undefined) {
            $("#searchquery").val(navobj.params.searchquery);
        }
        $("#searchquery").focus(function() {
            var $this = $(this);
            if ($this.val() === undefined) {
                return;
            }
            $this.data("oldvalue", $this.val());
            $this.val("");
        }).blur(function() {
            var $this = $(this);
            if ($this.val() === "") {
                if ($this.data("oldvalue")) {
                    $this.val($this.data('oldvalue'));
                    $this.data("oldvalue", null);
                } else {
                    $this.val(gettext("Search a domain"));
                }
            }
        });
        if (navobj.params.start) {
            $("#id_from").val(navobj.params.start);
        }
        if (navobj.params.end) {
            $("#id_to").val(navobj.params.end);
        }
        if (navobj.params.period) {
            $("input[data-period={0}]".format(navobj.params.period))
                .attr("checked", true)
                .parent().addClass("active");
            if (navobj.params.period == "custom") {
                $("#custom_period").removeClass("hidden");
            }
        }
        $("#custom-period .datetime_picker").datetimepicker({
            format: 'YYYY-MM-DD hh:mm:ss',
            language: this.options.language
        });
        $("#searchquery").autocompleter({
            choices: $.proxy(this.get_domain_list, this),
            choice_selected: $.proxy(this.search_domain, this),
            empty_choice: $.proxy(this.reset_search, this)
        });

        this.register_nav_callbacks();
        this.listen();
    },

    listen: function() {
        $(".period_selector").click($.proxy(this.change_period, this));
        $("#customsend").on("click", $.proxy(this.custom_period, this));
        $(window).resize($.proxy(this.resize_charts, this));
    },

    register_nav_callbacks: function() {
        this.navobj.register_callback("graphs",
            $.proxy(this.charts_cb, this));
    },

    /**
     * Retrieve a list of domain from the server.
     */
    get_domain_list: function() {
        var result;

        $.ajax({
            url: this.options.domain_list_url,
            dataType: "json",
            async: false
        }).done(function(data) {
            result = data;
        });
        return result;
    },

    change_period: function(e) {
        e.preventDefault();
        var $link = $(e.target).children("input");
        var period = $link.attr("data-period");

        if (period != "custom") {
            $("#custom_period").addClass("hidden");
            this.navobj.delparam("start").delparam("end");
            this.navobj.setparam("period", $link.attr("data-period")).update();
        } else {
            $("#custom_period").removeClass("hidden");
        }
    },

    /**
     * Update all charts on resize event.
     *
     * @this {Stats}
     */
    resize_charts: function() {
        var data = this.data;
        $.each(this.charts, function(id, mychart) {
            mychart.update(data.graphs[id]);
        });
    },

    /**
     * Create or update charts.
     *
     * @this {Stats}
     * @param {Object} data
     */
    charts_cb: function(data) {
        var menuid = "menu_" + this.navobj.getparam("gset");

        $("#" + menuid).addClass("active");
        this.data = data;
        if (this.charts !== undefined) {
             $.each(this.charts, function(id, mychart) {
                 mychart.update(data.graphs[id]);
             });
        } else {
            this.charts = {};
            $.each(data.graphs, $.proxy(function(id, graphdef) {
                var mychart = ModoChart("#gset");
                this.charts[id] = mychart;
                mychart(graphdef);
            }, this));
        }
    },

    search_domain: function(value) {
        this.navobj.setparam("searchquery", value).update();
    },

    reset_search: function() {
        $("#searchquery").data("oldvalue", null);
        this.navobj.delparam("searchquery").update();
    },

    custom_period: function(e) {
        e.preventDefault();
        var $fromdate = $("#id_from");
        var $todate = $("#id_to");

        if ($fromdate.val() === "" || $todate.val() === "") {
            return;
        }
        this.navobj.setparams({
            period: "custom",
            start: $fromdate.val(),
            end: $todate.val()
        }).update();
    }
};
