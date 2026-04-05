import { useState } from "react";

export default function App() {
  const [mode, setMode] = useState("text");

  return (
    <div style={{ display: "flex", height: "100vh", background: "#0f172a", color: "white" }}>
      
      {/* Sidebar */}
      <div style={{
        width: "200px",
        background: "#1e293b",
        padding: "20px"
      }}>
        <h3>Modes</h3>

        <button onClick={() => setMode("text")}>Text</button><br /><br />
        <button onClick={() => setMode("image")}>Image</button><br /><br />
        <button onClick={() => setMode("video")}>Video</button>
      </div>

      {/* Main Area */}
      <div style={{ flex: 1, padding: "20px" }}>
        <h2>{mode.toUpperCase()} SEARCH</h2>

        <input
          type="text"
          placeholder="Enter query..."
          style={{ padding: "10px", width: "300px" }}
        />
      </div>

    </div>
  );
}