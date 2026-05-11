from fastapi import FastAPI, WebSocket
import asyncio

from grid_engine import generate_grid_data

app = FastAPI()

telemetry_history = []
MAX_HISTORY_SIZE = 100
event_log = []
MAX_EVENT_LOG_SIZE = 50

control_state = {
    "emergency_mode": False,
    "battery_priority": False,
    "ai_auto_stabilization": True,
    "manual_load_reduction": False,
    "renewable_boost": False
}


def store_telemetry(data):
    telemetry_history.append(data)

    if len(telemetry_history) > MAX_HISTORY_SIZE:
        telemetry_history.pop(0)

def store_event(message):
    from datetime import datetime

    event_log.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "message": message
    })

    if len(event_log) > MAX_EVENT_LOG_SIZE:
        event_log.pop(0)


@app.get("/")
def home():
    return {
        "platform": "MyGrid AI",
        "status": "Backend running"
    }


@app.get("/grid/status")
def grid_status():
    data = generate_grid_data(control_state)
    data["control_state"] = control_state
    store_telemetry(data)
    return data


@app.get("/grid/history")
def grid_history():
    return {
        "history_count": len(telemetry_history),
        "history": telemetry_history
    }

@app.get("/grid/events")
def get_events():
    return {
        "event_count": len(event_log),
        "events": event_log
    }

@app.get("/grid/controls")
def get_controls():
    return control_state


@app.post("/grid/controls/{control_name}")
def toggle_control(control_name: str):

    if control_name not in control_state:
        return {
            "error": "Invalid control name"
        }

    control_state[control_name] = not control_state[control_name]

    status = (
        "activated"
        if control_state[control_name]
        else "deactivated"
    )

    readable_name = control_name.replace("_", " ").title()

    store_event(f"{readable_name} {status}")

    return {
        "control": control_name,
        "new_value": control_state[control_name],
        "all_controls": control_state
    }


@app.get("/alerts")
def get_alerts():
    data = generate_grid_data(control_state)
    data["control_state"] = control_state
    store_telemetry(data)

    return {
        "timestamp": data["timestamp"],
        "grid_state": data["grid"]["state"],
        "active_alerts": data["grid"]["alerts"],
        "alert_count": len(data["grid"]["alerts"])
    }


@app.websocket("/ws/grid")
async def websocket_grid(websocket: WebSocket):
    await websocket.accept()

    while True:
        data = generate_grid_data(control_state)
        data["control_state"] = control_state
        data["events"] = event_log
        store_telemetry(data)
        await websocket.send_json(data)
        await asyncio.sleep(2)