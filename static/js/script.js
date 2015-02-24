(function(window){
L.mapbox.accessToken = 'YOUR_ACCESS_TOKEN';
  var map = L.mapbox.map('map', 'examples.map-i86nkdio')
      .setView([49.41, 8.68], 14);

  var featureGroup = L.featureGroup().addTo(map);
  var passableArea = false;
  var pnts = [];
  var featureLayer, pathLayer;
  var pathStyle = {
                  color: '#FF8000',
                  weight: 5
                };

  var drawControl = new L.Control.Draw({
    draw: {
        polyline: false,
        polygon: {
          allowIntersection: false,
          drawError: {
            color: '#b00b00',
            timeout: 1000
          }
        },
        rectangle: false,
        circle: false
      }
  }).addTo(map);

  function sendRequest(){
    var params = {
          'polygonGeom': passableArea,
          'endPoints': pnts
        };

          $.ajax({
            type: "POST",
            url: "/graphGeneration/",
            data: JSON.stringify(params),
            crossDomain: true,
            success: function(response){
              if (response.status === 'OK'){
                if (!pathLayer) {
                  pathLayer = L.mapbox.featureLayer(JSON.parse(response.path)).addTo(map);
                  pathLayer.setStyle(pathStyle);
                } else {
                  pathLayer.setGeoJSON(JSON.parse(response.path));
                  pathLayer.setStyle(pathStyle);
                }
              } else {
                alert(response.message)
              }
            },
            error: function(errorMsg){
              alert(errorMsg);
            },
            dataType: 'json'
        });
}

  map.on('draw:created', function(e) {
      if (e.layerType == 'polygon') {
        if (!passableArea) {
          passableArea = e.layer.toGeoJSON();
          featureLayer = L.mapbox.featureLayer(passableArea)
                            .addTo(map);
        }
        else {
          passableArea.geometry.coordinates.push(e.layer.toGeoJSON().geometry.coordinates[0]);
          featureLayer.setGeoJSON(passableArea);
        }
      } else if (e.layerType == 'marker') {
        if (pnts.length < 2) {
          pnts.push(e.layer.toGeoJSON());
          featureGroup.addLayer(e.layer);
        }
      }
      if (pnts.length == 2) {
        sendRequest();
      }
  });
})();

