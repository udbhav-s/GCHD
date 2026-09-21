window.gchd = Object.assign({}, window.gchd, {
  caseStudies: {
    pointToLayer: function (feature, latlng) {
      return L.circleMarker(latlng, {
        radius: 7,
        color: "#ffffff",
        weight: 2,
        fillColor: "#1CABE2",
        fillOpacity: 0.92
      });
    },
    onEachFeature: function (feature, layer) {
      var properties = feature.properties || {};
      if (properties.title) {
        layer.bindTooltip(properties.title);
      }

      var popup = document.createElement("div");
      popup.className = "case-study-popup";

      var title = document.createElement("div");
      title.className = "case-study-popup-title";
      title.textContent = properties.title || "Case study";
      popup.appendChild(title);

      if (properties.location) {
        var location = document.createElement("div");
        location.className = "case-study-popup-location";
        location.textContent = properties.location;
        popup.appendChild(location);
      }

      if (properties.url) {
        var link = document.createElement("a");
        link.href = properties.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = "Read case study ↗";
        popup.appendChild(link);
      }
      layer.bindPopup(popup);
    }
  }
});
