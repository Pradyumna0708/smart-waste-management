# Testing & Verification Guide — Smart Waste Management System

Procedures to verify each component against the **current** implementation.

---

## 1. Verify the Python simulator and MQTT connection

1. Ensure Mosquitto is running.
2. Activate the virtual environment and start the simulator:
   ```powershell
   cd d:\smart-waste-management
   .\venv\Scripts\Activate.ps1
   python simulator/bin_simulator.py
   ```

### Expected startup output

```text
================================================================================
           SMART WASTE MANAGEMENT SYSTEM - SIMULATOR STARTED
================================================================================
MQTT Broker: localhost:1883
Topic:       waste/bin/data
Interval:    5 seconds
--------------------------------------------------------------------------------
Simulated Bins:
 - BIN001: Pune (Kothrud) (Lat: 18.5074, Lon: 73.8077)
 - BIN002: Pune (Koregaon Park) (Lat: 18.5362, Lon: 73.8940)
 - BIN003: Pune (Shivajinagar) (Lat: 18.5314, Lon: 73.8446)
 - BIN004: Pune (Viman Nagar) (Lat: 18.5679, Lon: 73.9143)
 - BIN005: Pune (Hadapsar) (Lat: 18.5089, Lon: 73.9260)
--------------------------------------------------------------------------------

[SYSTEM] Connected successfully to MQTT Broker at localhost:1883
```

### Expected per-cycle output

Every 5 seconds, five JSON messages are published (one per bin):

```text
--- [Cycle #1] Generating & Publishing Data ---
 * BIN001 (Pune (Kothrud)): Fill Level increased to 22% (+12%)
   Published to waste/bin/data: {"bin_id": "BIN001", "fill_level": 22, "weight": 11, "latitude": 18.5074, "longitude": 73.8077, "timestamp": "2026-06-23 20:15:32"}
```

### Collection simulation

When a bin exceeds **85%** fill:

```text
 [ALERT TRIGGERED] BIN003 is full (90%). Truck scheduled in 2 cycles.
 * BIN003 (Pune (Shivajinagar)): WAITING COLLECTION (Level: 90%, Cycles Left: 1)
 [TRUCK COLLECTED] Emptying BIN003 in Pune (Shivajinagar). Level reset to 3%
```

---

## 2. Verify the SQLite database logs

Node-RED writes each message to `waste_management.db` after status calculation.

1. Run the simulator for at least 15–20 seconds with Node-RED deployed.
2. Query the latest rows:
   ```powershell
   python -c "import sqlite3; conn = sqlite3.connect('waste_management.db'); cur = conn.cursor(); cur.execute('SELECT * FROM waste_data ORDER BY id DESC LIMIT 5'); [print(row) for row in cur.fetchall()]; conn.close()"
   ```

### Expected output shape

```text
(6410, 'BIN005', 42, 22, 18.5089, 73.926, '2026-06-23 20:15:32', 'Normal')
(6409, 'BIN004', 58, 30, 18.5679, 73.9143, '2026-06-23 20:15:32', 'Warning')
(6408, 'BIN003', 89, 45, 18.5314, 73.8446, '2026-06-23 20:15:32', 'Critical')
```

Tuple order: `(id, bin_id, fill_level, weight, latitude, longitude, timestamp, status)`

### Status values to expect

| Fill Level | Status |
| :--- | :--- |
| 0–50% | `Normal` |
| 51–80% | `Warning` |
| > 80% | `Critical` |

---

## 3. Verify the Node-RED flow

Open [http://localhost:1880](http://localhost:1880) and confirm the **Smart Waste Flow** tab contains:

| Node | Type | Role |
| :--- | :--- | :--- |
| Subscribe Bins | `mqtt in` | Subscribes to `waste/bin/data` |
| Parse JSON | `json` | Parses MQTT payload |
| Calculate Status | `function` | Adds `status` field |
| Build SQL Query | `function` | Builds `INSERT` statement |
| Save to SQLite | `sqlite` | Writes to `waste_data` |
| Custom Beautiful Dashboard | `ui_template` | Renders custom UI |
| Route History Requests | `function` | Fetches history on dashboard load |
| Format History Response | `function` | Formats SQLite query results |

With the simulator running, wires should show activity on the MQTT and function nodes.

---

## 4. Verify the dashboard interface

Open [http://localhost:1880/ui/](http://localhost:1880/ui/)

The page uses a custom sidebar (not the default Node-RED dashboard drawer). Test all four tabs:

### Tab 1 — Overview

| Element | Verification |
| :--- | :--- |
| Total Monitored Bins | Shows `5` |
| Normal / Warning / Critical KPIs | Update as fill levels change |
| System Diagnostics | Total records and last updated time refresh |
| Live Telemetry Table | 5 rows; fill, weight, status update every ~5 s |
| Live Pune Map View | 5 markers around Pune; colors match status |
| Fill Level Telemetry Trends | Line chart with 5 bin series and 80% threshold |

### Tab 2 — Bin Monitoring

| Element | Verification |
| :--- | :--- |
| Full table | 8 columns including location, coordinates, timestamp |
| 5 rows | One per bin ID |
| Status pills | Green / orange / red styling |

### Tab 3 — Bin Locations Map

| Element | Verification |
| :--- | :--- |
| Fullscreen map | Centered on Pune, zoom 12 |
| 5 circle markers | Kothrud, Koregaon Park, Shivajinagar, Viman Nagar, Hadapsar |
| Marker colors | Green (Normal), orange (Warning), red (Critical) |
| Popup on click | Bin ID, fill %, weight, status |

Map tiles require internet access (CartoDB CDN).

### Tab 4 — Analytics & Trends

| Element | Verification |
| :--- | :--- |
| Large fill level chart | Same trend data as Overview, with visible legend |
| 80% threshold line | Red dashed horizontal reference |
| Legend toggle | Click legend items to hide/show bin lines |

> **Note:** The current dashboard charts **fill level only**. A separate weight trend chart exists in the legacy `waste_flow.json.bak` but not in the active flow.

---

## 5. Test alerts and collection resets

### Toast alerts (dashboard, threshold > 80%)

1. Let the simulator run until a bin exceeds 80% fill.
2. A red toast appears top-right:
   `Critical Threshold Alert — BIN00X (Pune (...)) is full at NN%!`
3. Toast auto-dismisses after 8 seconds or closes via ×.
4. Map marker and status pill turn red; Critical KPI increments.

### Collection reset (simulator, threshold > 85%)

1. Watch the simulator console for `WAITING COLLECTION` messages.
2. After 1–2 cycles, `[TRUCK COLLECTED]` resets fill to 0–10%.
3. Dashboard chart shows a drop; toast clears when fill ≤ 80%.

---

## 6. Verify history load on dashboard refresh

On page load, the dashboard sends `fetch_history` to Node-RED, which queries:

- Last 200 records from `waste_data`
- Total `COUNT(*)` for diagnostics

Refresh the browser with the simulator stopped. Previously stored data should still populate charts and tables from SQLite.

---

## Common failure indicators

| Symptom | Likely cause |
| :--- | :--- |
| Simulator connection loop | Mosquitto not running |
| No SQLite rows | Flow not deployed or wrong DB path |
| Blank `/ui/` page | `node-red-dashboard` not installed |
| Empty map | No internet for CDN/tiles, or no data yet |
| Unknown node types on import | Missing `node-red-node-sqlite` |

See [README.md](../README.md#troubleshooting) for fixes.
