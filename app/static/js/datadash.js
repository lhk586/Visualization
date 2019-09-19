

// var Year = [1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006]
// var consumption = [10.027993, 9.818009, 9.60813, 9.398355, 9.188686, 8.979121, 8.76966, 4]

// var data = Year.map((d, i) => [d, consumption[i]])
// data = d3.csv.parse(data)
// const initData = JSON.parse(JSON.stringify(data));

// data = JSON.parse(data)
// console.log(data)
// initData = JSON.parse(JSON.stringify(data))

const width = 800
const height = 600
const padding = 60

const N = 5
const nTop = 2
// const nBottom = 0.5

var minX;
var maxX;
var minY;
var maxY;

var xScale;
var yScale;
var line;
var last;
var invm;

minX = d3.min(data, (d) => d[0])
console.log("minX:", minX)
maxX = d3.max(data, (d) => d[0])
console.log("maxX:", maxX)
minY = d3.min(data, (d) => d[1])
maxY = d3.max(data, (d) => d[1])


var svg = d3.select("#User")
    .append("svg")
    .attr("width", width)
    .attr("height", height)
    .attr('transform', 'translate(10,5)')
    .style("border", "1px dashed black")
    .style("margin-left", "10px")
    .on("mousedown", mousedown)
    .on("mousemove", mousemove);

var xSlider;
xSlider = d3
    .sliderBottom()
    .min(minX)
    .max(maxX + N)
    .width(300)
    .tickFormat(d3.format('d'))
    .ticks(5)
    .step(1)
    .default(maxX)
    .fill('#2196f3')
    .on('onchange', val => draw(val, ySlider.value(), svg));

var gX= d3
    .select('div#x-slider-range')
    .append('svg')
    .attr('width', 500)
    .attr('height', 100)
    .append('g')
    .attr('transform', 'translate(30,30)');

gX.call(xSlider);

var ySlider;
ySlider = d3
    .sliderBottom()
    .min(0)
    .max(maxY * nTop)
    .width(300)
    .ticks(5)
    .step(0.5)
    .default([minY, maxY])
    .fill('#2196f3')
    .on('onchange', val => draw(xSlider.value(), val, svg));

var gY = d3
    .select('div#y-slider-range')
    .append('svg')
    .attr('width', 500)
    .attr('height', 100)
    .append('g')
    .attr('transform', 'translate(30,30)');

gY.call(ySlider)

last = data[data.length-1]
draw(xSlider.value(), ySlider.value(), svg)

function draw(xSliderValue, ySliderValue, svg) {
    console.log(data)
    svg.selectAll("*").remove();
    xScale = d3.scaleLinear()
        .domain([minX, xSliderValue])
        .range([padding, width - padding]);

    yScale = d3.scaleLinear()
        .domain([ySliderValue[0], ySliderValue[1]])
        .range([height - padding, padding]);

    const xAxis = d3.axisBottom(xScale).tickFormat(d3.format("d"));
    const yAxis = d3.axisLeft(yScale);

    svg.append("g")
        .attr("transform", "translate(0," + (height - padding) + ")")
        .call(xAxis)
        .selectAll("text")
        .attr("y", 0)
        .attr("x", 25)
        .attr("dy", ".5em")
        .attr("transform", "rotate(90)")
        .attr("font-size", "12px")
        .attr("text-anchor", "start");

    svg.append("g")
        .attr("transform", "translate(" + (padding) + "," + "0)")
        .call(yAxis)
        .attr("font-size", "12px");

    svg.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "steelblue")
        .attr("stroke-width", 1.5)
        .attr("d", d3.line()
            .x(function(d) { return xScale(d[0]) })
            .y(function(d) { return yScale(d[1]) })
        )

    line = svg.append("line")
        .attr("stroke", "steelblue")
        .attr("x1", xScale(last[0]))
        .attr("y1", yScale(last[1]))
        .attr("x2", xScale(last[0]))
        .attr("y2", yScale(last[1]));

}

function mousedown() {
    var m = d3.mouse(this);
    if (!(m[0] < padding || m[0] > width - padding || m[1] < padding || m[1] > height - padding)) {
        last = [xScale.invert(m[0]), yScale.invert(m[1])]
        data.push(last)
        draw(xSlider.value(), ySlider.value(), svg)
    }
}

function mousemove() {
    var m = d3.mouse(this);
    invm = [xScale.invert(m[0]), yScale.invert(m[1])]
    if (m[0] < padding || m[0] > width - padding || m[1] < padding || m[1] > height - padding) {
        $("#x-value").text("None")
        $("#y-value").text("None")
        line.attr("x1", xScale(last[0]))
            .attr("y1", yScale(last[1]))
            .attr("x2", xScale(last[0]))
            .attr("y2", yScale(last[1]));
    }
    else {
        $("#x-value").text(invm[0])
        $("#y-value").text(invm[1])

        line.attr("x1", xScale(last[0]))
            .attr("y1", yScale(last[1]))
            .attr("x2", m[0])
            .attr("y2", m[1]);
    }

}

$('#reset').click(function(){
    xSlider.value(maxX);
    ySlider.value([minY, maxY]);
    data = JSON.parse(JSON.stringify(initData));
    last = data[data.length-1]
    draw(xSlider.value(), ySlider.value(), svg)
});
