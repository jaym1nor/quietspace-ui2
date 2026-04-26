import React, { useEffect, useState } from "react";
import RoomCard from "./Card";
import type { RoomHistory, TimeRange, DataPoint } from "./Card";
import { getCurrentTime } from "./helpers/CurrentTime";
import "./SoundDashboard.css"

// Activity type (unchanged)
type HistoryEntry = {
  time: string;
  room: string;
  value: number;
};

// Initialize rooms
const initialRooms: RoomHistory[] = [
  { name: "Room A", data: [], reported: false },
  { name: "Room B", data: [], reported: false },
  { name: "Room C", data: [], reported: false },
];

const SoundDashboard: React.FC<{ onLogout: () => void }> = ({ onLogout }) => {
  const [rooms, setRooms] = useState<RoomHistory[]>(initialRooms);
  const [activity, setActivity] = useState<HistoryEntry[]>([]);
  const [range, setRange] = useState<TimeRange>("day");

  const reportRoom = (roomName: string) => {
    setRooms((prev) =>
      prev.map((r) =>
        r.name === roomName ? { ...r, reported: true } : r
      )
    );
  };

  const resolveRoom = (roomName: string) => {
    setRooms((prev) =>
      prev.map((r) =>
        r.name === roomName ? { ...r, reported: false } : r
      )
    );
  };

  // Simulate live updates
  useEffect(() => {
  const interval = setInterval(() => {
    setRooms((prevRooms) => {
      const now = Date.now();

      const updatedRooms = prevRooms.map((room) => {
        const newValue = Math.floor(Math.random() * 100);

        const newPoint: DataPoint = {
          timestamp: now,
          value: newValue,
        };

        return {
          ...room,
          data: [...room.data, newPoint].slice(-200),
        };
      });

      const randomRoom =
        updatedRooms[Math.floor(Math.random() * updatedRooms.length)];

      const latestValue =
        randomRoom.data[randomRoom.data.length - 1];

      setActivity((prev) => [
        {
          time: getCurrentTime(),
          room: randomRoom.name,
          value: latestValue.value,
        },
        ...prev,
      ].slice(0, 15));

      return updatedRooms;
    });
  }, 2000);

  return () => clearInterval(interval);
}, []);

  // Compute loudest room based on latest value
  const loudestRoom =
  rooms.length > 0
    ? rooms.reduce((prev, curr) => {
        const prevVal = prev.data.at(-1)?.value ?? 0;
        const currVal = curr.data.at(-1)?.value ?? 0;
        return currVal > prevVal ? curr : prev;
      })
    : null;

  const loudestValue = loudestRoom?.data.at(-1)?.value ?? 0;


  return (
    <div className="dashboard">
      {/* HEADER */}
      <header className="header">
        Sound Dashboard

        <button className="header-btn-left" onClick={onLogout}>
          👤
        </button>

        <button className="header-btn-right">⚙️</button>
      </header>

      {/* MAIN */}
      <div className="main">
        {/* LEFT: Activity */}
        <div className="activity-panel">
          <h2>Recent Activity</h2>
          <table style={{ width: "100%" }}>
            <thead>
              <tr>
                <th>Time</th>
                <th>Room</th>
                <th>dB</th>
              </tr>
            </thead>
            <tbody>
              {activity.map((entry, i) => (
                <tr key={i}>
                  <td>{entry.time}</td>
                  <td>{entry.room}</td>
                  <td>{entry.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* RIGHT */}
        <div className="right">
          {/* Loudest Room */}
          <div className="loudest">

            <h2>Loudest Room</h2>
            <div>
              <strong>{loudestRoom?.name}</strong>: {loudestValue} dB
            </div>
          </div>

          {/* Room Cards */}
          <div>
            {/* Time Range Selector */}
            <div className="range-buttons">
              <button 
                className={range === "day" ? "active" : ""} 
                onClick={() => setRange("day")}
              >
                Day
              </button>

              <button
                className={range === "week" ? "active" : ""}
                onClick={() => setRange("week")}
              >
                Week
              </button>

              <button
                className={range === "month" ? "active" : ""}
                onClick={() => setRange("month")}
              >
                Month
              </button>
            </div>

            {/* Cards */}
            <div className="cards">
              {rooms.map((room) => (
                <div key={room.name} style={{ flex: 1 }}>
                  <RoomCard room={room} range={range} onResolve={resolveRoom} onReport={reportRoom} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SoundDashboard;