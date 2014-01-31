var Graphic = function(data, options) {
    this.initialize(data, options);
};

Graphic.prototype = {
    constructor: Graphic,

    defaults: {

    },

    initialize: function(data, options) {
        this.options = $.extend({}, this.defaults, options);
        this.graphics = {};
        this.setup(data);
        $(window).resize($.proxy(this.resize_graphics, this));
    },

    setup: function(data) {
        $.each(data.graphs, $.proxy(function(id, graph) {
            var chart = new Rickshaw.Graph({
                element: document.getElementById(id),
                renderer: 'area',
                stroke: true,
                series: graph,
                height: 350
            });

            var preview = new Rickshaw.Graph.RangeSlider.Preview({
                graph: chart,
	        element: document.getElementById(id + '_preview')
            });

            var xAxis = new Rickshaw.Graph.Axis.Time({
                graph: chart,
                ticksTreatment: 'glow'
            });

            var yAxis = new Rickshaw.Graph.Axis.Y({
                graph: chart
            });

            var previewXAxis = new Rickshaw.Graph.Axis.Time({
                graph: preview.previews[0],
	        /*timeFixture: new Rickshaw.Fixtures.Time.Local(),*/
	        ticksTreatment: 'glow'
            });

            var hoverDetail = new Rickshaw.Graph.HoverDetail( {
                graph: chart,
	        xFormatter: function(x) {
		    return new Date(x * 1000).toString();
	        }
            });

            var legend = new Rickshaw.Graph.Legend({
                graph: chart,
                element: document.getElementById(id + '_legend')
            });

            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: chart,
                legend: legend
            });

            chart.render();
            xAxis.render();
            yAxis.render();
            previewXAxis.render();

            this.graphics[id] = {
                chart: chart, preview: preview
            };
        }, this));
    },

    resize_graphics: function(e) {
        $.each(this.graphics, function(id, graphic) {
            var w = $('#' + id).parent().width();
            $.each(graphic, function(id, object) {
                object.configure({width: w});
                object.render();
            });
        });
    },

    update: function(data) {
        $.each(data.graphs, $.proxy(function(id, graph) {
            var $parent = $('#' + id).parent();
            $('#' + id).remove();
            $('#' + id + '_legend').remove();
            $('#' + id + '_preview').remove();
            $parent.append($("<div />", {id: id}));
            $parent.append($("<div />", {id: id + '_preview'}));
            $parent.append($("<div />", {id: id + '_legend', 'class': 'legend'}));
        }, this));
        this.setup(data);
    }
};
