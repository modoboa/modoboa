/*
 *
 */
var Graphic = function(selector, options) {
    this.initialize(selector, options);
};

Graphic.prototype = {
    constructor: Graphic,

    defaults: {
        height: 300,
        preview_height: 80,
        brush_height: 7,
        margin: {
            left: 40,
            top: 10,
            bottom: 20
        }
    },

    initialize: function(selector, data, options) {
        this.options = $.extend({}, this.defaults, options);
        this.selector = selector;
        this.data = data;
        $(window).resize($.proxy(this.resize, this));
        this.render();
    },

    resize: function() {
        d3.selectAll("svg").remove();
        this.render();
    },

    height: function() {
        return this.options.height + 2 * this.options.margin.top 
            + 2 * this.options.margin.bottom + this.options.preview_height
            + this.options.brush_height;
    },

    render: function() {
        var $element = $(this.selector);
        var width = $element.width();
        var container = d3.select(this.selector)
            .append("div")
            .attr("class", "chart");
        var svg = container
            .append("svg")
            .attr("width", width)
            .attr("height", this.height());

        svg.append("defs").append("clipPath")
            .attr("id", "clip")
            .append("rect")
            .attr("width", width - 2 * this.options.margin.left)
            .attr("height", this.options.height);
    
        var x = d3.time.scale().range([0, width - 2 * this.options.margin.left]),
            x2 = d3.time.scale().range([0, width - 2 * this.options.margin.left]);
        var xAxis = d3.svg.axis().scale(x).orient("bottom"),
            xAxis2 = d3.svg.axis().scale(x2).orient("bottom");
        var y = d3.scale.linear().range([this.options.height, 0]),
            y2 = d3.scale.linear().range([this.options.preview_height, 0]);

        
        var brush = d3.svg.brush()
            .x(x2)
            .on("brush", brushed);
        
        x.domain(d3.extent(this.data[0].data.map(function(d) { return d.x * 1000; })));
        y.domain([
            d3.min(this.data, function(d) { return d3.min(d.data, function(v) { return v.y; }); }),
            d3.max(this.data, function(d) { return d3.max(d.data, function(v) { return v.y; }); })
        ]);
        x2.domain(x.domain());
        y2.domain(y.domain());

        var yAxis = d3.svg.axis().scale(y).orient("left");

        var area = d3.svg.area()
            .interpolate("cardinal")
            .x(function(d) { return x(d.x * 1000); })
            .y0(this.options.height)
            .y1(function(d) { return y(d.y); });

        var area2 = d3.svg.area()
            .interpolate("cardinal")
            .x(function(d) { return x2(d.x * 1000); })
            .y0(this.options.preview_height)
            .y1(function(d) { return y2(d.y); });

        var focus = svg.append("g")
            .attr("class", "focus")
            .attr("transform",
                  "translate(" + this.options.margin.left + ",0)");// + this.options.margin.top * 2 + ")");

        var context = svg.append("g")
            .attr("class", "context")
            .attr("transform", "translate(" + this.options.margin.left + "," + (this.options.height + this.options.margin.top + this.options.margin.bottom + this.options.brush_height) + ")");

        var curve2 = context.selectAll(".curve")
            .data(this.data)
            .enter().append("g")
                .attr("class", "curve");

        var curvegroup = focus.append("g")
            .attr('clip-path', 'url(#clip)');

        var curve = curvegroup.selectAll(".curve")
            .data(this.data)
            .enter().append("g")
            .attr("class", "curve");

        curve.append("path")
            .attr("class", "area")
            .attr("d", function(d) { 
                return area(d.data);
            })
            .attr("data-legend", function(d) { return d.name; })
            .attr("stroke", function(d) { return d.color; })
            .attr("stroke-width", "3px")
            .attr("stroke-opacity", 0.8)
            .style("fill", function(d) { return d.color; });

        function make_x_axis() {
            return d3.svg.axis()
                .scale(x)
                .orient("bottom")
                .ticks(5)
                .tickSize(-this.options.height, 0, 0)
                .tickFormat("");
        }

        function make_y_axis() {
            return d3.svg.axis()
                .scale(y)
                .orient("left")
                .ticks(5)
                .tickSize(-(width - 2 * this.options.margin.left), 0, 0)
                .tickFormat("");
        }

        focus.append("g")
            .attr("class", "grid")
            .attr("transform", "translate(0," + (this.options.height + this.options.margin.top) + ")")
            .call(make_x_axis.apply(this));

        focus.append("g")         
            .attr("class", "grid")
            .call(make_y_axis.apply(this));

        focus.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + this.options.height + ")")
            .call(xAxis);
        focus.append("g")
            .attr("class", "y axis")
            .call(yAxis);

        var tooltip = d3.select(".chart")
            .append("div")
            .attr("class", "remove")
            .style("position", "absolute")
            .style("z-index", "20")
            .style("display", "none")
            .style("top", "0px")
            .style("right", "10px");

        var datearray = [];

        focus.selectAll(".area")
            .on("mousemove", function(d) {
                var mousex = d3.mouse(this)[0];
                var date = x.invert(mousex);

                for (var k = 0; k < d.data.length; k++) {
                    datearray[k] = x.invert(d.data[k].x).value;
                }
                var mousedate = datearray.indexOf(date.value);
                var pro = d.data[mousedate].y;

                tooltip.html( "<p>" + date + "<br>" + pro + "</p>" )
                        .style("display", "block");
            });

        var legend = focus.append("g")
            .attr("class", "legend")
            .attr("transform", "translate(50,30)")
            .style("font-size", "12px")
            .call(d3.legend);

        curve2.append("path")
            .attr("class", "area2")
            .attr("d", function(d) { return area2(d.data); })
            .attr("stroke", function(d) { return d.color; })
            .attr("stroke-width", "2px")
            .attr("stroke-opacity", 0.8)
            .style("fill", function(d) { return d.color; });

        context.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + this.options.preview_height + ")")
            .call(xAxis2);

        context.append("g")
            .attr("class", "x brush")
            .call(brush)
            .selectAll("rect")
            .attr("y", -6)
            .attr("height", this.options.preview_height + this.options.brush_height);

        function brushed() {
            x.domain(brush.empty() ? x2.domain() : brush.extent());
            focus.selectAll(".area")
                .attr("d", function(d) { return area(d.data); });
            focus.select(".x.axis").call(xAxis);
        }
    }
};

/*
 *
 */
var GraphicSet = function(selector, data, options) {
    this.initialize(selector, data, options);
};

GraphicSet.prototype = {
    constructor: GraphicSet,

    initialize: function(selector, data, options) {
        var graph = new Graphic(selector, data.graphs.averagetraffic, options);
    }

};
