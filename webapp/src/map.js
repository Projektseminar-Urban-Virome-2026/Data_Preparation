//var map = L.map('map').setView([51.505, -0.09], 1);
window.myMap = L.map('map-container').setView([20, 10], 2);
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

// Quelle: https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch
async function getCities() {
  const url = "http://localhost:5001/cities";
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }
    const result = await response.json();
    result.forEach(city => {
        const marker = L.marker([city.latitude, city.longitude], { icon: virusIcon }).addTo(window.myMap);

             marker.bindPopup(`<b>${city.country}</b><br>${city.name}`); 
    });
  } catch (error) {
    console.error('Fehler beim laden der Städte...',error.message);
  }
};     
getCities();