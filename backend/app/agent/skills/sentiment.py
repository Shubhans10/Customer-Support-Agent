import json
import os
from langchain_core.tools import tool

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def _load_equipment() -> list[dict]:
    with open(os.path.join(DATA_DIR, "equipment.json"), "r") as f:
        return json.load(f)


@tool
def equipment_status(query: str) -> str:
    """Check the status, health, and sensor readings of manufacturing equipment.
    Use this tool when someone asks about machine status, sensor data,
    maintenance schedules, or equipment availability.
    The query can be a machine ID (e.g., 'CNC-001'), machine type (e.g., 'CNC'),
    or a status filter (e.g., 'operational', 'maintenance', 'warning', 'offline').
    """
    equipment = _load_equipment()
    query_lower = query.lower().strip()

    # Search by machine ID
    for machine in equipment:
        if machine["machine_id"].lower() == query_lower:
            sensors = machine["sensor_readings"]
            sensor_summary = ", ".join(
                f"{k}: {v}" for k, v in sensors.items()
            )
            return json.dumps({
                "found": True,
                "machine": machine,
                "summary": (
                    f"Machine {machine['machine_id']} ({machine['name']}). "
                    f"Type: {machine['type']}. Status: {machine['status'].upper()}. "
                    f"Location: {machine['location']}. "
                    f"Utilization: {machine['utilization_pct']}%. "
                    f"Hours: {machine['hours_run']}. "
                    f"Last maintenance: {machine['last_maintenance']}. "
                    f"Next maintenance: {machine['next_maintenance']}. "
                    f"Sensors: {sensor_summary}. "
                    + (f"Active WOs: {', '.join(machine['active_work_orders'])}. " if machine['active_work_orders'] else "No active work orders. ")
                    + (f"Notes: {machine['notes']}" if machine['notes'] else "")
                )
            }, indent=2)

    # Search by status
    status_matches = [m for m in equipment if query_lower == m["status"].lower()]
    if status_matches:
        results = []
        for m in status_matches:
            results.append({
                "machine_id": m["machine_id"],
                "name": m["name"],
                "type": m["type"],
                "utilization_pct": m["utilization_pct"],
                "next_maintenance": m["next_maintenance"],
                "active_work_orders": m["active_work_orders"]
            })
        return json.dumps({
            "found": True,
            "count": len(results),
            "machines": results,
            "summary": f"Found {len(results)} machine(s) with status '{query}'."
        }, indent=2)

    # Search by type
    type_matches = [m for m in equipment if query_lower in m["type"].lower() or query_lower in m["name"].lower()]
    if type_matches:
        results = []
        for m in type_matches:
            results.append({
                "machine_id": m["machine_id"],
                "name": m["name"],
                "status": m["status"],
                "utilization_pct": m["utilization_pct"],
                "active_work_orders": m["active_work_orders"]
            })
        return json.dumps({
            "found": True,
            "count": len(results),
            "machines": results,
            "summary": f"Found {len(results)} machine(s) matching '{query}'."
        }, indent=2)

    return json.dumps({
        "found": False,
        "summary": f"No equipment found matching '{query}'. Try a machine ID (e.g., CNC-001), type (CNC, 3D Printer), or status (operational, maintenance)."
    })
