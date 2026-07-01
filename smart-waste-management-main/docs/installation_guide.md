# Installation Guide — Smart Waste Management System

Step-by-step setup for running the project on a local Windows machine. All steps reflect the **current** implementation: Python simulator, Mosquitto, Node-RED with `node-red-dashboard` and `node-red-node-sqlite`, and the custom `ui_template` dashboard in `node_red/waste_flow.json`.

---

## Prerequisites

| Software | Purpose |
| :--- | :--- |
| Python 3.x | Run `simulator/bin_simulator.py` |
| Node.js + npm | Run Node-RED |
| Mosquitto MQTT Broker | Message bus on port 1883 |
| Internet connection | CDN assets (Chart.js, Leaflet, map tiles, fonts) |

---

## Step 1 — Clone and prepare Python environment

1. Clone the repository and open a terminal in the project folder:
   ```powershell
   cd d:\smart-waste-management
   ```

2. Create a virtual environment:
   ```powershell
   python -m venv venv
   ```

3. Activate it:
   - **PowerShell:**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
     If execution policy blocks scripts:
     ```powershell
     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
     .\venv\Scripts\Activate.ps1
     ```
   - **CMD:**
     ```cmd
     .\venv\Scripts\activate.bat
     ```

4. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
   This installs `paho-mqtt<2.0.0`.

---

## Step 2 — Install Mosquitto MQTT Broker

1. Download the Windows installer from [mosquitto.org/download](https://mosquitto.org/download/) (64-bit recommended).
2. Run the installer (default path: `C:\Program Files\mosquitto`).
3. The installer registers Mosquitto as a Windows service.
4. Verify the broker is listening:
   ```cmd
   netstat -an | findstr 1883
   ```
   Expect a line with `LISTENING` on port `1883`.

---

## Step 3 — Install Node.js and Node-RED

1. Install Node.js LTS from [nodejs.org](https://nodejs.org/).
2. Verify:
   ```powershell
   node --version
   npm --version
   ```
3. Install Node-RED globally:
   ```powershell
   npm install -g --unsafe-perm node-red
   ```
4. Start Node-RED (keep this terminal open):
   ```powershell
   node-red
   ```
5. Open the editor at [http://localhost:1880](http://localhost:1880).

---

## Step 4 — Install required Node-RED packages

The active flow requires **two** packages:

| Package | Purpose |
| :--- | :--- |
| `node-red-dashboard` | Hosts `ui_template`, `ui_base`, `ui_tab`, `ui_group` |
| `node-red-node-sqlite` | SQLite read/write nodes |

### Option A — Palette Manager (recommended)

1. In Node-RED: **Menu (☰) → Manage palette → Install**
2. Search and install:
   - `node-red-dashboard`
   - `node-red-node-sqlite`
3. Close the palette manager when both are installed.

### Option B — Command line

```powershell
cd $env:USERPROFILE\.node-red
npm install node-red-dashboard node-red-node-sqlite
```

Restart Node-RED after CLI installation.

> **Not required:** `node-red-contrib-web-worldmap` was used in the legacy flow (`waste_flow.json.bak`). The current dashboard embeds Leaflet.js directly in `dashboard.html`.

---

## Step 5 — Import and configure the Node-RED flow

1. Open `node_red/waste_flow.json` in a text editor and copy the full JSON.
2. In Node-RED: **Menu → Import**
3. Paste the JSON and select **Import to New Flow**
4. A tab named **Smart Waste Flow** appears.

### Configure MQTT broker

The flow ships with broker config **Local Mosquitto**:

| Setting | Value |
| :--- | :--- |
| Host | `localhost` |
| Port | `1883` |

Double-click the **Subscribe Bins** MQTT In node only if your broker runs on a different host or port.

### Configure SQLite database path (required if not using default path)

The flow default database path is:

```text
D:/smart-waste-management/waste_management.db
```

If your project lives elsewhere:

1. Double-click the **Save to SQLite** node
2. Click the pencil icon next to the database configuration
3. Set **Path** to your absolute `waste_management.db` path (forward slashes work on Windows)
4. Click **Update** → **Done**

### Initialize schema (optional)

Node-RED creates the database file in `RWC` mode. To pre-create the schema:

```powershell
sqlite3 waste_management.db < sql/database_schema.sql
```

### Deploy

Click the red **Deploy** button in the top-right corner.

---

## Step 6 — Run the simulator

With Mosquitto and Node-RED running, and the flow deployed:

```powershell
cd d:\smart-waste-management
.\venv\Scripts\Activate.ps1
python simulator/bin_simulator.py
```

Expected startup output includes broker `localhost:1883`, topic `waste/bin/data`, interval `5` seconds, and all five Pune bin locations.

---

## Step 7 — Access the dashboard

Open [http://localhost:1880/ui/](http://localhost:1880/ui/)

The custom dashboard fills the page with four internal tabs:

- Overview
- Bin Monitoring
- Bin Locations Map
- Analytics & Trends

---

## Step 8 — (Developers) Regenerate flow after UI edits

If you modify `node_red/dashboard.html`:

```powershell
python node_red/update_flow.py
```

This reads `waste_flow.json.bak` and `dashboard.html`, then writes an updated `waste_flow.json`. Re-import or redeploy in Node-RED.

---

## Quick verification checklist

| Check | Expected result |
| :--- | :--- |
| `netstat -an \| findstr 1883` | Mosquitto listening |
| `http://localhost:1880` | Node-RED editor loads |
| Simulator console | `[SYSTEM] Connected successfully to MQTT Broker` |
| `http://localhost:1880/ui/` | Custom dark dashboard with sidebar |
| SQLite query (see testing guide) | New rows in `waste_data` every 5 seconds |

For detailed verification steps, see [testing_guide.md](testing_guide.md).
