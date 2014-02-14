/*
 *
 */
var Graphic = function(selector, data, options) {
    this.initialize(selector, data, options);
};

Graphic.prototype = {
    constructor: Graphic,

    defaults: {
        height: 300,
        preview_height: 80,
        brush_height: 7,
        margin: {
            left: 50,
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
        this.remove();
        this.render();
    },

    remove: function() {
        this.container.select("svg").remove();
        $(this.container[0][0]).empty();
    },

    height: function() {
        return this.options.height + 2 * this.options.margin.top 
            + 2 * this.options.margin.bottom + this.options.preview_height
            + this.options.brush_height;
    },

    render: function() {
        var $element = $(this.selector);
        var width = $element.width();
        this.container = d3.select(this.selector)
            .append("div")
            .attr("class", "chart");
        this.container.append("h6")
            .html(this.data.title);
        var svg = this.container
            .append("svg")
            .attr("width", width)
            .attr("height", this.height());

        svg.append("defs").append("clipPath")
            .attr("id", "clip")
            .append("rect")
            .attr("width", width - 2 * this.options.margin.left)
            .attr("height", this.options.height + 30);
    
        var x = d3.time.scale().range([0, width - 2 * this.options.margin.left]),
            x2 = d3.time.scale().range([0, width - 2 * this.options.margin.left]);
        var xAxis = d3.svg.axis().scale(x).orient("bottom"),
            xAxis2 = d3.svg.axis().scale(x2).orient("bottom");
        var y = d3.scale.linear().range([this.options.height, 0]),
            y2 = d3.scale.linear().range([this.options.preview_height, 0]);
        var bisectDate = d3.bisector(function(d) { return d.x * 1000; }).left;

        var brush = d3.svg.brush()
            .x(x2)
            .on("brush", brushed);

        var points = [];
        
        x.domain(d3.extent(this.data.curves[0].data.map(function(d) { return d.x * 1000; })));
        y.domain([
            d3.min(this.data.curves, function(d) { return d3.min(d.data, function(v) { return v.y; }); }),
            d3.max(this.data.curves, function(d) { return d3.max(d.data, function(v) { return v.y; }); })
        ]);
        x2.domain(x.domain());
        y2.domain(y.domain());

        var yAxis = d3.svg.axis().scale(y).orient("left");

        var area = d3.svg.area()
            .interpolate("monotone")
            .x(function(d) { return x(d.x * 1000); })
            .y0(this.options.height)
            .y1(function(d) { return y(d.y); });

        var area2 = d3.svg.area()
            .interpolate("monotone")
            .x(function(d) { return x2(d.x * 1000); })
            .y0(this.options.preview_height)
            .y1(function(d) { return y2(d.y); });

        var focus = svg.append("g")
            .attr("class", "focus")
            .attr("width", width - 2 * this.options.margin.left)
            .attr("height", this.options.height)
            .attr("pointer-events", "all")
            .attr("transform",
                  "translate(" + this.options.margin.left + "," + this.options.margin.top + ")");

        var context = svg.append("g")
            .attr("class", "context")
            .attr("transform", "translate(" + this.options.margin.left + "," + (this.options.height + this.options.margin.top + this.options.margin.bottom + this.options.brush_height) + ")");

        var curve2 = context.selectAll(".curve")
            .data(this.data.curves)
            .enter().append("g")
                .attr("class", "curve");

        var curvegroup = focus.append("g")
            .attr('clip-path', 'url(#clip)');

        var curve = curvegroup.selectAll(".curve")
            .data(this.data.curves)
            .enter().append("g")
            .attr("class", "curve");

        var line = focus.append("line")
            .attr("class", "line_over")
            .attr("x1", 0)
            .attr("y1", 0)
            .attr("x2", 0)
            .attr("y2", this.options.height);

        var rect = focus.append("rect")
            .attr("fill", "none")
            .attr("width", width - 2 * this.options.margin.left)
            .attr("height", this.options.height);

        var tooltip = this.container
            .append("div")
            .attr("class", "remove")
            .attr("class", "tip");

        var path = curve.append("path")
            .attr("class", "area")
            .attr("d", function(d, i) {
                var path = this;

                points[path] = {};
                d.data.forEach(function(d) {
                    points[path][d.x] = d.y;
                });
                focus.append("circle")
                    .attr("class", "tracker tracker-" + i)
                    .attr("r", 4);
                return area(d.data);
            })
            .attr("data-legend", function(d) { return d.name; })
            .attr("stroke", function(d) { return d.color; })
            .attr("stroke-width", "2px")
            .attr("stroke-opacity", 0.8)
            .style("fill", function(d) { return d.color; });

        function make_x_axis() {
            return d3.svg.axis()
                .scale(x)
                .orient("bottom")
                .ticks(6)
                .tickSize(-this.options.height, 0, 0)
                .tickFormat("");
        }

        function make_y_axis() {
            return d3.svg.axis()
                .scale(y)
                .orient("left")
                .ticks(6)
                .tickSize(-(width - 2 * this.options.margin.left), 0, 0)
                .tickFormat("");
        }

        var xrules = make_x_axis.apply(this);
        focus.append("g")
            .attr("class", "grid")
            .attr("transform", "translate(0," + (this.options.height) + ")")
            .call(xrules);

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

        var data = this.data.curves;
        rect
            .on("mouseover", function(d) {
                line.style("display", "block");
                tooltip.style("display", "block");
                data.forEach(function(d, cid) {
                    var display = d3.selectAll("[data-legend='" + d.name + "']")
                        .style("display");
                    if (display == "none") {
                        return;
                    }
                    focus.select(".tracker-" + cid).style("display", "block");    
                });
            })
            .on("mousemove", function(d) {
                var mousex = d3.mouse(this)[0],
                    mousey = d3.mouse(this)[1];
                var date = x.invert(mousex);
                var text = "";

                line.attr("x1", mousex)
                    .attr("x2", mousex);

                data.forEach(function(d, cid) {
                    var display = d3.selectAll("[data-legend='" + d.name + "']")
                        .style("display");
                    if (display == "none") {
                        return;
                    }
                    var i = bisectDate(d.data, date.getTime(), 1),
                        d0 = d.data[i - 1],
                        d1 = d.data[i],
                        point = date.getTime() - (d0.x * 1000) > (d1.x * 1000) - date.getTime() ? d1 : d0;
                    text += "<p>" + d.name + ": " + point.y.toFixed(3) + "</p>";

                    var tracker_x = x(point.x * 1000),
                        tracker_y = y(point.y);

                    focus.selectAll(".tracker-" + cid)
                        .style("fill", d.color)
                        .attr("cx", tracker_x)
                        .attr("cy", tracker_y);
                });
                if (mousex + tooltip[0][0].clientWidth >= width - 2 * 40) {
                    tooltip
                        .style("left", (mousex - (tooltip[0][0].clientWidth - 30)) + "px");
                } else {
                    tooltip.style("left", (mousex + 60) + "px");
                }
                tooltip.html("<p>" + date + "</p>" + text);
            })
            .on("mouseout", function(d) {
                tooltip.style("display", "none");
                line.style("display", "none");
                focus.selectAll(".tracker").style("display", "none");
            });

        var legend = focus.append("g")
            .attr("class", "legend")
            .attr("transform", "translate(50,10)")
            .style("font-size", "12px")
            .call(d3.legend);

        curve2.append("path")
            .attr("class", "area2")
            .attr("d", function(d) { return area2(d.data); })
            .attr("stroke", function(d) { return d.color; })
            .attr("stroke-width", "2px")
            .attr("stroke-opacity", 0.8)
            .attr("data-legend", function(d) { return d.name; })
            .style("fill", function(d) { return d.color; });

        context.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + this.options.preview_height + ")")
            .call(xAxis2);

        function make_preview_x_axis() {
            return d3.svg.axis()
                .scale(x2)
                .orient("bottom")
                .ticks(6)
                .tickSize(-this.options.preview_height, 0, 0)
                .tickFormat("");
        }

        context.append("g")
            .attr("class", "grid")
            .attr("transform", "translate(0," + (this.options.preview_height) + ")")
            .call(make_preview_x_axis.apply(this));

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
            focus.select(".grid").call(xrules);
        }
    }
};
