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
const virusDetailChart = document.getElementById("virus-detail-chart");
const selectedViruses = new Map();
const statVirusCount = document.getElementById("stat-virus-count");
const statRunCount = document.getElementById("stat-run-count");
const statCityCount = document.getElementById("stat-city-count");
const statHostCount = document.getElementById("stat-host-count");
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

function renderRealmsBarchart(data, weather) {
    const runs = data.aggregated_virus_data;
    const weather_data = weather;

    // Group data by realm
    const realmData = runs.reduce((acc, curr) => {
        if (!acc[curr.realm]) {
            acc[curr.realm] = { x: [], y: [], name: curr.realm, type: 'bar', opacity: 0.9};
            }
        acc[curr.realm].x.push(curr.collection_date);
        acc[curr.realm].y.push(curr.total_percentage);
        return acc;
    }, {});

    // Prepare traces for Plotly
    const traces = Object.values(realmData);

    const temperatureTrace = {
        x: weather_data.map(entry => entry.time),
        y: weather_data.map(entry => entry.temperature),
        name: 'Temperature',
        yaxis: 'y2',
        mode: 'lines',
        line: { color: 'red', shape: 'spline' },
        smoothing: 1.1,
        opacity: 0.4,
        visible: 'legendonly'
    };

    const rainTrace = {
        x: weather_data.map(entry => entry.time),
        y: weather_data.map(entry => entry.rainfall),
        name: 'Rainfall (mm)',
        yaxis: 'y3',
        mode: 'none',
        line: { color: 'blue', shape: 'spline'},
        smoothing: 1.5,
        opacity: 0.5,
        fill: 'tozeroy',
        //visible: 'legendonly',
        fillcolor: 'rgba(0, 0, 255, 0.5)'
    };

    const humidityTrace = {
        x: weather_data.map(entry => entry.time),
        y: weather_data.map(entry => entry.humidity),
        name: 'Humidity (%)',
        yaxis: 'y4',
        mode: 'lines',
        line: { color: 'green', shape: 'spline' },
        smoothing: 1.1,
        opacity: 0.4,
        visible: 'legendonly'
    };

    traces.push(temperatureTrace, rainTrace, humidityTrace);

    const layout = {
        template: 'ggplot2',
        paper_bgcolor: 'rgba(0, 0, 0, 0)',
        plot_bgcolor: 'rgba(0, 0, 0, 0)',
        title: {text: 'Aggregated Virus Data by Realm Across Samples'},
        barmode: 'relative',
        hovermode: 'x unified',
        hoversubplots: 'axis',
        //xaxis: { title: {text: 'Date' }},
        yaxis: { title: {text: 'Share of classified Virome (%); Humidity (%); Rainfall (mm)'}, side: 'left', range: [0, 101]},
        yaxis2: {
            title: {text: 'Temperature (°C)'},
            overlaying: 'y',
            side: 'right',
            range: [0, 36],
            showgrid: false
        },
        yaxis3: {
            title: {text: 'Rainfall (mm)'},
            overlaying: 'y',
            side: 'right',
            anchor: 'free',
            position: 0.7, // Adjust as needed for visibility
            range: [0, 101],
            showgrid: false,
            visible: false
        },
        yaxis4: {
            title: {text: 'Humidity (%)', font: {color: 'rgba(0, 255, 0, 0.5)'}},
            overlaying: 'y',
            side: 'right',
            //anchor: 'free',
            position: 1, // Adjust for visual spacing
            autoshift: true,
            range: [0, 101],
            showgrid: false,
            tickcolor: 'rgba(0, 255, 0, 0.5)',
            tickfont: {color: 'rgba(0, 255, 0, 0.5)'},
            visible: false
        },
        legend: {
            x: 0.5,
            y: -0.2,
            xanchor: 'center',
            yanchor: 'top',
            orientation: 'h'  // Set the orientation to horizontal
        }
    };



    // Render the plot
    Plotly.newPlot('virus-aggregation-chart', traces, layout);

}

async function renderShannonIndex(data, weather) {
    const xDates = data.map(entry => entry.collection_date);
    const yShannonIndex = data.map(entry => entry.shannon_index);
    const weather_data = weather;
    const averageShannonIndex = yShannonIndex.reduce((sum, value) => sum + value, 0) / yShannonIndex.length;

    const trace = {
        x: xDates,
        y: yShannonIndex,
        mode: 'lines+markers',
        type: 'scatter',
        marker: { color: 'black' },
        line: { color: 'black' },
        name: 'Shannon Index'
    };

    const temperatureTrace = {
        x: weather_data.map(entry => entry.time),
        y: weather_data.map(entry => entry.temperature),
        name: 'Temperature',
        yaxis: 'y2',
        mode: 'lines',
        line: { color: 'red', shape: 'spline' },
        smoothing: 1.1,
        opacity: 0.4,
        visible: 'legendonly'
    };

    const rainTrace = {
        x: weather_data.map(entry => entry.time),
        y: weather_data.map(entry => entry.rainfall),
        name: 'Rainfall (mm)',
        yaxis: 'y3',
        mode: 'none',
        line: { color: 'blue', shape: 'spline'},
        smoothing: 1.5,
        opacity: 0.5,
        fill: 'tozeroy',
        //visible: 'legendonly',
        fillcolor: 'rgba(0, 0, 255, 0.5)'
    };

    const humidityTrace = {
        x: weather_data.map(entry => entry.time),
        y: weather_data.map(entry => entry.humidity),
        name: 'Humidity (%)',
        yaxis: 'y4',
        mode: 'lines',
        line: { color: 'green', shape: 'spline' },
        smoothing: 1.1,
        opacity: 0.4,
        visible: 'legendonly'
    };

    const traces = [trace, temperatureTrace, rainTrace, humidityTrace];

    const layout = {
        paper_bgcolor: 'rgba(0, 0, 0, 0)',
        plot_bgcolor: 'rgba(0, 0, 0, 0)',
        title: {text: 'Alpha-Diversität (Shannon Index)'},
        //xaxis: { title: {text: 'Collection Date'} },
        yaxis: { title: {text: 'Shannon Index'} },
        yaxis2: {
            title: {text: 'Temperature (°C)', standoff: 0},
            overlaying: 'y',
            side: 'right',
            anchor: 'free',
            position: 0.99,
            autoshift: true,
            range: [0, 36],
            showgrid: false
        },
        yaxis3: {
            title: {text: 'Rainfall (mm); Humidity (%)', standoff: 0},
            overlaying: 'y',
            side: 'right',
            anchor: 'free',
            position: 1, // Adjust as needed for visibility
            autoshift: true,
            range: [0, 100],
            showgrid: false,
            visible: true
        },
        yaxis4: {
            title: {text: 'Humidity (%)'},
            overlaying: 'y',
            side: 'right',
            anchor: 'free',
            position: 1.3, // Adjust for visual spacing
            range: [0, 100],
            showgrid: false,
            visible: false
        },
        legend: {
            x: 0.5,
            y: -0.2,
            xanchor: 'center',
            yanchor: 'top',
            orientation: 'h'  // Set the orientation to horizontal
        },
        template: 'ggplot2',
        shapes: [
            {
                type: 'line',
                x0: xDates[0],
                x1: xDates[xDates.length - 1],
                y0: averageShannonIndex,
                y1: averageShannonIndex,
                line: {
                    color: 'gray',
                    width: 2,
                    dash: 'dashdot',
                    opacity: 0.5
                }
            }
        ]
    };

    Plotly.newPlot('shannon-index-chart', traces, layout);

}

function renderShannonAndHostModel(data) {
    const shannon_prediction = data.predictions.shannon_mixed_model.toFixed(2);
    const host_prediction = data.predictions.human_host_model.toFixed(2);
    const prediction_date_raw = data.forecast_date;
    let prediction_date;
    try {
        const dateObject = new Date(prediction_date_raw);
        prediction_date = dateObject.toLocaleDateString('de-DE', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    } catch {
        prediction_date = "Invalid date";
    }

    var div = document.getElementById("shannon-index-model");
    div.innerHTML = `
                    <div class="model-render experimental mt-4 mb-4">
                    <div>
                        <h4 class="h5 fw-bold mb-1">Prognostizierter Shannon Index für den ${prediction_date}</h4>
                        <p class="h5 shannon-display">${shannon_prediction}</p>
                        <p class="text-secondary">Vorhersage basierend auf den (prognostizierten) Wetterdaten der vergangenen drei und nächsten zwei Tage.<br> Modell trainiert mit allen bisherigen Messungen.</p>
                    </div>
                    <span class="status-pill experimental muted">Experimentelles Feature</span>
                    </div>
                    `
    var div = document.getElementById("human-host-model");
        div.innerHTML = `
                        <div class="model-render experimental mt-4 mb-4">
                        <div>
                            <h4 class="h5 fw-bold mb-1">Prognostizierte Human Host Virus Abundance für den ${prediction_date}</h4>
                            <p class="h5 shannon-display">${host_prediction} %</p>
                            <p class="text-secondary">Vorhersage basierend auf den (prognostizierten) Wetterdaten der vergangenen drei und nächsten zwei Tage.<br> Modell trainiert mit allen bisherigen Messungen.</p>
                        </div>
                        <span class="status-pill experimental muted">Experimentelles Feature</span>
                        </div>
                        `
}

function renderHumanHostVirusChart(data, weather) {
    const virusData = data.virus_summary_by_date;
    const weather_data = weather;

    // Group virus data by collection date and create a stacked bar chart data structure
    const virusNames = new Set();
    const dateTraces = {};

    for (const date in virusData) {
        const details = virusData[date];
        for (const virusName in details.viruses) {
            virusNames.add(virusName);
            if (!dateTraces[virusName]) {
                dateTraces[virusName] = { x: [], y: [], name: virusName, type: 'bar', opacity: 0.9 };
            }
            dateTraces[virusName].x.push(date);
            dateTraces[virusName].y.push(details.viruses[virusName]);
        }
    }

    const traces = Object.values(dateTraces);

    // Create weather data traces
    const temperatureTrace = {
        x: weather_data.map(entry => entry.time),
        y: weather_data.map(entry => entry.temperature),
        name: 'Temperature',
        yaxis: 'y2',
        mode: 'lines',
        line: { color: 'red', shape: 'spline' },
        smoothing: 1.1,
        opacity: 0.4,
        visible: 'legendonly'
    };

    const rainTrace = {
        x: weather_data.map(entry => entry.time),
        y: weather_data.map(entry => entry.rainfall),
        name: 'Rainfall (mm)',
        yaxis: 'y3',
        mode: 'none',
        line: { color: 'blue', shape: 'spline' },
        smoothing: 1.5,
        opacity: 0.5,
        fill: 'tozeroy',
        fillcolor: 'rgba(0, 0, 255, 0.5)'
    };

    const humidityTrace = {
        x: weather_data.map(entry => entry.time),
        y: weather_data.map(entry => entry.humidity),
        name: 'Humidity (%)',
        yaxis: 'y4',
        mode: 'lines',
        line: { color: 'green', shape: 'spline' },
        smoothing: 1.1,
        opacity: 0.4,
        visible: 'legendonly'
    };

    traces.push(temperatureTrace, rainTrace, humidityTrace);

    const layout = {
        template: 'ggplot2',
        paper_bgcolor: 'rgba(0, 0, 0, 0)',
        plot_bgcolor: 'rgba(0, 0, 0, 0)',
        title: { text: 'Aggregated Human Host Virus Abundance' },
        barmode: 'stack', // Switch to stacked mode for bars
        hovermode: 'x unified',
        hoversubplots: 'axis',
        yaxis: { title: { text: 'Virus Abundance (%)' }, side: 'left'},
        yaxis2: {
            title: {text: 'Temperature (°C)', standoff: 0},
            overlaying: 'y',
            side: 'right',
            anchor: 'free',
            position: 0.99,
            autoshift: true,
            range: [0, 36],
            showgrid: false
        },
        yaxis3: {
            title: {text: 'Rainfall (mm); Humidity (%)', standoff: 0},
            overlaying: 'y',
            side: 'right',
            anchor: 'free',
            position: 1, // Adjust as needed for visibility
            autoshift: true,
            range: [0, 100],
            showgrid: false,
            visible: true
        },
        yaxis4: {
            title: {text: 'Humidity (%)'},
            overlaying: 'y',
            side: 'right',
            anchor: 'free',
            position: 1.3, // Adjust for visual spacing
            range: [0, 100],
            showgrid: false,
            visible: false
        },
        legend: {
            x: 0.5,
            y: -0.2,
            xanchor: 'center',
            yanchor: 'top',
            orientation: 'h'
        }
    };

    Plotly.newPlot('human-host-virus-chart', traces, layout);
}

function renderHumanHostVirus(data) {
    const viruses = data.viruses || [];
    selectedViruses.clear();

    if (viruses.length === 0) {
        return;
    }

    const totalRunHits = viruses.reduce((sum, virus) => sum + virus.run_count, 0);
    const chartRows = viruses.map((virus, index) => {
        const detailId = `${data.city.id}-${virus.virus_id}`;
        const virusName = escapeHtml(virus.name);
        const percentage = virus.percentage / virus.run_count;
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
                    <div class="virus-bar-track" aria-label="${virusName}: ${virus.run_count} Samples">
                        <div class="virus-bar-fill" style="width: ${width}%"></div>
                    </div>
                    <div class="virus-bar-meta">${virus.run_count} Samples</div>
                </div>
            </button>
        `;
    }).join("");

    var div = document.getElementById("human-host-virus");
    div.innerHTML = '<h4 class="h4 fw-bold mb-1">Klassifizierte Viren mit potentiellem menschlichen Host</h4>';
    div.innerHTML += '<p class="text-secondary mb-3">Prozentwerte geben die durchschnittliche Häufigkeit des Vorkommens in den jeweiligen Samples an.</p>'
    div.innerHTML += chartRows;
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
            <span>baltimore_class</span>
            <strong>${escapeHtml(detail.baltimore_class || "-")}</strong>
        </div>
        <div class="detail-card">
            <span>human host</span>
            <strong>${escapeHtml(detail.human_host === 1 ? "Yes" : "No" || "-")}</strong>
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
    virusDetailChart.innerHTML = `<div class='h4'>Stadt auswählen für weitere Infos</div>`

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
            const color = "blue";
            const marker = L.circleMarker([city.latitude, city.longitude], {
                //radius,
                color,
                weight: 2,
                fillColor: color,
                fillOpacity: 0.65,
            }).addTo(virusCityLayer);

            marker.bindPopup(`
                <b>${escapeHtml(city.city_name)}, ${escapeHtml(city.country)}</b><br>
                Durchschnitt: ${Number(city.average_amount).toFixed(2)} %<br>
                Temperatur: ${formatTemperature(city.average_temperature)}<br>
                Runs mit Treffer: ${city.run_count}
            `);
            marker.on("click", () => loadVirusDetail(virusId, city));
            bounds.push([city.latitude, city.longitude]);
        });

        if (bounds.length > 0) {
            virusCityMap.fitBounds(bounds, { padding: [40, 40], maxZoom: 5 });
        }
    } catch (error) {
        console.error("Fehler beim Laden der Virus-Stadtkarte...", error.message);
    }
}

async function loadVirusDetail(virusId, city) {
    virusDetailChart.innerHTML = `<div id="virus-abundance-chart"></div>
                                  <div id="virus-model"></div>
                                 `;
    renderVirusAbundance(city.city_id, virusId);
    renderVirusModel(city.city_id, virusId);
}

async function renderVirusAbundance(cityId, virusId) {
    try {
        const response = await fetch(`${API_BASE_URL}/cities/${cityId}/virus/${virusId}/abundance`);
        if (!response.ok) {
            throw new Error('Unable to fetch virus abundance data');
        }
        const weather_response = await fetch(`${API_BASE_URL}/cities/${cityId}/weather_data`);
        if (!weather_response.ok) {
            throw new Error(`Failed to fetch weather data: ${weather_response.status}`);
        }

        const weather_data = await weather_response.json();

        const data = await response.json();
        const xDates = data.abundance_data.map(entry => entry.collection_date);
        const yAbundances = data.abundance_data.map(entry => entry.amount_in_sample_as_percentage);

        const trace = {
            x: xDates,
            y: yAbundances,
            type: 'bar',
            marker: { color: 'orange', opacity: 0.8 },
            name: 'Abundance'
        };

        const temperatureTrace = {
            x: weather_data.map(entry => entry.time),
            y: weather_data.map(entry => entry.temperature),
            name: 'Temperature',
            yaxis: 'y2',
            mode: 'lines',
            line: { color: 'red', shape: 'spline' },
            smoothing: 1.1,
            opacity: 0.4,
            visible: 'legendonly'
        };

        const rainTrace = {
            x: weather_data.map(entry => entry.time),
            y: weather_data.map(entry => entry.rainfall),
            name: 'Rainfall (mm)',
            yaxis: 'y3',
            mode: 'none',
            line: { color: 'blue', shape: 'spline'},
            smoothing: 1.5,
            opacity: 0.5,
            fill: 'tozeroy',
            //visible: 'legendonly',
            fillcolor: 'rgba(0, 0, 255, 0.5)'
        };

        const humidityTrace = {
            x: weather_data.map(entry => entry.time),
            y: weather_data.map(entry => entry.humidity),
            name: 'Humidity (%)',
            yaxis: 'y4',
            mode: 'lines',
            line: { color: 'green', shape: 'spline' },
            smoothing: 1.1,
            opacity: 0.4,
            visible: 'legendonly'
        };

        const traces = [trace, temperatureTrace, rainTrace, humidityTrace];

        const layout = {
            title: {text: `${data.virus_name} Abundance in ${data.city.name}`},
            xaxis: { title: {text: 'Collection Date' }},
            yaxis: { title: {text: 'Abundance (%)' }},
            yaxis2: {
                title: {text: 'Temperature (°C)'},
                overlaying: 'y',
                side: 'right',
                range: [0, 36],
                showgrid: false
            },
            yaxis3: {
                title: {text: 'Rainfall (mm)'},
                overlaying: 'y',
                side: 'right',
                anchor: 'free',
                position: 0.7, // Adjust as needed for visibility
                range: [0, 100],
                showgrid: false,
                visible: false
            },
            yaxis4: {
                title: {text: 'Humidity (%)'},
                overlaying: 'y',
                side: 'right',
                anchor: 'free',
                position: 1.3, // Adjust for visual spacing
                range: [0, 100],
                showgrid: false,
                visible: false
            },
            legend: {
                x: 0.5,
                y: -0.2,
                xanchor: 'center',
                yanchor: 'top',
                orientation: 'h'  // Set the orientation to horizontal
            },
            template: 'ggplot2'
        };

        Plotly.newPlot('virus-abundance-chart', traces, layout);
    } catch (error) {
        console.error('Error plotting virus abundance:', error);
    }
}

async function renderVirusModel(cityId, virusId) {
    try {
        const response = await fetch(`${API_BASE_URL}/cities/${cityId}/virus/${virusId}/model`);
        if (!response.ok) {
            throw new Error('Unable to fetch virus prediction data');
        }

        const data = await response.json();
        const virus_name = data.virus_name;
        let raw_prediction = data.predictions[`${virus_name}_model`];
        if (typeof raw_prediction === 'number') {
            if (raw_prediction < 0) {
                virus_prediction = 0.00;
            } else {
                virus_prediction = raw_prediction;
            }
        } else {
            virus_prediction = 0.00;
        }
        virus_prediction = virus_prediction.toFixed(2);
        const host_prediction = data.predictions.human_host_model.toFixed(2);
        const prediction_date_raw = data.forecast_date;
        let prediction_date;
        try {
            const dateObject = new Date(prediction_date_raw);
            prediction_date = dateObject.toLocaleDateString('de-DE', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        } catch {
            prediction_date = "Invalid date";
        }

        var div = document.getElementById("virus-model");
        div.innerHTML = `
                        <div class="model-render experimental mt-4 mb-4">
                        <div>
                            <h4 class="h5 fw-bold mb-1">Prognostizierter Anteil von ${virus_name} für den ${prediction_date}</h4>
                            <p class="h5 shannon-display">${virus_prediction} %</p>
                            <p class="text-secondary">Vorhersage basierend auf den (prognostizierten) Wetterdaten der vergangenen drei und nächsten zwei Tage.<br> Modell trainiert mit allen bisherigen Messungen.</p>
                        </div>
                        <span class="status-pill experimental muted">Experimentelles Feature</span>
                        </div>
                        `

    } catch (error) {
        console.error('Error showing virus model:', error);
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
        statHostCount.textContent = stats.host_count;
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

async function loadCityViruses(city) {      // called on-click
    setDetailState({
        title: `${city.name}, ${city.country}`,
        subtitle: "Virus-Daten werden geladen...",
        countLabel: "Lädt",
        isEmpty: true,
        content: `
            <div class="empty-state compact">
                <div class="spinner-border text-info" role="status" aria-label="Lädt"></div>
                <p class="text-secondary mb-0 mt-3">Daten werden von der API geladen.</p>
            </div>
        `,
    });

    count = "-";
    try {
            const response = await fetch(`${API_BASE_URL}/cities/${city.id}/sampleCount`);
            if (!response.ok) {
                throw new Error(`Failed to fetch sample data: ${response.status}`);
            }

            const sampleCount = await response.json();
            count = sampleCount.count;

        } catch (error) {
            console.error("Error fetching sample-count from database", error.message);
        }

    setDetailState({
        title: `${city.name}, ${city.country}`,
        subtitle: `Auswertung der Virenproben`,
        countLabel: `${count} Samples`,
        // add more <div>s for new plots here:
        content: `
            <div id="virus-aggregation-chart"></div>
            <div id="shannon-index-chart"></div>
            <div id="shannon-index-model"></div>
            <div id="human-host-virus"></div>
            <div id="human-host-virus-chart"></div>
            <div id="human-host-model"></div>
        `,
        });

    // Calling the different plot-functions

    try {
        const response = await fetch(`${API_BASE_URL}/cities/${city.id}/aggregate_realms`);
        if (!response.ok) {
            throw new Error(`Failed to fetch virus aggregate data: ${response.status}`);
        }
        const weather_response = await fetch(`${API_BASE_URL}/cities/${city.id}/weather_data`);
        if (!weather_response.ok) {
            throw new Error(`Failed to fetch weather data: ${weather_response.status}`);
        }

        const result = await response.json();
        const weather = await weather_response.json();
        renderRealmsBarchart(result, weather);

    } catch (error) {
        console.error("Error rendering virus aggregation chart", error.message);
    }

    try {
        const response = await fetch(`${API_BASE_URL}/cities/${city.id}/runs`);
        if (!response.ok) {
            throw new Error(`Failed to fetch human host data: ${response.status}`);
        }
        const weather_response = await fetch(`${API_BASE_URL}/cities/${city.id}/weather_data`);
        if (!weather_response.ok) {
            throw new Error(`Failed to fetch weather data: ${weather_response.status}`);
        }

        const result = await response.json();
        const weather = await weather_response.json();
        renderShannonIndex(result, weather);

    } catch (error) {
        console.error("Error rendering shannon index chart", error.message);
    }

    try {
        const response = await fetch(`${API_BASE_URL}/cities/${city.id}/shannon_and_host_model`);
        if (!response.ok) {
            throw new Error(`Failed to fetch model data: ${response.status}`);
        }

        const result = await response.json();
        renderShannonAndHostModel(result);

    } catch (error) {
        console.error("Error rendering shannon model", error.message);
    }

    try {
        const response = await fetch(`${API_BASE_URL}/cities/${city.id}/human_host_virus_summary`);
        if (!response.ok) {
            throw new Error(`Failed to fetch human host data: ${response.status}`);
        }
        const weather_response = await fetch(`${API_BASE_URL}/cities/${city.id}/weather_data`);
        if (!weather_response.ok) {
            throw new Error(`Failed to fetch weather data: ${weather_response.status}`);
        }

        const result = await response.json();
        const weather = await weather_response.json();
        renderHumanHostVirusChart(result, weather);

    } catch (error) {
        console.error("Error rendering human host virus chart", error.message);
    }

    try {
        const response = await fetch(`${API_BASE_URL}/cities/${city.id}/human_host_virus`);
        if (!response.ok) {
            throw new Error(`Failed to fetch human host data: ${response.status}`);
        }

        const result = await response.json();
        renderHumanHostVirus(result);

    } catch (error) {
        console.error("Error rendering human host viruses", error.message);
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
        console.error("Fehler beim Laden der Virusdaten...", error.message);
            setDetailState({
                title: `${city.name}, ${city.country}`,
                subtitle: "Die Virusdaten konnten nicht geladen werden.",
                countLabel: "Fehler",
                isEmpty: true,
                content: `
                    <div class="empty-state compact">
                    <h5 class="fw-bold mb-1">API nicht erreichbar</h5>
                    <p class="text-secondary mb-0">Prüfe, ob die DB-API auf ${API_BASE_URL} läuft.</p>
                    </div>
                    `,
                });
    }
}

loadStats();
getCities();
