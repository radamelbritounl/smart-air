import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from flask import Flask, Response, jsonify, render_template, request


app = Flask(__name__)


class AirQualityClassifier:
    def classify(self, mq_scaled: float) -> str:
        if mq_scaled <= 350:
            return "Bajo"
        if mq_scaled <= 700:
            return "Medio"
        return "Alto"


@dataclass
class SensorReading:
    mq_raw: float
    uv_raw: float
    voltage: float = 5.0
    created_at: str | None = None

    @property
    def mq_scaled(self) -> float:
        return round(self.mq_raw * 10, 2)

    @property
    def uv_voltage(self) -> float:
        return round((self.uv_raw * 5.0) / 1023.0, 2)

    @property
    def uv_index(self) -> float:
        return round(max(0, self.uv_voltage * 10), 2)

    def to_record(self) -> dict:
        classifier = AirQualityClassifier()
        return {
            "created_at": self.created_at or datetime.now(timezone.utc).isoformat(),
            "mq_raw": self.mq_raw,
            "mq_scaled": self.mq_scaled,
            "uv_raw": self.uv_raw,
            "uv_voltage": self.uv_voltage,
            "uv_index": self.uv_index,
            "voltage": self.voltage,
            "air_level": classifier.classify(self.mq_scaled),
        }


class ReadingStore:
    def add(self, reading: SensorReading) -> dict:
        raise NotImplementedError

    def latest(self) -> dict | None:
        raise NotImplementedError

    def hourly(self) -> list[dict]:
        raise NotImplementedError

    def daily(self) -> list[dict]:
        raise NotImplementedError


class SQLiteStore(ReadingStore):
    def __init__(self, path: str = "smart_air.db"):
        self.path = path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.path)

    def _init_db(self):
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    mq_raw REAL NOT NULL,
                    mq_scaled REAL NOT NULL,
                    uv_raw REAL NOT NULL,
                    uv_voltage REAL NOT NULL,
                    uv_index REAL NOT NULL,
                    voltage REAL NOT NULL,
                    air_level TEXT NOT NULL
                )
                """
            )

    def add(self, reading: SensorReading) -> dict:
        record = reading.to_record()
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO readings (
                    created_at, mq_raw, mq_scaled, uv_raw, uv_voltage,
                    uv_index, voltage, air_level
                )
                VALUES (
                    :created_at, :mq_raw, :mq_scaled, :uv_raw, :uv_voltage,
                    :uv_index, :voltage, :air_level
                )
                """,
                record,
            )
        return record

    def latest(self) -> dict | None:
        rows = self._query(
            "SELECT * FROM readings ORDER BY datetime(created_at) DESC LIMIT 1"
        )
        return rows[0] if rows else None

    def hourly(self) -> list[dict]:
        return self._query(
            """
            SELECT
                substr(created_at, 1, 13) || ':00' AS label,
                ROUND(AVG(mq_scaled), 2) AS mq_scaled,
                ROUND(AVG(uv_index), 2) AS uv_index,
                ROUND(AVG(voltage), 2) AS voltage
            FROM readings
            WHERE datetime(created_at) >= datetime('now', '-24 hours')
            GROUP BY substr(created_at, 1, 13)
            ORDER BY label
            """
        )

    def daily(self) -> list[dict]:
        return self._query(
            """
            SELECT
                substr(created_at, 1, 10) AS label,
                ROUND(AVG(mq_scaled), 2) AS mq_scaled,
                ROUND(AVG(uv_index), 2) AS uv_index,
                ROUND(AVG(voltage), 2) AS voltage
            FROM readings
            WHERE datetime(created_at) >= datetime('now', '-7 days')
            GROUP BY substr(created_at, 1, 10)
            ORDER BY label
            """
        )

    def _query(self, sql: str) -> list[dict]:
        with self._connect() as con:
            con.row_factory = sqlite3.Row
            return [dict(row) for row in con.execute(sql).fetchall()]


class SupabaseStore(ReadingStore):
    def __init__(self, url: str, key: str):
        self.url = url.rstrip("/")
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def add(self, reading: SensorReading) -> dict:
        import requests

        record = reading.to_record()
        response = requests.post(
            f"{self.url}/rest/v1/readings",
            headers=self.headers,
            json=record,
            timeout=15,
        )
        response.raise_for_status()
        return response.json()[0]

    def latest(self) -> dict | None:
        rows = self._get("select=*&order=created_at.desc&limit=1")
        return rows[0] if rows else None

    def hourly(self) -> list[dict]:
        rows = self._get("select=created_at,mq_scaled,uv_index,voltage&order=created_at.asc")
        return average_by_label(rows[-1200:], "hour")

    def daily(self) -> list[dict]:
        rows = self._get("select=created_at,mq_scaled,uv_index,voltage&order=created_at.asc")
        return average_by_label(rows, "day")[-7:]

    def _get(self, query: str) -> list[dict]:
        import requests

        response = requests.get(
            f"{self.url}/rest/v1/readings?{query}",
            headers=self.headers,
            timeout=15,
        )
        response.raise_for_status()
        return response.json()


def average_by_label(rows: list[dict], mode: str) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        label = row["created_at"][:13] + ":00" if mode == "hour" else row["created_at"][:10]
        groups.setdefault(label, []).append(row)

    result = []
    for label, values in groups.items():
        result.append(
            {
                "label": label,
                "mq_scaled": avg(values, "mq_scaled"),
                "uv_index": avg(values, "uv_index"),
                "voltage": avg(values, "voltage"),
            }
        )
    return sorted(result, key=lambda item: item["label"])


def avg(rows: list[dict], key: str) -> float:
    return round(sum(float(row[key]) for row in rows) / len(rows), 2)


def get_store() -> ReadingStore:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if supabase_url and supabase_key:
        return SupabaseStore(supabase_url, supabase_key)
    return SQLiteStore(os.getenv("SQLITE_PATH", "smart_air.db"))


store = get_store()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/latest")
def api_latest():
    return jsonify(store.latest() or {})


@app.get("/api/history/hourly")
def api_hourly():
    return jsonify(store.hourly())


@app.get("/api/history/daily")
def api_daily():
    return jsonify(store.daily())


@app.get("/plot/hourly.svg")
def plot_hourly():
    return Response(svg_chart(store.hourly(), "Promedio por hora"), mimetype="image/svg+xml")


@app.get("/plot/daily.svg")
def plot_daily():
    return Response(svg_chart(store.daily(), "Promedio diario - ultimos 7 dias"), mimetype="image/svg+xml")


@app.route("/api/readings", methods=["GET", "POST"])
def api_readings():
    try:
        data = request.get_json(silent=True) or request.values
        reading = SensorReading(
            mq_raw=float(data.get("mq_raw", 0)),
            uv_raw=float(data.get("uv_raw", 0)),
            voltage=float(data.get("voltage", 5.0)),
        )
        return jsonify(store.add(reading)), 201
    except Exception as exc:
        return jsonify(
            {
                "error": "No se pudo guardar la lectura",
                "detail": str(exc),
            }
        ), 500


def svg_chart(rows: list[dict], title: str) -> str:
    width = 900
    height = 300
    pad = 44
    colors = {
        "mq_scaled": "#c83d32",
        "uv_index": "#2f6fbd",
        "voltage": "#23a455",
    }
    labels = {
        "mq_scaled": "Aire",
        "uv_index": "UV",
        "voltage": "Voltaje",
    }

    if not rows:
        return f"""
        <svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
          <rect width="100%" height="100%" fill="#fbfdfd"/>
          <text x="44" y="150" font-family="Arial" font-size="18" fill="#647174">Esperando datos...</text>
        </svg>
        """

    max_value = max(
        10,
        *[
            float(row.get(key) or 0)
            for row in rows
            for key in ("mq_scaled", "uv_index", "voltage")
        ],
    )
    chart_w = width - pad * 2
    chart_h = height - pad * 2
    step = chart_w / max(1, len(rows) - 1)

    lines = []
    for key, color in colors.items():
        points = []
        for index, row in enumerate(rows):
            x = pad + step * index
            y = height - pad - (float(row.get(key) or 0) / max_value) * chart_h
            points.append(f"{x:.1f},{y:.1f}")
        lines.append(
            f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="3"/>'
        )

    legend = []
    for index, (key, color) in enumerate(colors.items()):
        x = 680 + index * 72
        legend.append(f'<rect x="{x}" y="18" width="10" height="10" fill="{color}"/>')
        legend.append(
            f'<text x="{x + 14}" y="28" font-family="Arial" font-size="12" fill="#162022">{labels[key]}</text>'
        )

    return f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
      <rect width="100%" height="100%" fill="#fbfdfd"/>
      <line x1="{pad}" y1="{pad}" x2="{pad}" y2="{height - pad}" stroke="#d7e0e2"/>
      <line x1="{pad}" y1="{height - pad}" x2="{width - pad}" y2="{height - pad}" stroke="#d7e0e2"/>
      <text x="{pad}" y="28" font-family="Arial" font-size="14" font-weight="700" fill="#162022">{title}</text>
      <text x="14" y="{height - pad + 4}" font-family="Arial" font-size="12" fill="#647174">0</text>
      <text x="8" y="{pad + 4}" font-family="Arial" font-size="12" fill="#647174">{max_value:.0f}</text>
      {"".join(legend)}
      {"".join(lines)}
    </svg>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
