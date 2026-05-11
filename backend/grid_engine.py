from random import uniform
from datetime import datetime

grid_state_memory = {
    "solar_output": 55.0,
    "wind_output": 28.0,
    "load_demand": 85.0,
    "grid_frequency": 50.0,
    "grid_voltage": 232.0,
    "battery_soc": 65.0,
}


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def trend_direction(new_value, old_value):
    if new_value > old_value:
        return 1
    if new_value < old_value:
        return -1
    return 0


def generate_grid_data(control_state=None):
    if control_state is None:
        control_state = {}

    previous_load = grid_state_memory["load_demand"]
    previous_voltage = grid_state_memory["grid_voltage"]
    previous_battery = grid_state_memory["battery_soc"]

    solar_output = grid_state_memory["solar_output"] + uniform(-1.2, 1.2)
    wind_output = grid_state_memory["wind_output"] + uniform(-1.0, 1.0)
    load_demand = grid_state_memory["load_demand"] + uniform(-1.5, 1.5)

    if control_state.get("renewable_boost"):
        solar_output += 7
        wind_output += 5

    if control_state.get("manual_load_reduction"):
        load_demand -= 8

    if control_state.get("emergency_mode"):
        load_demand -= 15

    solar_output = clamp(solar_output, 20, 130)
    wind_output = clamp(wind_output, 10, 95)
    load_demand = clamp(load_demand, 25, 140)

    total_generation = round(solar_output + wind_output, 2)
    power_balance = round(total_generation - load_demand, 2)

    grid_frequency = grid_state_memory["grid_frequency"] + uniform(-0.02, 0.02)
    grid_voltage = grid_state_memory["grid_voltage"] + uniform(-0.5, 0.5)

    if power_balance < -15:
        grid_frequency -= 0.06
        grid_voltage -= 1.4
    elif power_balance > 15:
        grid_frequency += 0.03
        grid_voltage += 0.8

    if control_state.get("ai_auto_stabilization"):
        grid_frequency += (50.0 - grid_frequency) * 0.45
        grid_voltage += (232.0 - grid_voltage) * 0.35

    grid_frequency = clamp(grid_frequency, 49.5, 50.5)
    grid_voltage = clamp(grid_voltage, 215, 245)

    battery_soc = grid_state_memory["battery_soc"]

    if power_balance > 5:
        battery_soc += 1.8
        battery_mode = "CHARGING"
    elif power_balance < -5:
        battery_soc -= 1.8
        battery_mode = "DISCHARGING"
    else:
        battery_mode = "STABLE"

    if control_state.get("battery_priority"):
        battery_soc += 5
        battery_mode = "PRIORITY CHARGING"

    if control_state.get("emergency_mode"):
        battery_soc -= 0.5

    battery_soc = clamp(battery_soc, 20, 100)

    voltage_trend = trend_direction(grid_voltage, previous_voltage)
    load_trend = trend_direction(load_demand, previous_load)
    battery_trend = trend_direction(battery_soc, previous_battery)

    grid_state_memory["solar_output"] = solar_output
    grid_state_memory["wind_output"] = wind_output
    grid_state_memory["load_demand"] = load_demand
    grid_state_memory["grid_frequency"] = grid_frequency
    grid_state_memory["grid_voltage"] = grid_voltage
    grid_state_memory["battery_soc"] = battery_soc

    solar_output = round(solar_output, 2)
    wind_output = round(wind_output, 2)
    load_demand = round(load_demand, 2)
    grid_frequency = round(grid_frequency, 2)
    grid_voltage = round(grid_voltage, 2)
    battery_soc = round(battery_soc)

    alerts = []

    if total_generation < load_demand:
        alerts.append("GENERATION DEFICIT")

    if grid_voltage < 225:
        alerts.append("LOW VOLTAGE")

    if grid_frequency < 49.8:
        alerts.append("FREQUENCY INSTABILITY")

    if control_state.get("emergency_mode"):
        alerts.append("EMERGENCY MODE ACTIVE")

    if control_state.get("manual_load_reduction"):
        alerts.append("LOAD REDUCTION ACTIVE")

    if control_state.get("renewable_boost"):
        alerts.append("RENEWABLE BOOST ACTIVE")

    grid_state = "STABLE" if len(alerts) == 0 else "WARNING"

    grid_efficiency = round((total_generation / max(load_demand, 1)) * 100, 2)
    power_balance = round(total_generation - load_demand, 2)

    power_balance_status = (
        "SURPLUS POWER"
        if power_balance >= 0
        else "POWER DEFICIT"
    )

    if grid_efficiency >= 120:
        efficiency_status = "SURPLUS"
    elif grid_efficiency >= 90:
        efficiency_status = "BALANCED"
    else:
        efficiency_status = "STRESSED"

    overload_risk = round((load_demand / max(total_generation, 1)) * 50, 2)
    overload_risk = min(overload_risk, 100)

    instability_score = 0

    if grid_frequency < 49.8:
        instability_score += 30

    if grid_voltage < 225:
        instability_score += 25

    if total_generation < load_demand:
        instability_score += 35

    if battery_soc < 40:
        instability_score += 10

    instability_score = min(instability_score, 100)

    if control_state.get("battery_priority"):
        instability_score = max(0, instability_score - 20)

    if control_state.get("ai_auto_stabilization"):
        instability_score = max(0, instability_score - 15)

    if control_state.get("emergency_mode"):
        instability_score = max(0, instability_score - 30)

    health_score = 100
    health_score -= overload_risk * 0.3
    health_score -= instability_score * 0.4
    health_score -= len([a for a in alerts if "ACTIVE" not in a]) * 10

    if grid_efficiency < 100:
        health_score -= (100 - grid_efficiency) * 0.2

    if control_state.get("battery_priority"):
        health_score += 8

    if control_state.get("ai_auto_stabilization"):
        health_score += 10

    if control_state.get("manual_load_reduction"):
        health_score += 12

    if control_state.get("renewable_boost"):
        health_score += 12

    if control_state.get("emergency_mode"):
        health_score += 18

    health_score = round(max(0, min(100, health_score)), 2)

    if health_score >= 80:
        health_status = "EXCELLENT"
    elif health_score >= 60:
        health_status = "MODERATE RISK"
    else:
        health_status = "CRITICAL"

    forecast_load_kw = round(load_demand + uniform(-2, 5), 2)
    forecast_generation_kw = round(total_generation + uniform(-3, 3), 2)

    if control_state.get("manual_load_reduction"):
        forecast_load_kw -= 8

    if control_state.get("renewable_boost"):
        forecast_generation_kw += 10

    if control_state.get("emergency_mode"):
        forecast_load_kw -= 15

    forecast_load_kw = round(clamp(forecast_load_kw, 25, 140), 2)
    forecast_generation_kw = round(clamp(forecast_generation_kw, 20, 220), 2)

    forecast_balance_kw = round(forecast_generation_kw - forecast_load_kw, 2)

    blackout_risk_score = 0

    if forecast_balance_kw < 0:
        blackout_risk_score += 35

    if battery_soc < 35:
        blackout_risk_score += 25

    if instability_score >= 50:
        blackout_risk_score += 25

    if grid_voltage < 225:
        blackout_risk_score += 15

    if control_state.get("battery_priority"):
        blackout_risk_score -= 15

    if control_state.get("manual_load_reduction"):
        blackout_risk_score -= 20

    if control_state.get("renewable_boost"):
        blackout_risk_score -= 20

    if control_state.get("emergency_mode"):
        blackout_risk_score -= 30

    if control_state.get("ai_auto_stabilization"):
        blackout_risk_score -= 15

    blackout_risk_score = max(0, min(100, blackout_risk_score))

    if blackout_risk_score >= 70:
        blackout_risk_level = "HIGH"
    elif blackout_risk_score >= 40:
        blackout_risk_level = "MEDIUM"
    else:
        blackout_risk_level = "LOW"

    forecast_confidence = round(100 - (instability_score * 0.4), 2)
    forecast_window_seconds = 30

    active_controls = [
        name for name, enabled in control_state.items()
        if enabled
    ]

    if control_state.get("emergency_mode"):
        ai_recommendation = "Emergency stabilization active. Non-critical demand is being reduced."
    elif control_state.get("manual_load_reduction"):
        ai_recommendation = "Manual load reduction active. Demand is being reduced to protect the grid."
    elif control_state.get("renewable_boost"):
        ai_recommendation = "Renewable boost active. Generation support has been increased."
    elif control_state.get("battery_priority"):
        ai_recommendation = "Battery priority active. Storage reserve is being protected."
    elif instability_score >= 50:
        ai_recommendation = "Increase battery discharge or reduce non-critical load"
    else:
        ai_recommendation = "Grid conditions normal. Continue monitoring"

    return {
        "timestamp": datetime.now().isoformat(),

        "renewables": {
            "solar_kw": solar_output,
            "wind_kw": wind_output,
            "total_generation_kw": total_generation
        },

        "grid": {
            "load_demand_kw": load_demand,
            "frequency_hz": grid_frequency,
            "voltage_v": grid_voltage,
            "state": grid_state,
            "alerts": alerts,
            "efficiency_percent": grid_efficiency,
            "efficiency_status": efficiency_status,
            "power_balance_kw": power_balance,
            "power_balance_status": power_balance_status
        },

        "battery": {
            "state_of_charge_percent": battery_soc,
            "mode": battery_mode
        },

        "trends": {
            "voltage": voltage_trend,
            "load": load_trend,
            "battery": battery_trend
        },

        "forecast": {
            "window_seconds": forecast_window_seconds,
            "projected_load_kw": forecast_load_kw,
            "projected_generation_kw": forecast_generation_kw,
            "projected_balance_kw": forecast_balance_kw,
            "blackout_risk_score": blackout_risk_score,
            "blackout_risk_level": blackout_risk_level,
            "confidence_percent": forecast_confidence
        },

        "controls": {
            "active_controls": active_controls
        },

        "ai_prediction": {
            "overload_risk_percent": overload_risk,
            "instability_score_percent": instability_score,
            "recommendation": ai_recommendation,
            "health_score": health_score,
            "health_status": health_status
        }
    }