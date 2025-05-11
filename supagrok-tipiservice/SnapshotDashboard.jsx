// PRF-SUPAGROK-V3-SNAPSHOT-DASHBOARD-JSX-HEALTH-WEBSOCKET
// UUID: 7b1e9c0a-3d5f-4e8a-9c0b-8d7f6a5b4c3d
// Path: /home/owner/supagrok-tipiservice/SnapshotDashboard.jsx
// Purpose: React component to interact with the Supagrok Snapshot service,
//          including health checks, triggering snapshots, and viewing real-time logs via WebSocket.
// PRF Relevance: P01, P02, P03, P04, P05, P06, P07, P08, P09, P10, P11, P14, P16, P19, P21, P23, P24, P28

import React, { useState, useEffect, useCallback, useRef } from 'react';

const API_BASE_URL = "http://localhost:8000"; // PRF-P06: Configurable base URL

export default function SnapshotDashboard() {
  const [healthStatus, setHealthStatus] = useState('Checking...');
  const [healthError, setHealthError] = useState('');
  const [snapshotStatus, setSnapshotStatus] = useState('Idle');
  const [snapshotError, setSnapshotError] = useState('');
  const [logMessages, setLogMessages] = useState([]);
  const ws = useRef(null);
  const logContainerRef = useRef(null);

  // PRF-P07, PRF-P10: Health Check
  const checkHealth = useCallback(async () => {
    setHealthError('');
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status} ${response.statusText}`);
      }
      const data = await response.json();
      if (data.status === "OK") {
        setHealthStatus("Healthy");
      } else {
        setHealthStatus("Unhealthy");
        setHealthError(`Backend reported: ${data.status || 'Unknown status'}`);
      }
    } catch (error) {
      setHealthStatus("Unhealthy");
      setHealthError(`Failed to connect to backend: ${error.message}`);
      console.error("Health check error:", error);
    }
  }, []);

  useEffect(() => {
    checkHealth(); // Initial check
    const intervalId = setInterval(checkHealth, 5000); // Poll every 5 seconds
    return () => clearInterval(intervalId);
  }, [checkHealth]);

  // PRF-P03, PRF-P08, PRF-P19, PRF-P21: WebSocket for logs
  useEffect(() => {
    if (healthStatus !== "Healthy") {
        // Don't attempt to connect WebSocket if backend is not healthy
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.close();
        }
        return;
    }

    if (ws.current && (ws.current.readyState === WebSocket.OPEN || ws.current.readyState === WebSocket.CONNECTING)) {
        // WebSocket already open or connecting
        return;
    }
    
    setLogMessages(prev => [...prev, `[System] Attempting WebSocket connection to ${API_BASE_URL.replace('http', 'ws')}/ws/snapshot...`]);
    ws.current = new WebSocket(`${API_BASE_URL.replace('http', 'ws')}/ws/snapshot`);

    ws.current.onopen = () => {
      setLogMessages(prev => [...prev, "[WebSocket] Connection established."]);
      setSnapshotStatus(prev => (prev === "Error" || prev === "Starting..." || prev === "In Progress...") ? prev : "Idle"); // Keep current active status
    };

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const message = data.message || JSON.stringify(data); // Ensure message is a string
        setLogMessages(prev => [...prev, message]);
        
        // Update snapshot status based on messages
        if (message.toLowerCase().includes("snapshot job") && message.toLowerCase().includes("started")) {
          setSnapshotStatus("In Progress...");
        } else if (message.toLowerCase().includes("completed") || message.toLowerCase().includes("successfully")) {
          setSnapshotStatus("Done");
        } else if (message.toLowerCase().includes("failed") || message.toLowerCase().includes("error")) {
          setSnapshotStatus("Error");
          setSnapshotError(message); // Show the error message from WebSocket
        }
      } catch (e) {
        setLogMessages(prev => [...prev, `[WebSocket] Error parsing message: ${event.data}`]);
        console.error("WebSocket message parse error:", e);
      }
    };

    ws.current.onerror = (error) => {
      setLogMessages(prev => [...prev, `[WebSocket] Connection error. Is the backend running at ${API_BASE_URL}?`]);
      console.error("WebSocket error:", error);
      setSnapshotStatus("Error"); // Set to error if WS connection fails
      setSnapshotError("WebSocket connection failed.");
    };

    ws.current.onclose = (event) => {
      setLogMessages(prev => [...prev, `[WebSocket] Connection closed. Code: ${event.code}, Reason: ${event.reason || 'N/A'}`]);
      // If the connection closes unexpectedly while a snapshot is in progress, reflect that.
      if (snapshotStatus === "In Progress..." || snapshotStatus === "Starting...") {
        setSnapshotStatus("Error");
        setSnapshotError("WebSocket connection lost during snapshot.");
      }
    };

    return () => {
      if (ws.current) {
        setLogMessages(prev => [...prev, "[WebSocket] Closing connection."]);
        ws.current.close();
        ws.current = null;
      }
    };
  }, [healthStatus, snapshotStatus]); // Re-run if healthStatus changes, to attempt re-connection

  // Scroll to bottom of log container
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logMessages]);

  // PRF-P03, PRF-P09, PRF-P10: Trigger Snapshot
  const handleTriggerSnapshot = async () => {
    setSnapshotStatus('Starting...');
    setSnapshotError('');
    setLogMessages(prev => [...prev, "[Action] Triggering snapshot..."]);
    try {
      const response = await fetch(`${API_BASE_URL}/snapshot`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          source_path: "/data/source", // This is the path *inside the container*
        }),
      });

      const responseData = await response.json();

      if (!response.ok) {
        setSnapshotStatus('Error');
        const errorMsg = responseData.detail || responseData.error || `Snapshot trigger failed: ${response.status}`;
        setSnapshotError(errorMsg);
        setLogMessages(prev => [...prev, `[Action] Error: ${errorMsg}`]);
        console.error("Snapshot trigger error:", responseData);
      } else {
        // Status will be updated by WebSocket messages.
        // Log the initial response from the POST request.
        setLogMessages(prev => [...prev, `[Action] Snapshot request sent. UUID: ${responseData.uuid || 'N/A'}`]);
      }
    } catch (error) {
      setSnapshotStatus('Error');
      setSnapshotError(`Snapshot trigger failed: ${error.message}`);
      setLogMessages(prev => [...prev, `[Action] Error: ${error.message}`]);
      console.error("Snapshot trigger fetch error:", error);
    }
  };

  // PRF-P05: Visual feedback styles
  const getStatusColor = (status) => {
    if (status === "Healthy") return 'text-green-600';
    if (status === "Unhealthy") return 'text-red-600';
    if (status === "Checking...") return 'text-yellow-600';
    return 'text-gray-600';
  };

  const getSnapshotStatusColor = (status) => {
    if (status === "Done") return 'text-green-600';
    if (status === "Error") return 'text-red-600';
    if (status === "In Progress..." || status === "Starting...") return 'text-blue-600';
    return 'text-gray-600';
  };

  return (
    <div style={{ fontFamily: 'Arial, sans-serif', padding: '20px', maxWidth: '800px', margin: 'auto', border: '1px solid #ccc', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
      <h1 style={{ textAlign: 'center', color: '#333', marginBottom: '20px' }}>Supagrok Snapshot Dashboard</h1>
      
      <div style={{ marginBottom: '20px', padding: '10px', border: '1px solid #eee', borderRadius: '4px', backgroundColor: '#f9f9f9' }}>
        <strong>Backend Health: </strong>
        <span style={{ fontWeight: 'bold' }} className={getStatusColor(healthStatus)}>{healthStatus}</span>
        {healthError && <p style={{ color: 'red', fontSize: '0.9em', marginTop: '5px' }}>Details: {healthError}</p>}
      </div>

      <button 
        style={{ 
          padding: '12px 20px', 
          backgroundColor: (snapshotStatus === 'In Progress...' || snapshotStatus === 'Starting...' || healthStatus !== 'Healthy') ? '#ccc' : '#007bff', 
          color: 'white', 
          border: 'none', 
          borderRadius: '4px', 
          cursor: (snapshotStatus === 'In Progress...' || snapshotStatus === 'Starting...' || healthStatus !== 'Healthy') ? 'not-allowed' : 'pointer',
          fontSize: '16px',
          display: 'block',
          width: '100%',
          marginBottom: '20px'
        }} 
        onClick={handleTriggerSnapshot}
        disabled={snapshotStatus === 'In Progress...' || snapshotStatus === 'Starting...' || healthStatus !== 'Healthy'}
      >
        {snapshotStatus === 'In Progress...' || snapshotStatus === 'Starting...' ? 'Snapshot In Progress...' : 'Trigger Snapshot'}
      </button>
      
      <div style={{ marginBottom: '10px' }}>
        <strong>Snapshot Status:</strong> <span style={{ fontStyle: 'italic' }} className={getSnapshotStatusColor(snapshotStatus)}>{snapshotStatus}</span>
        {snapshotError && snapshotStatus === 'Error' && <p style={{ color: 'red', fontSize: '0.9em', marginTop: '5px' }}>Error Details: {snapshotError}</p>}
      </div>

      <h3 style={{ marginTop: '20px', marginBottom: '10px', color: '#555' }}>Logs:</h3>
      <pre 
        ref={logContainerRef}
        style={{ 
          backgroundColor: '#f0f0f0', 
          border: '1px solid #ddd', 
          padding: '15px', 
          height: '300px', 
          overflowY: 'scroll', 
          whiteSpace: 'pre-wrap',
          wordWrap: 'break-word',
          borderRadius: '4px',
          fontSize: '14px',
          lineHeight: '1.6'
        }}
        // PRF-P24: Ensure text is selectable
        onCopy={(e) => e.stopPropagation()} // Allow copying from pre
      >
        {logMessages.length > 0 ? logMessages.join("\n") : "No logs yet..."}
      </pre>
    </div>
  );
}
