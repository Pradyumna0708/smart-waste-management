# Deployment & Presentation Guide — Smart Waste Management System

How to run the system continuously in the background and present it for evaluation or GitHub demos. Based on the **current** stack: Mosquitto, Node-RED with custom `ui_template` dashboard, Python simulator, and local SQLite.

---

## Part 1 — Local deployment as background services

### 1. Mosquitto broker (Windows service)

The Mosquitto installer registers a Windows service by default.

1. Press `Win + R`, type `services.msc`, press Enter.
2. Find **Mosquitto Broker**.
3. Set **Startup type** to **Automatic**.

Verify anytime:
```cmd
netstat -an | findstr 1883
```

### 2. Node-RED with PM2

[PM2](https://pm2.keymetrics.io/) keeps Node-RED running without an open terminal.

```powershell
npm install -g pm2
pm2 start $env:APPDATA\npm\node-red.cmd --name "node-red"
```

Adjust the path if your global npm bin directory differs. Common alternatives:

```text
C:\Users\<Your-Username>\AppData\Roaming\npm\node-red.cmd
```

**Useful PM2 commands:**

| Command | Action |
| :--- | :--- |
| `pm2 list` | Show running processes |
| `pm2 logs node-red` | Stream Node-RED logs |
| `pm2 stop node-red` | Stop Node-RED |
| `pm2 restart node-red` | Restart after flow changes |

For boot-time startup on Windows, consider `pm2-windows-service` (optional third-party package).

After starting Node-RED via PM2, ensure `node_red/waste_flow.json` is imported and deployed, and the SQLite path points to your machine.

### 3. Python simulator in the background (Windows)

**Option A — `pythonw` (no console window)**

```powershell
pythonw simulator/bin_simulator.py
```

Stop via Task Manager → end the **Python** background process.

**Option B — PM2**

```powershell
pm2 start simulator/bin_simulator.py --name "waste-sim" --interpreter python
```

Requires the Python interpreter on PATH and an activated venv path if dependencies are venv-only.

### 4. Runtime dependencies

| Component | Port | Notes |
| :--- | :--- | :--- |
| Mosquitto | 1883 | MQTT broker |
| Node-RED editor | 1880 | Flow configuration |
| Dashboard | 1880/ui/ | Custom template UI |
| Internet | — | Required for CDN (Chart.js, Leaflet, map tiles, fonts) |

---

## Part 2 — Academic presentation and demo script

### Suggested slide structure

1. **Title** — Smart Waste Management System (Pune simulation)
2. **Problem** — Overflowing bins, reactive routing, no historical telemetry
3. **Architecture** — Simulator → MQTT → Node-RED → SQLite → Dashboard
4. **Features** — Real-time monitoring, status classification, map view, alerts
5. **Implementation** — Python, Paho MQTT, Mosquitto, Node-RED, SQLite, Chart.js, Leaflet
6. **Future scope** — Route optimization, predictive analytics, notifications

### Live demonstration script

#### 1. Show project structure

Open the repository and highlight:

- `simulator/bin_simulator.py` — telemetry source
- `node_red/waste_flow.json` — processing and dashboard wiring
- `node_red/dashboard.html` — custom UI source
- `sql/database_schema.sql` — persistence schema
- `waste_management.db` — live data file

#### 2. Start the simulator (visible terminal)

```powershell
python simulator/bin_simulator.py
```

Point out JSON payloads, 5-second interval, gradual fill, and collection resets above 85%.

#### 3. Show Node-RED backend

Open [http://localhost:1880](http://localhost:1880):

- **Subscribe Bins** — MQTT topic `waste/bin/data`
- **Calculate Status** — Normal / Warning / Critical rules
- **Save to SQLite** — INSERT into `waste_data`
- **Custom Beautiful Dashboard** — single `ui_template` driving the entire UI
- **Route History Requests** — loads last 200 records on dashboard open

Mention the SQLite path must match the local `waste_management.db` location.

#### 4. Prove database persistence

```powershell
python -c "import sqlite3; c=sqlite3.connect('waste_management.db'); r=c.cursor(); r.execute('SELECT bin_id, fill_level, status, timestamp FROM waste_data ORDER BY id DESC LIMIT 5'); [print(x) for x in r.fetchall()]"
```

#### 5. Open the dashboard

Navigate to [http://localhost:1880/ui/](http://localhost:1880/ui/):

| Tab | Demo points |
| :--- | :--- |
| **Overview** | KPI cards, live table, compact map, fill trend chart |
| **Bin Monitoring** | Full detail table with coordinates and timestamps |
| **Bin Locations Map** | Fullscreen Leaflet map; click markers for popups |
| **Analytics & Trends** | Large chart with legend and 80% threshold line |

#### 6. Trigger a live alert

Wait for a bin to exceed **80%** fill:

- Red toast: `Critical Threshold Alert`
- Critical KPI and red map marker update
- Status pill shows `Critical`

Then wait for simulator collection (triggered at **>85%**):

- Console shows `[TRUCK COLLECTED]`
- Fill level drops on charts and map returns to green

### Key talking points

- **No physical sensors** — simulator replaces hardware for reproducible demos
- **No cloud** — entirely local MQTT, Node-RED, and SQLite
- **Custom dashboard** — one `ui_template` replaces multiple legacy dashboard widgets
- **Status vs collection thresholds** — dashboard alerts at >80%; simulator schedules collection at >85%

### Pre-demo checklist

| Item | Status |
| :--- | :--- |
| Mosquitto running on 1883 | ☐ |
| Node-RED running on 1880 | ☐ |
| Flow imported and deployed | ☐ |
| SQLite path configured | ☐ |
| Simulator running | ☐ |
| Internet available (CDN/maps) | ☐ |
| Browser tab on `/ui/` ready | ☐ |
