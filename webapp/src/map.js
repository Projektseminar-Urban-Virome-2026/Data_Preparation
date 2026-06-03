//var map = L.map('map').setView([51.505, -0.09], 1);
window.myMap = L.map('map-container').setView([51.505, -0.09], 2);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(window.myMap);//.addTo(map);
//Quelle: https://leafletjs.com/examples/custom-icons/
var virusIcon = L.icon({
    iconUrl: 'ressources/images/marker.png',
    shadowUrl: 'ressources/images/marker_shadow.png',
    iconSize:     [25, 45], 
    shadowSize:   [25, 64], 
    iconAnchor:   [12, 44], 
    shadowAnchor: [0, 62],  
    popupAnchor:  [-2, -46]
});


    var marker_australia = L.marker([-37.81, 144.96],{icon: virusIcon}).addTo(window.myMap);
    marker_australia.bindPopup("<b>Australia</b><br>I am a popup.").openPopup();
    var marker_cameroon = L.marker([3.87058, 11.48450],{icon: virusIcon}).addTo(window.myMap);
    marker_cameroon.bindPopup("<b>Cameroon</b><br>I am a popup.").openPopup();
    var marker_canada = L.marker([50.45, -104.62],{icon: virusIcon}).addTo(window.myMap);
    marker_canada.bindPopup("<b>Canada</b><br>I am a popup. ").openPopup();
    var marker_china = L.marker([34.60315132568785, 103.79083761333533],{icon: virusIcon}).addTo(window.myMap);
    marker_china.bindPopup("<b>China</b><br>unknown coordinations!").openPopup();
    var marker_denmark = L.marker([55.66, 12.52],{icon: virusIcon}).addTo(window.myMap);
    marker_denmark.bindPopup("<b>Denmark</b><br>I am a popup.").openPopup();
    var marker_ecuador = L.marker([-0.22, -78.51],{icon: virusIcon}).addTo(window.myMap);
    marker_ecuador.bindPopup("<b>Ecuador</b><br>I am a popup.").openPopup();
    var marker_malaysia = L.marker([3.18306, 101.71111],{icon: virusIcon}).addTo(window.myMap);
    marker_malaysia.bindPopup("<b>Malaysia</b><br>I am a popup.").openPopup();
    var marker_usa = L.marker([47.66190, -122.43130],{icon: virusIcon}).addTo(window.myMap);
    marker_usa.bindPopup("<b>USA</b><br>I am a popup.").openPopup();