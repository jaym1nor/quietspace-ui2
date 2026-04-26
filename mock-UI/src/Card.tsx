import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// Types (you can also import these from a shared file)
export type DataPoint = {
  timestamp: number;
  value: number;
};

export type RoomHistory = {
  name: string;
  data: DataPoint[];
  reported?: boolean; // 👈 new
};

export type TimeRange = "day" | "week" | "month";

// Helpers (or import from utils)
const filterDataByRange = (data: DataPoint[], range: TimeRange) => {
  const now = Date.now();

  const ranges = {
    day: 24 * 60 * 60 * 1000,
    week: 7 * 24 * 60 * 60 * 1000,
    month: 30 * 24 * 60 * 60 * 1000,
  };

  return data.filter((d) => now - d.timestamp <= ranges[range]);
};

const getStats = (data: DataPoint[]) => {
  if (data.length === 0) return { avg: 0, peak: 0 };

  const values = data.map((d) => d.value);
  const avg =
    values.reduce((sum, v) => sum + v, 0) / values.length;

  const peak = Math.max(...values);

  return { avg: Math.round(avg), peak };
};

type Props = {
  room: RoomHistory;
  range: TimeRange;
  onResolve: (roomName: string) => void;
  onReport: (roomName: string) => void;
};


const RoomCard: React.FC<Props> = ({ room, range, onResolve, onReport }) => {
  const filtered = filterDataByRange(room.data, range);
  const stats = getStats(filtered);

    const fallbackData: DataPoint[] = [
    { timestamp: 0, value: 0 },
  ];
    const safeData = filtered.length > 0 ? filtered : fallbackData;

    
  return (
    <div className={`room-card ${room.reported ? "reported" : ""}`}>
      <h3>{room.name}</h3>

      {/* <div style={{ width: "100%", height: "150px", minHeight: "200px"}}>
  <ResponsiveContainer width="100%" height="100%" >
    <LineChart data={safeData}>
      <XAxis
        dataKey="timestamp"
        tickFormatter={(t) =>
          t ? new Date(Number(t)).toLocaleTimeString() : ""
        }
      />
      <YAxis />
      <Tooltip
        labelFormatter={(t) =>
          t ? new Date(Number(t)).toLocaleString() : ""
        }
      />
      <Line
        type="monotone"
        dataKey="value"
        stroke="#8884d8"
        dot={false}
      />
    </LineChart>
  </ResponsiveContainer>
</div> */}

      <div style={{ marginTop: "10px" }}>
        <div>Avg: {stats.avg} dB</div>
        <div>Peak: {stats.peak} dB</div>
      </div>
      
      {room.reported ? (
        <button
          className="resolve-btn"
          onClick={() => onResolve(room.name)}
        >
          Resolve
        </button>
      ) : (
        <button 
          className="report-btn"
          onClick={() => onReport(room.name)}
        >
          Report
        </button>
      )}
    </div>
  );
};

export default RoomCard;