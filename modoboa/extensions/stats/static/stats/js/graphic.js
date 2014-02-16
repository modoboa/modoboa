/**
 * Creates an instance of ModoChart.
 * 
 * @constructor
 * @this {ModoChart}
 * @param {string} selection add chart to this DOM element.
 * 
 */
function ModoChart(selection) {
    var width = 0,
        height = 300,
        preview_height = 80,
        brush_height = 7,
        margin = {
            left: 50,
            top: 10,
            bottom: 20
        };
    var container;

    /**
     * Create and render the chart.
     *
     * @this {ModoChart}
     * @param {Object} data chart's data.
     */
    function my(data) {
        container = d3.select(selection)
            .append("div")
            .attr("class", "chart");

        container.append("h6").html(data.title);
        width = $(selection).width();

        var svg = container
            .append("svg")
            .attr("width", width)
            .attr("height", my.totalHeight());

        svg.append("defs").append("clipPath")
            .attr("id", "clip")
            .append("rect")
            .attr("width", width - 2 * margin.left)
            .attr("height", height + margin.top + margin.bottom);

        var x = d3.time.scale().range([0, width - 2 * margin.left]),
            x2 = d3.time.scale().range([0, width - 2 * margin.left]);
        var xAxis = d3.svg.axis().scale(x).orient("bottom"),
            xAxis2 = d3.svg.axis().scale(x2).orient("bottom");
        var y = d3.scale.linear().range([height, 0]),
            y2 = d3.scale.linear().range([preview_height, 0]);
        var yAxis = d3.svg.axis().scale(y).orient("left");
        var bisectDate = d3.bisector(function(d) { return d.x * 1000; }).left;

        var brush = d3.svg.brush()
            .x(x2)
            .on("brush", brushed);

        x.domain(
            d3.extent(data.curves[0].data.map(function(d) { return d.x * 1000; }))
        );
        y.domain(
            [d3.min(data.curves, function(d) { return d3.min(d.data, function(v) { return v.y; }); }),
             d3.max(data.curves, function(d) { return d3.max(d.data, function(v) { return v.y; }); })
            ]
        );
        x2.domain(x.domain());
        y2.domain(y.domain());

        var area = d3.svg.area()
            .interpolate("monotone")
            .x(function(d) { return x(d.x * 1000); })
            .y0(height)
            .y1(function(d) { return y(d.y); });
        var area2 = d3.svg.area()
            .interpolate("monotone")
            .x(function(d) { return x2(d.x * 1000); })
            .y0(preview_height)
            .y1(function(d) { return y2(d.y); });

        var focus = svg.append("g")
            .attr("class", "focus")
            .attr("width", width - 2 * margin.left)
            .attr("height", height)
            .attr("pointer-events", "all")
            .attr("transform",
                  "translate(" + margin.left + "," + margin.top + ")");
        var context = svg.append("g")
            .attr("class", "context")
            .attr("transform", "translate(" + margin.left + "," + (height + margin.top + margin.bottom + brush_height) + ")");

        var curvegroup = focus.append("g")
            .attr('clip-path', 'url(#clip)');
        var curve = curvegroup.selectAll(".curve")
            .data(data.curves)
            .enter().append("g")
            .attr("class", "curve");
        var curve2 = context.selectAll(".curve")
            .data(data.curves)
            .enter().append("g")
                .attr("class", "curve");

        /* Vertical line */
        var line = focus.append("line")
            .attr("class", "line_over")
            .attr("x1", 0)
            .attr("y1", 0)
            .attr("x2", 0)
            .attr("y2", height);

        /* Custom rectangle to catch mouse events */
        var rect = focus.append("rect")
            .attr("fill", "none")
            .attr("width", width - 2 * margin.left)
            .attr("height", height);

        var tooltip = container
            .append("div")
            .attr("class", "remove")
            .attr("class", "tip");

        var points = [];

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

        var xrules = make_x_axis();

        focus.append("g")
            .attr("class", "grid")
            .attr("transform", "translate(0," + height + ")")
            .call(xrules);
        focus.append("g")         
            .attr("class", "grid")
            .call(make_y_axis);
        focus.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis);
        focus.append("g")
            .attr("class", "y axis")
            .call(yAxis);

        rect.on("mouseover", function(d) {
            line.style("display", "block");
            tooltip.style("display", "block");
            data.curves.forEach(function(d, cid) {
                var display = d3.selectAll("[data-legend='" + d.name + "']")
                    .style("display");
                if (display == "none") {
                    return;
                }
                focus.select(".tracker-" + cid).style("display", "block");    
            });
        }).on("mousemove", function(d) {
            var mousex = d3.mouse(this)[0],
                mousey = d3.mouse(this)[1];
            var date = x.invert(mousex);
            var text = "";

            line.attr("x1", mousex).attr("x2", mousex);
            data.curves.forEach(function(d, cid) {
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
            if (mousex + tooltip[0][0].clientWidth >= width - 2 * margin.left) {
                var left = mousex - (tooltip[0][0].clientWidth - (margin.left - 20));
                tooltip.style("left", left + "px");
            } else {
                tooltip.style("left", (mousex + margin.left + 20) + "px");
            }
            tooltip.html("<p>" + date + "</p>" + text);
        }).on("mouseout", function(d) {
            tooltip.style("display", "none");
            line.style("display", "none");
            focus.selectAll(".tracker").style("display", "none");
        });

        var legend = focus.append("g")
            .attr("class", "legend")
            .attr("transform", "translate(50,10)")
            .style("font-size", "0.8em")
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
            .attr("transform", "translate(0," + preview_height + ")")
            .call(xAxis2);

        context.append("g")
            .attr("class", "grid")
            .attr("transform", "translate(0," + preview_height + ")")
            .call(make_preview_x_axis);

        context.append("g")
            .attr("class", "x brush")
            .call(brush)
            .selectAll("rect")
            .attr("y", -6)
            .attr("height", preview_height + brush_height);

        function make_x_axis() {
            return d3.svg.axis()
                .scale(x)
                .orient("bottom")
                .ticks(6)
                .tickSize(-height, 0, 0)
                .tickFormat("");
        }

        function make_y_axis() {
            return d3.svg.axis()
                .scale(y)
                .orient("left")
                .ticks(6)
                .tickSize(-(width - 2 * margin.left), 0, 0)
                .tickFormat("");
        }

        function make_preview_x_axis() {
            return d3.svg.axis()
                .scale(x2)
                .orient("bottom")
                .ticks(6)
                .tickSize(-preview_height, 0, 0)
                .tickFormat("");
        }

        function brushed() {
            x.domain(brush.empty() ? x2.domain() : brush.extent());
            focus.selectAll(".area")
                .attr("d", function(d) { return area(d.data); });
            focus.select(".x.axis").call(xAxis);
            focus.select(".grid").call(xrules);
        }
    }

    /**
     * Set or get chart's width.
     * 
     * @this {ModoChart}
     * @param {integer} value new width.
     * @return {number} current width.
     */
    my.width = function(value) {
        if (!arguments.length) return width;
        width = value;
        return my;
    };

    /**
     * Set or get chart's height.
     * 
     * @this {ModoChart}
     * @param {integer} value new height.
     * @return {number} current height.
     */
    my.height = function(value) {
        if (!arguments.length) return height;
        height = value;
        return my;
    };

    /**
     * Set or get chart's margin.
     * 
     * @this {ModoChart}
     * @param {Object} value new margin.
     * @return {Object} current margin.
     */
    my.margin = function(value) {
        if (!arguments.length) return margin;
        margin = value;
        return my;
    };

    /**
     * Compute and return chart's total height.
     * 
     * @this {ModoChart}
     * @return {integer} total height.
     */
    my.totalHeight = function() {
        return height + 2 * margin.top 
            + 2 * margin.bottom + preview_height
            + brush_height;
    };

    /**
     * Update the chart with new data.
     *
     * @this {ModoChart}
     * @param {Object} data new data
     */
    my.update = function(data) {
        container.select("svg").remove();
        $(container[0][0]).empty();
        my(data);
    };

    return my;
}
