const API_BASE_URL = "http://localhost:5001";

window.myMap = L.map("map-container").setView([20, 10], 2);

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(window.myMap);

const cityDetailTitle = document.getElementById("city-detail-title");
const cityDetailSubtitle = document.getElementById("city-detail-subtitle");
const cityDetailCount = document.getElementById("city-detail-count");
const virusChart = document.getElementById("virus-chart");
const virusDetailTitle = document.getElementById("virus-detail-title");
const virusDetailGrid = document.getElementById("virus-detail-grid");
const selectedViruses = new Map();
const statVirusCount = document.getElementById("stat-virus-count");
const statRunCount = document.getElementById("stat-run-count");
const statCityCount = document.getElementById("stat-city-count");
const statTimeframe = document.getElementById("stat-time-frame");
let virusCityMap;
let virusCityLayer;

function setDetailState({ title, subtitle, countLabel, content, isEmpty = false }) {
    cityDetailTitle.textContent = title;
    cityDetailSubtitle.textContent = subtitle;
    cityDetailCount.textContent = countLabel;
    virusChart.classList.toggle("empty", isEmpty);
    virusChart.innerHTML = content;
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function renderVirusChart(data) {
    const viruses = data.viruses || [];
    selectedViruses.clear();

    if (viruses.length === 0) {
        setDetailState({
            title: `${data.city.name}, ${data.city.country}`,
            subtitle: `${data.run_count} Runs gefunden, aber keine Virusdaten in der Datenbank.`,
            countLabel: "Keine Daten",
            isEmpty: true,
            content: `
                <div class="empty-state compact">
                    <h5 class="fw-bold mb-1">Keine Viren gefunden</h5>
                    <p class="text-secondary mb-0">Für diese Stadt sind aktuell keine Einträge in Virus_in_Runs vorhanden.</p>
                </div>
            `,
        });
        return;
    }

    const totalRunHits = viruses.reduce((sum, virus) => sum + virus.run_count, 0);
    const chartRows = viruses.map((virus, index) => {
        const detailId = `${data.city.id}-${virus.virus_id}`;
        const virusName = escapeHtml(virus.name);
        const percentage = totalRunHits > 0 ? (virus.run_count / totalRunHits) * 100 : 0;
        const width = Math.max(percentage, 2);
        selectedViruses.set(detailId, { ...virus, city: data.city });

        return `
            <button class="virus-bar-row" type="button" data-virus-detail="${detailId}">
                <div class="virus-rank">${index + 1}</div>
                <div class="virus-bar-content">
                    <div class="virus-bar-label">
                        <span>${virusName}</span>
                        <strong>${percentage.toFixed(1)}%</strong>
                    </div>
                    <div class="virus-bar-track" aria-label="${virusName}: ${virus.run_count} Runs">
                        <div class="virus-bar-fill" style="width: ${width}%"></div>
                    </div>
                    <div class="virus-bar-meta">${virus.run_count} Runs</div>
                </div>
            </button>
        `;
    }).join("");

    setDetailState({
        title: `${data.city.name}, ${data.city.country}`,
        subtitle: `${viruses.length} Viren über ${data.run_count} Runs hinweg, Prozentwerte als Anteil aller Treffer.`,
        countLabel: `${viruses.length} Viren`,
        content: chartRows,
    });
}

function showVirusDetail(detail) {
    virusDetailTitle.textContent = detail.name;
    virusDetailGrid.innerHTML = `
        <div class="detail-card">
            <span>tax_id</span>
            <strong>${detail.virus_id}</strong>
        </div>
        <div class="detail-card">
            <span>name</span>
            <strong>${escapeHtml(detail.name)}</strong>
        </div>
        <div class="detail-card">
            <span>realm</span>
            <strong>${escapeHtml(detail.realm || "-")}</strong>
        </div>
        <div class="detail-card">
            <span>kingdom</span>
            <strong>${escapeHtml(detail.kingdom || "-")}</strong>
        </div>
        <div class="detail-card">
            <span>phylum</span>
            <strong>${escapeHtml(detail.phylum || "-")}</strong>
        </div>
        <div class="detail-card">
            <span>class</span>
            <strong>${escapeHtml(detail.class || "-")}</strong>
        </div>
        <div class="detail-card">
            <span>taxonomic_order</span>
            <strong>${escapeHtml(detail.taxonomic_order || "-")}</strong>
        </div>
        <div class="detail-card">
            <span>family</span>
            <strong>${escapeHtml(detail.family || "-")}</strong>
        </div>
        <div class="detail-card">
            <span>genus</span>
            <strong>${escapeHtml(detail.genus || "-")}</strong>
        </div>
        <div class="detail-card">
            <span>species</span>
            <strong>${escapeHtml(detail.species || "-")}</strong>
        </div>
        <div class="detail-card">
            <span>baltimore_class</span>
            <strong>${escapeHtml(detail.baltimore_class || "-")}</strong>
        </div>
    `;
    showPage("virus-detail");
    loadVirusCityMap(detail.virus_id);
}

function ensureVirusCityMap() {
    if (!virusCityMap) {
        virusCityMap = L.map("virus-city-map").setView([20, 10], 2);
        L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        }).addTo(virusCityMap);
        virusCityLayer = L.layerGroup().addTo(virusCityMap);
    }
    setTimeout(() => virusCityMap.invalidateSize(), 100);
}

function markerColor(temperature, minTemperature, maxTemperature) {
    if (temperature === null || temperature === undefined || minTemperature === maxTemperature) {
        return "#19a6a8";
    }

    const ratio = (temperature - minTemperature) / (maxTemperature - minTemperature);
    const red = Math.round(48 + ratio * 207);
    const green = Math.round(120 - ratio * 70);
    const blue = Math.round(210 - ratio * 160);
    return `rgb(${red}, ${green}, ${blue})`;
}

async function loadVirusCityMap(virusId) {
    ensureVirusCityMap();
    virusCityLayer.clearLayers();

    try {
        const response = await fetch(`${API_BASE_URL}/viruses/${virusId}/cities`);
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        const cities = await response.json();
        const maxAverage = Math.max(...cities.map((city) => city.average_amount), 0);
        const temperatures = cities
            .map((city) => city.average_temperature)
            .filter((temperature) => temperature !== null && temperature !== undefined);
        const minTemperature = temperatures.length ? Math.min(...temperatures) : null;
        const maxTemperature = temperatures.length ? Math.max(...temperatures) : null;
        const bounds = [];

        cities.forEach((city) => {
            const radius = maxAverage > 0 ? 8 + (city.average_amount / maxAverage) * 24 : 10;
            const color = markerColor(city.average_temperature, minTemperature, maxTemperature);
            const marker = L.circleMarker([city.latitude, city.longitude], {
                radius,
                color,
                weight: 2,
                fillColor: color,
                fillOpacity: 0.65,
            }).addTo(virusCityLayer);

            marker.bindPopup(`
                <b>${escapeHtml(city.city_name)}, ${escapeHtml(city.country)}</b><br>
                Durchschnitt: ${Number(city.average_amount).toFixed(2)}<br>
                Temperatur: ${formatTemperature(city.average_temperature)}<br>
                Runs mit Treffer: ${city.run_count}
            `);
            bounds.push([city.latitude, city.longitude]);
        });

        if (bounds.length > 0) {
            virusCityMap.fitBounds(bounds, { padding: [40, 40], maxZoom: 5 });
        }
    } catch (error) {
        console.error("Fehler beim Laden der Virus-Stadtkarte...", error.message);
    }
}

function formatTemperature(value) {
    return value === null || value === undefined ? "-" : `${Number(value).toFixed(1)} °C`;
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        const stats = await response.json();
        statVirusCount.textContent = stats.virus_count;
        statRunCount.textContent = stats.run_count;
        statCityCount.textContent = stats.city_count;
        statTimeframe.textContent = stats.min_date + " bis " + stats.max_date;
    } catch (error) {
        console.error("Fehler beim Laden der Statistiken...", error.message);
    }
}

virusChart.addEventListener("click", (event) => {
    const row = event.target.closest("[data-virus-detail]");
    if (row && selectedViruses.has(row.dataset.virusDetail)) {
        showVirusDetail(selectedViruses.get(row.dataset.virusDetail));
    }
});

async function loadCityViruses(city) {
/*    setDetailState({
        title: `${city.name}, ${city.country}`,
        subtitle: "Virus-Häufigkeiten werden geladen...",
        countLabel: "Lädt",
        isEmpty: true,
        content: `
            <div class="empty-state compact">
                <div class="spinner-border text-info" role="status" aria-label="Lädt"></div>
                <p class="text-secondary mb-0 mt-3">Daten werden von der API geladen.</p>
            </div>
        `,
    });
*/
    try {
            const response = await fetch(`${API_BASE_URL}/cities/${city.id}/aggregate_realms`);
            if (!response.ok) {
                throw new Error(`Failed to fetch virus aggregate data: ${response.status}`);
            }

            const data = await response.json();

            // Assuming your API response contains an array of runs with genus-level aggregation
            const runs = data.aggregated_virus_data;

                // Group data by realm
                const realmData = runs.reduce((acc, curr) => {
                    if (!acc[curr.realm]) {
                        acc[curr.realm] = { x: [], y: [], name: curr.realm, type: 'bar' };
                    }
                    acc[curr.realm].x.push(curr.collection_date);
                    acc[curr.realm].y.push(curr.total_percentage);
                    return acc;
                }, {});

                // Prepare traces for Plotly
                const traces = Object.values(realmData);

                // Define plotly layout
                const layout = {
                    title: 'Aggregated Virus Data by Realm Across Runs',
                    barmode: 'stack',
                    xaxis: { title: 'Date' },
                    yaxis: { title: 'Percentage of Total' },
                };


            // Render the plot
            Plotly.newPlot('virus-aggregation-chart', traces, layout);
        } catch (error) {
            console.error("Error rendering virus aggregation chart", error.message);
        }
}

async function getCities() {
    try {
        const response = await fetch(`${API_BASE_URL}/cities`);
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        const result = await response.json();
        result.forEach((city) => {
            const marker = L.marker([city.latitude, city.longitude]).addTo(window.myMap);
            marker.bindPopup(`<b>${escapeHtml(city.country)}</b><br>${escapeHtml(city.name)}`);
            marker.on("click", () => loadCityViruses(city));
        });
    } catch (error) {
        console.error("Fehler beim Laden der Städte...", error.message);
    }
}

loadStats();
getCities();
