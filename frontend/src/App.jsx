import { Zap } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import "./App.css";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";

function App() {
  const [gridData, setGridData] = useState(null);
  const [history, setHistory] = useState([]);
  const [controls, setControls] = useState({});
  const [events, setEvents] = useState([]);

  const fetchEvents = useCallback(async () => {
    const response = await fetch("https://mygrid-ai-backend.onrender.com/grid/events");
    const data = await response.json();
    setEvents(data.events || []);
  }, []);

  const toggleControl = async (controlName) => {
    const response = await fetch(
      `https://mygrid-ai-backend.onrender.com/grid/controls/${controlName}`,
      {
        method: "POST",
      }
    );

    const data = await response.json();

    setControls(data.control_state || data.all_controls || {});
    await fetchEvents();
  };

  useEffect(() => {
    fetch("https://mygrid-ai-backend.onrender.com/grid/controls")
      .then((response) => response.json())
      .then((data) => setControls(data));

    fetchEvents();

    const eventTimer = setInterval(() => {
      fetchEvents();
    }, 2000);

    fetch("https://mygrid-ai-backend.onrender.com/grid/history")
      .then((response) => response.json())
      .then((data) => {
        const formattedHistory = data.history.map((entry) => ({
          time: new Date(entry.timestamp).toLocaleTimeString(),
          generation: entry.renewables.total_generation_kw,
          load: entry.grid.load_demand_kw,
        }));

        setHistory(formattedHistory.slice(-20));
      });

    const socket = new WebSocket("wss://mygrid-ai-backend.onrender.com/ws/grid");

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      setGridData(data);
      setEvents(data.events || []);

      if (data.control_state) {
        setControls(data.control_state);
      }

      setHistory((prevHistory) => {
        const updatedHistory = [
          ...prevHistory,
          {
            time: new Date(data.timestamp).toLocaleTimeString(),
            generation: data.renewables.total_generation_kw,
            load: data.grid.load_demand_kw,
          },
        ];

        return updatedHistory.slice(-20);
      });
    };

    return () => {
      socket.close();
      clearInterval(eventTimer);
    };
  }, [fetchEvents]);

  if (!gridData) {
    return <h1>Connecting to MyGrid AI...</h1>;
  }

  return (
    <div className="dashboard">
      <h1>MyGrid AI</h1>
      <p className="subtitle">Real-Time Smart Grid Intelligence Platform</p>

      <div className="grid">
        <div className="card">
          <h2>Renewable Generation</h2>
          <p>Solar Output</p>
          <p className="metric">{gridData.renewables.solar_kw} kW</p>
          <p>Wind Output</p>
          <p className="metric">{gridData.renewables.wind_kw} kW</p>
          <p>Total Generation</p>
          <p className="metric">{gridData.renewables.total_generation_kw} kW</p>
        </div>

        <div className="card">
          <h2>Grid Status</h2>
          <p>Load Demand</p>
          <p className="metric">{gridData.grid.load_demand_kw} kW</p>

          <p>
            Load Trend:
            {gridData.trends.load === 1
              ? " ↑"
              : gridData.trends.load === -1
              ? " ↓"
              : " →"}
          </p>

          <p>Frequency</p>
          <p className="metric">{gridData.grid.frequency_hz} Hz</p>
          <p>Voltage</p>
          <p className="metric">{gridData.grid.voltage_v} V</p>

          <p>
            Voltage Trend:
            {gridData.trends.voltage === 1
              ? " ↑"
              : gridData.trends.voltage === -1
              ? " ↓"
              : " →"}
          </p>

          <p>
            Status:{" "}
            <span
              className={gridData.grid.state === "STABLE" ? "stable" : "warning"}
            >
              {gridData.grid.state}
            </span>
          </p>
        </div>

        <div className="card">
          <h2>Grid Efficiency</h2>
          <p>Generation-to-Demand Ratio</p>

          <p
            className={
              gridData.grid.efficiency_percent >= 100
                ? "metric risk-low"
                : gridData.grid.efficiency_percent >= 80
                ? "metric risk-medium"
                : "metric risk-high"
            }
          >
            {gridData.grid.efficiency_percent}%
          </p>

          <p>
            Status:{" "}
            <span
              className={
                gridData.grid.efficiency_status === "SURPLUS"
                  ? "stable"
                  : gridData.grid.efficiency_status === "BALANCED"
                  ? "safe"
                  : "warning"
              }
            >
              {gridData.grid.efficiency_status}
            </span>
          </p>
        </div>

        <div className="card">
          <h2>Power Balance</h2>
          <p>Generation minus Load Demand</p>

          <p
            className={
              gridData.grid.power_balance_kw >= 0
                ? "metric risk-low"
                : "metric risk-high"
            }
          >
            {gridData.grid.power_balance_kw} kW
          </p>

          <p>
            Status:{" "}
            <span
              className={gridData.grid.power_balance_kw >= 0 ? "stable" : "warning"}
            >
              {gridData.grid.power_balance_status}
            </span>
          </p>
        </div>

        <div className="card">
          <h2>Battery Storage</h2>
          <p>State of Charge</p>
          <p className="metric">{gridData.battery.state_of_charge_percent}%</p>

          <p>
            Battery Trend:
            {gridData.trends.battery === 1
              ? " ↑"
              : gridData.trends.battery === -1
              ? " ↓"
              : " →"}
          </p>

          <p>
            Mode:{" "}
            <span
              className={
                gridData.battery.mode === "CHARGING" ||
                gridData.battery.mode === "PRIORITY CHARGING"
                  ? "stable"
                  : "warning"
              }
            >
              {gridData.battery.mode}
            </span>
          </p>
        </div>

        <div className="card">
          <h2>Active Alerts</h2>
          {gridData.grid.alerts.length === 0 ? (
            <p className="safe">No active alerts</p>
          ) : (
            gridData.grid.alerts.map((alert, index) => (
              <div className="alert" key={index}>
                {alert}
              </div>
            ))
          )}
        </div>

        <div className="card health-card">
          <h2>Grid Health Score</h2>

          <p
            className={
              gridData.ai_prediction.health_score >= 80
                ? "metric risk-low"
                : gridData.ai_prediction.health_score >= 60
                ? "metric risk-medium"
                : "metric risk-high"
            }
          >
            {gridData.ai_prediction.health_score}/100
          </p>

          <p>
            Status:{" "}
            <span
              className={
                gridData.ai_prediction.health_status === "EXCELLENT"
                  ? "stable"
                  : gridData.ai_prediction.health_status === "MODERATE RISK"
                  ? "safe"
                  : "warning"
              }
            >
              {gridData.ai_prediction.health_status}
            </span>
          </p>
        </div>

        <div className="card ai-card">
          <h2>AI Grid Prediction</h2>

          <p>Overload Risk</p>
          <p
            className={
              gridData.ai_prediction.overload_risk_percent >= 70
                ? "metric risk-high"
                : gridData.ai_prediction.overload_risk_percent >= 40
                ? "metric risk-medium"
                : "metric risk-low"
            }
          >
            {gridData.ai_prediction.overload_risk_percent}%
          </p>

          <p>Instability Score</p>
          <p
            className={
              gridData.ai_prediction.instability_score_percent >= 70
                ? "metric risk-high"
                : gridData.ai_prediction.instability_score_percent >= 40
                ? "metric risk-medium"
                : "metric risk-low"
            }
          >
            {gridData.ai_prediction.instability_score_percent}%
          </p>

          <p>AI Recommendation</p>
          <p className="recommendation">{gridData.ai_prediction.recommendation}</p>
        </div>

        <div className="card control-card">
          <h2>Grid Control Center</h2>

          <button
            className={`control-button ${
              controls.emergency_mode ? "control-active" : ""
            }`}
            onClick={() => toggleControl("emergency_mode")}
          >
            Emergency Mode
          </button>

          <button
            className={`control-button ${
              controls.battery_priority ? "control-active" : ""
            }`}
            onClick={() => toggleControl("battery_priority")}
          >
            Battery Priority
          </button>

          <button
            className={`control-button ${
              controls.ai_auto_stabilization ? "control-active" : ""
            }`}
            onClick={() => toggleControl("ai_auto_stabilization")}
          >
            AI Auto-Stabilization
          </button>

          <button
            className={`control-button ${
              controls.manual_load_reduction ? "control-active" : ""
            }`}
            onClick={() => toggleControl("manual_load_reduction")}
          >
            Manual Load Reduction
          </button>

          <button
            className={`control-button ${
              controls.renewable_boost ? "control-active" : ""
            }`}
            onClick={() => toggleControl("renewable_boost")}
          >
            Renewable Boost
          </button>
        </div>

        <div className="card">
          <h2>AI Forecast Engine</h2>

          <p>Forecast Window</p>
          <p className="metric">{gridData.forecast.window_seconds}s</p>

          <p>Projected Load</p>
          <p className="metric">{gridData.forecast.projected_load_kw} kW</p>

          <p>Projected Generation</p>
          <p className="metric">{gridData.forecast.projected_generation_kw} kW</p>

          <p>Projected Balance</p>
          <p
            className={
              gridData.forecast.projected_balance_kw >= 0
                ? "metric stable"
                : "metric risk-high"
            }
          >
            {gridData.forecast.projected_balance_kw} kW
          </p>

          <p>
            Blackout Risk:{" "}
            <span
              className={
                gridData.forecast.blackout_risk_level === "LOW"
                  ? "stable"
                  : gridData.forecast.blackout_risk_level === "MEDIUM"
                  ? "warning"
                  : "risk-high"
              }
            >
              {gridData.forecast.blackout_risk_level}
            </span>
          </p>

          <p>Forecast Confidence</p>
          <p
            className={
              gridData.forecast.confidence_percent >= 80
                ? "metric stable"
                : gridData.forecast.confidence_percent >= 60
                ? "metric warning"
                : "metric risk-high"
            }
          >
            {gridData.forecast.confidence_percent}%
          </p>
        </div>

        <div className="card energy-network-card">
          <h2>Real-Time Energy Network</h2>

          <div className="energy-network">
            <div className="energy-node solar-node">
              ☀️
              <p>Solar</p>
              <span>{gridData.renewables.solar_kw} kW</span>
            </div>

            <div className="energy-flow">
              <Zap className="flow-icon" />
            </div>

            <div className="energy-node grid-node">
              ⚡
              <p>Main Grid</p>
              <span>{gridData.grid.load_demand_kw} kW</span>
            </div>

            <div className="energy-flow">
              <Zap className="flow-icon" />
            </div>

            <div className="energy-node battery-node">
              🔋
              <p>Battery</p>
              <span>{gridData.battery.state_of_charge_percent}%</span>
            </div>
          </div>
        </div>

        <div className="card event-log-card">
          <h2>System Event Log</h2>

          {events.length === 0 ? (
            <p className="safe">No system events yet</p>
          ) : (
            events
              .slice()
              .reverse()
              .map((event, index) => (
                <div className="event-log-item" key={index}>
                  <span>[{event.timestamp}]</span> {event.message}
                </div>
              ))
          )}
        </div>

        <div className="card chart-card">
          <h2>Live Energy Flow</h2>

          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={history}>
              <CartesianGrid stroke="#334155" strokeDasharray="3 3" />
              <XAxis dataKey="time" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Legend />

              <Line
                type="monotone"
                dataKey="generation"
                stroke="#22c55e"
                strokeWidth={4}
                dot={false}
              />

              <Line
                type="monotone"
                dataKey="load"
                stroke="#ef4444"
                strokeWidth={4}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

export default App;