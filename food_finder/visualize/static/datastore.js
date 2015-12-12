$(document).ready( function () {
	var _rawData = [];
	var _sortedData = [];
	var _filteredData = [];

	var avgRating = parseFloat($("#rating").text());
	var numReviews = parseInt($("#review").text());
	var clusterArray = [];

	DataStore = window.DataStore = {
		populateRawData: function (dataElement) {
			_rawData.push(dataElement);
		},


		sortOnKeys: function () {

		    var sortable = [];

		    for(var i = 0; i < _rawData.length; i++) {

		        sortable.push([_rawData[i], _rawData[i].avg_rating]);
		    }

			sortable.sort(function (b,a) { 
				return a[1] - b[1];
			});

		    var tempData = [];

		    for(var i = 0; i < sortable.length; i++) {
		        tempData.push(sortable[i][0]);
		    }

		    _rawData = tempData;
		},

		populateFilteredData: function () {
			_filteredData = [];

			_rawData.forEach(function (data) {
				if (data.avg_rating >= avgRating
					&& data.num_reviews >= numReviews 
					&& clusterArray.indexOf(data.cluster) != -1){
					_filteredData.push(data);
				}
			});
		},

		getFilteredData: function () {
			return _filteredData;
		},

		getRawData: function () {
			return _rawData;
		},

		getFilters: function () {
			return {
				avgRating: avgRating,
				numReviews: numReviews
			}
		},

		setAvgRating: function (rating) {
			avgRating = rating;
		},

		setClusterArray: function (cluster) {
			clusterArray = cluster;
		},

		setNumReviews: function (reviews) {
			numReviews = reviews;
		}

	};
});