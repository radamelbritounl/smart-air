const fields = {
  mqRaw: document.getElementById("mqRaw"),
  mqScaled: document.getElementById("mqScaled"),
  airLevel: document.getElementById("airLevel"),
  uvIndex: document.getElementById("uvIndex"),
  voltage: document.getElementById("voltage"),
  status: document.getElementById("status"),
};

const lights = {
  Bajo: document.getElementById("green"),
  Medio: document.getElementById("yellow"),
  Alto: document.getElementById("red"),
};

async function loadDashboard() {
  try {
    const [latest, hourly, daily] = await Promise.all([
      fetchJson("/api/latest"),
      fetchJson("/api/history/hourly"),
      fetchJson("/api/history/daily"),
    ]);

    updateLatest(latest);
    refreshPlot("hourlyChart", "/plot/hourly.svg");
    refreshPlot("dailyChart", "/plot/daily.svg");
    fields.status.textContent = "Actualizado: " + new Date().toLocaleTimeString();
  } catch (error) {
    fields.status.textContent = "Sin conexion con datos";
  }
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error("Error al cargar datos");
  return response.json();
}

function updateLatest(data) {
  fields.mqRaw.textContent = valueOrDash(data.mq_raw);
  fields.mqScaled.textContent = valueOrDash(data.mq_scaled);
  fields.airLevel.textContent = data.air_level || "--";
  fields.uvIndex.textContent = valueOrDash(data.uv_index);
  fields.voltage.textContent = data.voltage ? data.voltage + " V" : "--";

  Object.values(lights).forEach((light) => light.classList.remove("on"));
  if (lights[data.air_level]) lights[data.air_level].classList.add("on");
}

function valueOrDash(value) {
  return value === undefined || value === null ? "--" : Number(value).toFixed(2);
}

function refreshPlot(id, url) {
  document.getElementById(id).src = url + "?t=" + Date.now();
}

loadDashboard();
setInterval(loadDashboard, 5000);
