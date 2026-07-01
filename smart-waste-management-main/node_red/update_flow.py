import json
import os

def main():
    flow_file = "node_red/waste_flow.json.bak"
    output_file = "node_red/waste_flow.json"
    html_file = "node_red/dashboard.html"

    if not os.path.exists(flow_file):
        print(f"[ERROR] Backup flow file {flow_file} not found!")
        return
    if not os.path.exists(html_file):
        print(f"[ERROR] HTML file {html_file} not found!")
        return

    with open(flow_file, 'r', encoding='utf-8') as f:
        nodes = json.load(f)

    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # We will identify the configurations to keep
    keep_types = {
        "tab",
        "ui_base",
        "ui_tab",
        "mqtt-broker",
        "sqlitedb",
        "mqtt in",
        "json",
    }
    
    keep_ids = {
        "sheet_waste_flow",
        "ui_base_node",
        "tab_overview",
        "mqtt_broker_config",
        "sqlite_db_config",
        "mqtt_in_node",
        "json_parser_node",
        "status_calc_node",
        "sql_query_builder",
        "sqlite_database_node",
    }

    # Filter original nodes to keep the core infrastructure
    new_nodes = []
    status_calc_node = None
    sqlite_db_node = None
    sql_query_node = None

    for node in nodes:
        node_id = node.get("id")
        node_type = node.get("type")
        
        if node_id in keep_ids or node_type in keep_types:
            # We want to keep this node, but we might clean its wires or modify it
            if node_id == "ui_base_node":
                # Overwrite ui_base_node to have valid site configuration with sizes
                node = {
                    "id": "ui_base_node",
                    "type": "ui_base",
                    "theme": {
                        "name": "theme-dark"
                    },
                    "site": {
                        "name": "Smart Waste Dashboard",
                        "hideToolbar": "false",
                        "allowSwipe": "false",
                        "lockAxis": "true",
                        "sizes": {
                            "sx": 48,
                            "sy": 48,
                            "gx": 6,
                            "gy": 6,
                            "cx": 6,
                            "cy": 6,
                            "px": 0,
                            "py": 0
                        }
                    }
                }
            elif node_id == "status_calc_node":
                status_calc_node = node
            elif node_id == "sqlite_database_node":
                sqlite_db_node = node
            elif node_id == "sql_query_builder":
                sql_query_node = node
            
            # Remove legacy UI tabs other than tab_overview
            if node_type == "ui_tab" and node_id != "tab_overview":
                continue
                
            new_nodes.append(node)

    # 1. Update status_calc_node wiring
    # It must connect to sql_query_builder and ui_custom_dashboard
    if status_calc_node:
        status_calc_node["wires"] = [["sql_query_builder", "ui_custom_dashboard"]]
        print("[INFO] Updated status_calc_node wires.")

    # 2. Update sqlite_database_node wiring
    # It must output to history_response_formatter
    if sqlite_db_node:
        sqlite_db_node["wires"] = [["history_response_formatter"]]
        print("[INFO] Updated sqlite_database_node wires.")

    # 3. Create the new dashboard group node
    dashboard_group = {
        "id": "group_dashboard",
        "type": "ui_group",
        "name": "Waste Dashboard Group",
        "tab": "tab_overview",
        "order": 1,
        "disp": False, # hide group header
        "width": "12",
        "collapse": False
    }
    new_nodes.append(dashboard_group)
    print("[INFO] Added group_dashboard.")

    # 4. Create the custom template node (ui_custom_dashboard)
    # It receives msg from status_calc_node and history_response_formatter
    # It outputs to history_request_router
    custom_dashboard = {
        "id": "ui_custom_dashboard",
        "type": "ui_template",
        "z": "sheet_waste_flow",
        "group": "group_dashboard",
        "name": "Custom Beautiful Dashboard",
        "order": 1,
        "width": "12",
        "height": "20",
        "format": html_content,
        "storeOutMessages": False,
        "fwdInMessages": False,
        "resendOnRefresh": False,
        "templateScope": "local",
        "x": 670,
        "y": 380,
        "wires": [["history_request_router"]]
    }
    new_nodes.append(custom_dashboard)
    print("[INFO] Added ui_custom_dashboard template node.")

    # 5. Create the history_request_router function node
    history_request_router = {
        "id": "history_request_router",
        "type": "function",
        "z": "sheet_waste_flow",
        "name": "Route History Requests",
        "func": 'if (msg.payload === "fetch_history") {\n    // Output 1: Query historical data\n    let msg1 = {\n        topic: "SELECT bin_id, fill_level, weight, latitude, longitude, timestamp FROM waste_data ORDER BY id DESC LIMIT 200",\n        query_type: "history"\n    };\n    // Output 2: Query total count of records\n    let msg2 = {\n        topic: "SELECT COUNT(*) AS total_records FROM waste_data",\n        query_type: "count"\n    };\n    return [msg1, msg2];\n}\nreturn null;',
        "outputs": 2,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 420,
        "y": 440,
        "wires": [
            ["sqlite_database_node"],
            ["sqlite_database_node"]
        ]
    }
    new_nodes.append(history_request_router)
    print("[INFO] Added history_request_router node.")

    # 6. Create the history_response_formatter function node
    history_response_formatter = {
        "id": "history_response_formatter",
        "type": "function",
        "z": "sheet_waste_flow",
        "name": "Format History Response",
        "func": 'if (msg.query_type === "history") {\n    msg.payload = {\n        type: "history",\n        data: msg.payload\n    };\n    return msg;\n} else if (msg.query_type === "count") {\n    msg.payload = {\n        type: "count",\n        value: msg.payload[0].total_records\n    };\n    return msg;\n}\nreturn null;',
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 880,
        "y": 320,
        "wires": [["ui_custom_dashboard"]]
    }
    new_nodes.append(history_response_formatter)
    print("[INFO] Added history_response_formatter node.")

    # Save to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_nodes, f, indent=4, ensure_ascii=False)

    print(f"[SUCCESS] Upgraded flow written to {output_file}")

if __name__ == "__main__":
    main()
