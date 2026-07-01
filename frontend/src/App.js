import React, { useState, useEffect } from 'react';

function App() {
  const [alerts, setAlerts] = useState([]);
  const [wsStatus, setWsStatus] = useState('Disconnected');
  const [inputSymbol, setInputSymbol] = useState('RELIANCE');
  const [inputPrice, setInputPrice] = useState('');

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket(`ws://localhost:8000/ws/alerts`);

    ws.onopen = () => {
      setWsStatus('Connected');
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'NEW_ALERT') {
        // Add new alert to the list
        setAlerts(prev => [data.payload, ...prev]);
        // Play alert sound (optional)
        // new Audio('alert.mp3').play();
      }
    };

    ws.onclose = () => {
      setWsStatus('Disconnected');
      console.log('WebSocket disconnected');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setWsStatus('Error');
    };

    // Cleanup on unmount
    return () => {
      ws.close();
    };
  }, []);

  const sendTestAlert = async () => {
    if (!inputSymbol || !inputPrice) {
      alert('Please enter symbol and price');
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/simulate-tick`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          'symbol': inputSymbol,
          'price': inputPrice
        })
      });

      const result = await response.json();
      if (result.breakout_detected) {
        console.log('Test alert triggered:', result);
      } else {
        console.log('No breakout detected for test tick');
      }
    } catch (error) {
      console.error('Error sending test alert:', error);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '600px', margin: '0 auto' }}>
      <h1>ORB Tactical Alert Dashboard</h1>

      <div style={{ margin: '20px 0', padding: '10px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
        <h2>Connection Status: <span style={{ color: wsStatus === 'Connected' ? 'green' : 'red' }}>{wsStatus}</span></h2>
      </div>

      <div style={{ margin: '20px 0' }}>
        <h2>Test Alert Generator</h2>
        <div>
          <label>Symbol: </label>
          <input
            type="text"
            value={inputSymbol}
            onChange={(e) => setInputSymbol(e.target.value)}
            placeholder="e.g., RELIANCE"
            style={{ marginRight: '10px', padding: '5px' }}
          />
        </div>
        <div style={{ marginTop: '10px' }}>
          <label>Price: </label>
          <input
            type="number"
            value={inputPrice}
            onChange={(e) => setInputPrice(e.target.value)}
            placeholder="e.g., 2405"
            style={{ marginRight: '10px', padding: '5px' }}
          />
        </div>
        <button
          onClick={sendTestAlert}
          style={{ marginTop: '10px', padding: '10px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          Send Test Tick
        </button>
      </div>

      <div style={{ margin: '20px 0' }}>
        <h2>Alerts ({alerts.length})</h2>
        {alerts.length === 0 ? (
          <p>No alerts received yet</p>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {alerts.map((alert, index) => (
              <li
                key={index}
                style={{
                  padding: '15px',
                  margin: '10px 0',
                  backgroundColor: alert.direction === 'BULLISH' ? '#d4edda' : '#f8d7da',
                  border: `1px solid ${alert.direction === 'BULLISH' ? '#c3e6cb' : '#f5c6cb'}`,
                  borderRadius: '4px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                  <strong>{alert.symbol} {alert.direction} Breakout</strong>
                  <span style={{ fontSize: '0.9em', color: '#666' }}>{new Date().toLocaleTimeString()}</span>
                </div>
                <div>Entry: ₹{alert.breakout_price.toFixed(2)}</div>
                <div>Stop Loss: ₹{alert.stop_loss.toFixed(2)}</div>
                <div>Target: ₹{alert.target.toFixed(2)}</div>
                <div style={{ marginTop: '10px', fontSize: '0.9em', color: '#666' }}>
                  Range: ₹{alert.range_low.toFixed(2)} - ₹{alert.range_high.toFixed(2)}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div style={{ marginTop: '30px', paddingTop: '20px', borderTop: '1px solid #eee', fontSize: '0.9em', color: '#666' }}>
        <p>ORB Tactical Alert Dashboard - Minimal Interface</p>
        <p>Backend: http://localhost:8000</p>
        <p>WebSocket: ws://localhost:8000/ws/alerts</p>
      </div>
    </div>
  );
}

export default App;