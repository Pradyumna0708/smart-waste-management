# ==============================================================================
# SMART WASTE MANAGEMENT SYSTEM - GARBAGE BIN SIMULATOR
# ==============================================================================
# Description: Simulates 5 garbage bins across metropolitan cities in India.
#              Publishes telemetry data (fill level, weight, GPS coordinates)
#              to an MQTT Broker (Mosquitto) every 5 seconds.
#              Implements realistic gradual fill rates and collection cycles.
# Language:    Python 3.x
# Library:     paho-mqtt
# ==============================================================================

import time
import random
import json
import datetime
import sys
import paho.mqtt.client as mqtt

# --- CONFIGURATION ---
MQTT_BROKER = "localhost"    # MQTT Broker address (change if running remotely)
MQTT_PORT = 1883             # Standard Mosquitto MQTT port
MQTT_TOPIC = "waste/bin/data"# Topic to publish telemetry data
UPDATE_INTERVAL = 5          # Time between updates in seconds

# --- BIN GEOGRAPHICAL CONFIGURATION ---
# Fixed locations for neighborhoods within Pune city
BINS_CONFIG = {
    "BIN001": {"city": "Pune (Kothrud)", "lat": 18.5074, "lon": 73.8077},
    "BIN002": {"city": "Pune (Koregaon Park)", "lat": 18.5362, "lon": 73.8940},
    "BIN003": {"city": "Pune (Shivajinagar)", "lat": 18.5314, "lon": 73.8446},
    "BIN004": {"city": "Pune (Viman Nagar)", "lat": 18.5679, "lon": 73.9143},
    "BIN005": {"city": "Pune (Hadapsar)", "lat": 18.5089, "lon": 73.9260}
}

# --- STATE INITIALIZATION ---
# Track fill levels and collection cycles for each bin
bins_state = {}
for bin_id in BINS_CONFIG:
    bins_state[bin_id] = {
        "fill_level": random.randint(10, 30),  # Start with a random initial level
        "full_cycles_remaining": 0             # Cycles to stay full before reset (collection)
    }

# Initialize MQTT Client (using paho-mqtt 1.x API)
client = mqtt.Client()

def connect_to_broker():
    """Attempts to connect to the local MQTT broker with error handling."""
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print(f"\n[SYSTEM] Connected successfully to MQTT Broker at {MQTT_BROKER}:{MQTT_PORT}")
        return True
    except Exception as e:
        print(f"\n[ERROR] Connection failed to {MQTT_BROKER}:{MQTT_PORT} - {e}")
        print("[SYSTEM] Retrying in 5 seconds... (Ensure Mosquitto Broker service is running)")
        return False

# Main Execution Loop
def main():
    print("=" * 80)
    print("           SMART WASTE MANAGEMENT SYSTEM - SIMULATOR STARTED")
    print("=" * 80)
    print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Topic:       {MQTT_TOPIC}")
    print(f"Interval:    {UPDATE_INTERVAL} seconds")
    print("-" * 80)
    print("Simulated Bins:")
    for b_id, b_data in BINS_CONFIG.items():
        print(f" - {b_id}: {b_data['city']} (Lat: {b_data['lat']}, Lon: {b_data['lon']})")
    print("-" * 80)

    # Establish initial connection
    connected = False
    while not connected:
        connected = connect_to_broker()
        if not connected:
            time.sleep(5)

    client.loop_start()  # Start network loop in a background thread to handle auto-reconnects

    try:
        cycle = 1
        while True:
            print(f"\n--- [Cycle #{cycle}] Generating & Publishing Data ---")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for bin_id, geo in BINS_CONFIG.items():
                state = bins_state[bin_id]

                # 1. Gradual Fill & Collection Simulation Logic
                if state["full_cycles_remaining"] > 0:
                    # The bin is currently full and waiting for a garbage collection truck
                    state["full_cycles_remaining"] -= 1
                    print(f" * {bin_id} ({geo['city']}): WAITING COLLECTION (Level: {state['fill_level']}%, Cycles Left: {state['full_cycles_remaining']})")
                    
                    if state["full_cycles_remaining"] == 0:
                        # Collection truck arrived! Reset the bin to empty (0-10%)
                        state["fill_level"] = random.randint(0, 10)
                        print(f" [TRUCK COLLECTED] Emptying {bin_id} in {geo['city']}. Level reset to {state['fill_level']}%")
                else:
                    # Bin is accumulating waste gradually
                    # Increment fill level by 5% to 15% to simulate standard daily garbage throw
                    increment = random.randint(5, 15)
                    state["fill_level"] += increment
                    
                    # Cap fill level at 100%
                    if state["fill_level"] > 100:
                        state["fill_level"] = 100

                    print(f" * {bin_id} ({geo['city']}): Fill Level increased to {state['fill_level']}% (+{increment}%)")

                    # Check if the bin is now full (exceeds 85% threshold)
                    if state["fill_level"] > 85:
                        # Schedule collection after 1 to 2 cycles of being full
                        state["full_cycles_remaining"] = random.randint(1, 2)
                        print(f" [ALERT TRIGGERED] {bin_id} is full ({state['fill_level']}%). Truck scheduled in {state['full_cycles_remaining']} cycles.")

                # 2. Calculate Weight proportional to fill level with slight variation
                # Max bin capacity is assumed to be 50 kg
                max_capacity_kg = 50
                weight_fraction = state["fill_level"] / 100.0
                # Base weight + small random variance (1-3 kg) representing different types of garbage
                simulated_weight = int(weight_fraction * max_capacity_kg) + random.randint(1, 3)
                
                # Ensure weight is 0 if bin is completely empty
                if state["fill_level"] == 0:
                    simulated_weight = 0

                # 3. Create Payload
                payload = {
                    "bin_id": bin_id,
                    "fill_level": state["fill_level"],
                    "weight": simulated_weight,
                    "latitude": geo["lat"],
                    "longitude": geo["lon"],
                    "timestamp": timestamp
                }

                # 4. Publish via MQTT
                payload_str = json.dumps(payload)
                result = client.publish(MQTT_TOPIC, payload_str)
                
                # Check publish status
                status = result[0]
                if status == mqtt.MQTT_ERR_SUCCESS:
                    print(f"   Published to {MQTT_TOPIC}: {payload_str}")
                else:
                    print(f"   [MQTT ERROR] Failed to send message for {bin_id}")

            cycle += 1
            time.sleep(UPDATE_INTERVAL)

    except KeyboardInterrupt:
        print("\n[SYSTEM] Simulator stopped by user. Exiting...")
    finally:
        client.loop_stop()
        client.disconnect()
        print("[SYSTEM] Disconnected from MQTT Broker.")

if __name__ == "__main__":
    main()
