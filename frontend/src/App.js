import React, { useState, useEffect, useCallback } from 'react';

function App() {
  const [alerts, setAlerts] = useState([]);
  const [wsStatus, setWsStatus] = useState('Disconnected');
  const [inputSymbol, setInputSymbol] = useState('RELIANCE');
  const [inputPrice, setInputPrice] = useState('');
  const [simulating, setSimulating] = useState(false);

  // Fetch all alerts from API
  const fetchAlerts = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/alerts');
      if (response.ok) {
        const data = await response.json();
        setAlerts(data);
      }
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  }, []);

  useEffect(() => {
    // Initial fetch
    fetchAlerts();

    // Connect to WebSocket
    const ws = new WebSocket('ws://localhost:8000/ws/alerts');

    ws.onopen = () => {
      setWsStatus('Connected');
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'NEW_ALERT') {
          // Fetch updated alerts to get full record including database ID
          fetchAlerts();
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
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
  }, [fetchAlerts]);

  // Update alert status (TRADED / SKIPPED)
  const updateAlertStatus = async (alertId, newStatus) => {
    try {
      const response = await fetch(`http://localhost:8000/api/alerts/${alertId}/status`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (response.ok) {
        // Optimistic update of local state
        setAlerts((prev) =>
          prev.map((alert) =>
            alert.id === alertId ? { ...alert, status: newStatus } : alert
          )
        );
      } else {
        const errData = await response.json();
        console.error('Failed to update status:', errData.detail);
      }
    } catch (error) {
      console.error('Error updating alert status:', error);
    }
  };

  // Send a simulated tick
  const sendTestAlert = async (e) => {
    e.preventDefault();
    if (!inputSymbol || !inputPrice) {
      alert('Please enter a symbol and a price.');
      return;
    }

    setSimulating(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/simulate-tick?symbol=${encodeURIComponent(
          inputSymbol
        )}&price=${parseFloat(inputPrice)}`,
        {
          method: 'POST',
        }
      );

      if (response.ok) {
        const result = await response.json();
        if (result.breakout_detected) {
          console.log('Breakout detected!', result);
        } else {
          console.log('Tick accepted, no breakout detected.');
        }
        setInputPrice('');
      } else {
        console.error('Failed to simulate tick');
      }
    } catch (error) {
      console.error('Error simulating tick:', error);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1 className="dashboard-title">ORB Tactical Alert Dashboard</h1>
        <div className="status-badge">
          <span
            className={`status-indicator ${
              wsStatus === 'Connected' ? 'connected' : 'disconnected'
            }`}
          />
          <span>WebSocket {wsStatus}</span>
        </div>
      </header>

      <div className="dashboard-grid">
        {/* Left Column: Info, Warnings & Simulation */}
        <aside className="dashboard-sidebar">
          {/* In a Nutshell Section */}
          <section className="panel-card">
            <h2 className="panel-title">In a Nutshell</h2>
            <p className="nutshell-text">
              The Opening Range Breakout (ORB) engine locks the high and low price
              boundaries established during the opening 15 minutes of the market
              (9:15 AM - 9:30 AM IST).
            </p>
            <ul className="nutshell-list">
              <li>
                Bullish Breakout: Triggers if the price breaks above the range high.
              </li>
              <li>
                Bearish Breakout: Triggers if the price breaks below the range low.
              </li>
              <li>
                Risk management is calculated automatically with a strict 1:2 risk-to-reward ratio.
              </li>
            </ul>
          </section>

          {/* Legal Warnings Section */}
          <section className="panel-card">
            <h2 className="panel-title">Legal Warnings and Limitations</h2>
            <div className="warning-box">
              <div className="warning-item">
                <strong>Regulatory Compliance</strong>: This software is designed strictly
                as a private analytical and decision-support tool. It is not registered
                with the Securities and Exchange Board of India (SEBI) or any other
                regulatory authority. It does not provide public investment recommendations or
                advisory feeds. Public distribution of alerts or managing external client accounts
                using this system may violate financial regulations and result in legal action.
              </div>
              <div className="warning-item">
                <strong>Execution Risk</strong>: Recommended breakout levels are mathematical
                approximations. Live execution is subject to latency, broker API errors, and order book
                slippage. Users must review all levels before manually routing trades.
              </div>
              <div className="warning-item">
                <strong>Capital Risk</strong>: Trading equities and derivatives involves substantial risk of
                capital loss. Standard stop-losses do not guarantee protection against overnight gaps or
                extreme volatility. Users assume all trading liability.
              </div>
            </div>
          </section>

          {/* Test Alert Simulator */}
          <section className="panel-card">
            <h2 className="panel-title">Tick Simulator</h2>
            <form onSubmit={sendTestAlert}>
              <div className="form-group">
                <label className="form-label">Symbol</label>
                <input
                  type="text"
                  className="form-input"
                  value={inputSymbol}
                  onChange={(e) => setInputSymbol(e.target.value.toUpperCase())}
                  placeholder="e.g. RELIANCE"
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Price</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input"
                  value={inputPrice}
                  onChange={(e) => setInputPrice(e.target.value)}
                  placeholder="e.g. 2405.00"
                  required
                />
              </div>
              <button
                type="submit"
                className="btn-primary"
                disabled={simulating}
              >
                {simulating ? 'Sending Tick...' : 'Send Test Tick'}
              </button>
            </form>
          </section>
        </aside>

        {/* Right Column: Alerts List */}
        <main className="dashboard-content">
          <section className="panel-card" style={{ marginBottom: 0 }}>
            <h2 className="panel-title">Tactical Alerts ({alerts.length})</h2>

            {alerts.length === 0 ? (
              <div className="empty-state">
                <p>No active breakout alerts found.</p>
                <p style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>
                  Use the simulator or ingest live ticks to trigger calculations.
                </p>
              </div>
            ) : (
              <div className="alerts-list">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`alert-card ${alert.direction.toLowerCase()}`}
                  >
                    <div className="alert-header">
                      <div>
                        <span className="symbol-badge">{alert.symbol}</span>
                        <span
                          className={`direction-badge ${alert.direction.toLowerCase()}`}
                          style={{ marginLeft: '0.75rem' }}
                        >
                          {alert.direction}
                        </span>
                      </div>
                      <span className="alert-time">
                        {new Date(alert.alert_time).toLocaleTimeString()}
                      </span>
                    </div>

                    <div className="levels-grid">
                      <div className="level-item">
                        <span className="level-label">Entry</span>
                        <span className="level-value entry">
                          INR {alert.breakout_price.toFixed(2)}
                        </span>
                      </div>
                      <div className="level-item">
                        <span className="level-label">Stop Loss</span>
                        <span className="level-value sl">
                          INR {alert.stop_loss.toFixed(2)}
                        </span>
                      </div>
                      <div className="level-item">
                        <span className="level-label">Target</span>
                        <span className="level-value target">
                          INR {alert.target.toFixed(2)}
                        </span>
                      </div>
                    </div>

                    <div className="range-info">
                      <span>Range Low: INR {alert.range_low.toFixed(2)}</span>
                      <span>Range High: INR {alert.range_high.toFixed(2)}</span>
                    </div>

                    <div className="alert-footer">
                      <div>
                        <span className="level-label" style={{ display: 'block' }}>Status</span>
                        <span className={`status-text ${alert.status.toLowerCase()}`}>
                          {alert.status}
                        </span>
                      </div>

                      {alert.status === 'PENDING' && (
                        <div className="action-buttons">
                          <button
                            className="btn-action trade"
                            onClick={() => updateAlertStatus(alert.id, 'TRADED')}
                          >
                            Mark Traded
                          </button>
                          <button
                            className="btn-action skip"
                            onClick={() => updateAlertStatus(alert.id, 'SKIPPED')}
                          >
                            Mark Skipped
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;