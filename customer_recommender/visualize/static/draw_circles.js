$(document).ready(function() {
        <!-- SINGLE BAR CHART -->
        var current_rating = 0;
        var current_review = 5;

        <!-- DRAW D3 Chart -->
        function drawCircles() {

            svg.selectAll("circle").remove();

            svg.selectAll("circle")

            .data(DataStore.getFilteredData())
                .enter()
                .append("a")
                .attr("xlink:href", function(d) {
                    return 'http://' + d.user;
                })
                .append("svg:circle")
                .attr("class", "circle")
                .attr("r", function(d) {
                    return 0;
                })
                .attr("cx", function(d, i) {
                    return Math.random() * width;
                })
                .attr("cy", function(d, i) {
                    return Math.random() *((i * radius) / width) * radius;
                })
                .style("fill", function(d) {
                    console.log(color(d.cluster));
                    return color(d.cluster);
                })
                .style("fill-opacity", .2)

            .transition()
                .duration(2000)
                .ease("linear")
                .attr("r", function(d) {
                    return d.avg_rating * Math.floor(radius/10);
                })
                .attr("cx", function(d, i) {
                    return (i * radius) % width;
                })
                .attr("cy", function(d, i) {
                    return Math.floor((i * radius) / width) * radius;
                })
                .style("fill-opacity", 1);

            svg.selectAll("circle")
                .append("svg:title")
                .text(function(d) {
                    return 'http://' + d.user;
                });
            d3.select("#chart").selectAll("svg")
                .style("height", DataStore.getFilteredData().length * radius / width * radius + 50)

            $('svg circle').tipsy({
                gravity: 'w',
                html: true,
                title: function() {
                    var d = this.__data__,
                        c = color(d.i);
                    return '<table><tr><td>Average Rating: ' + d.avg_rating + '</td></tr>' +
                        '<tr><td>Number Local Reviews: ' + d.num_reviews + '</td></tr>' +
                        '<tr><td>Cluster: ' + d.cluster_name + '</td></tr></table>'


                    ;
                }
            });


        };

        function getCheckedCheckboxesFor(checkboxName) {
            var checkboxes = document.querySelectorAll('input[name="' + checkboxName + '"]:checked'), values = [];
            Array.prototype.forEach.call(checkboxes, function(el) {
                values.push(parseInt(el.value));
            });
            return values;
        };

        function filterClusters(e) {
            var cluster = getCheckedCheckboxesFor('cluster');
            DataStore.setClusterArray(cluster);
            DataStore.populateFilteredData();
            drawCircles();
        };

        <!-- SET UP EVENT LISTENERS -->
        $("#rating").on("DOMSubtreeModified", function(e) {
            var rating = parseFloat(e.currentTarget.textContent);
            DataStore.setAvgRating(rating);
            DataStore.populateFilteredData();
            drawCircles();
        });

        $("#review").on("DOMSubtreeModified", function(e) {
            var review = parseFloat(e.currentTarget.textContent);
            DataStore.setNumReviews(review);
            DataStore.populateFilteredData();
            drawCircles();
        });

        $("#cluster1").on("click", filterClusters);
        $("#cluster2").on("click", filterClusters);
        $("#cluster3").on("click", filterClusters);
        $("#cluster4").on("click", filterClusters);
        $("#cluster5").on("click", filterClusters);
        $("#cluster6").on("click", filterClusters);
        $("#cluster7").on("click", filterClusters);
        $("#cluster8").on("click", filterClusters);
        $("#cluster9").on("click", filterClusters);
        $("#cluster10").on("click", filterClusters);
        var cluster = getCheckedCheckboxesFor('cluster');
        DataStore.setClusterArray(cluster);

        <!-- SLIDERS -->
        d3.select('#rating_slider')
            .call(
                d3.slider()
                .value(current_rating)
                .min(0)
                .max(5)
                .step(.05)
                .axis(true)
                .on("slide", function(evt, value) {
                    d3.select('#rating').text(Math.round(value * 100) / 100);
                    current_rating = value;
                })
            );

        d3.select('#review_slider')
            .call(
                d3.slider()
                .value(current_review)
                .min(5)
                .max(100)
                .step(1)
                .axis(true)
                .on("slide", function(evt, value) {
                    d3.select('#review').text(value);
                    current_review = value;
                })
            );


        var margin = {
                top: 20,
                right: 20,
                bottom: 30,
                left: 40
            },
            width = 800 - margin.left - margin.right,
            radius = 20;
            // height = 1900 - margin.top - margin.bottom;


        var color = d3.scale.category10();

        var svg = d3.select("#chart").append("svg:svg")
            .attr("width", width + margin.left + margin.right)
            // .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        d3.csv("../static/data.csv", function(error, data) {
            var x = 0;
            var y = 0;



            data.forEach(function(d, i) {
                d.user = d.user;
                d.last_review_date = d.last_review_date;
                d.avg_rating = parseFloat(d.avg_rating);
                d.num_reviews = parseInt(d.num_reviews);
                d.cluster = parseInt(d.cluster);
                d.cluster_name = d.cluster_name;
                DataStore.populateRawData(d);
            });

            DataStore.sortOnKeys();
            DataStore.populateFilteredData();

            drawCircles();


        });

});