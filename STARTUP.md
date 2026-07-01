# ORB Tactical Alert Dashboard - Startup Instructions

## Backend Setup
```bash
cd orb_dashboard/backend
python -m venv venv
.\venv\Scripts\activate  # Windows
# OR
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python run_backend.py
```

Backend will be available at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws/alerts
- Health Check: http://localhost:8000/health

## Frontend Setup
```bash
cd orb_dashboard/frontend
npm install
npm start
```

Frontend will be available at: http://localhost:3000

## Features Implemented

### Backend (Phase 1 + WebSocket)
- ✅ ORB Logic Engine (opening range calculation, breakout detection)
- ✅ SQLite Database with alerts table
- ✅ REST API Endpoints:
  - GET /health - Health check
  - GET /api/alerts - Get all alerts
  - POST /api/alerts/{id}/status - Update alert status
  - POST /api/simulate-tick - Simulate tick processing (for testing)
  - GET /api/orb/{symbol} - Get ORB engine status
- ✅ WebSocket Endpoint:
  - WS /ws/alerts - Real-time alert broadcasting
- ✅ Automatic database initialization on startup
- ✅ CORS middleware enabled

### Frontend (Minimal Interface)
- ✅ React application
- ✅ WebSocket connection to backend for real-time alerts
- ✅ Simple alert display list
- ✅ Test alert generator (simulate-tick endpoint)
- ✅ Connection status indicator
- ✅ Minimal, clean interface

## Usage
1. Start the backend first: `python run_backend.py`
2. Start the frontend: `npm start` (in frontend directory)
3. Use the form in the frontend to send test ticks:
   - Enter a symbol (e.g., RELIANCE)
   - Enter a price (e.g., 2405)
   - Click "Send Test Tick"
4. When a breakout is detected, it will:
   - Be saved to the database
   - Be broadcast via WebSocket to all connected clients
   - Appear in the alerts list in the frontend
   - (Optional: play alert sound)

## Testing
Run backend tests:
```bash
cd orb_dashboard/backend
python -m pytest ../tests/test_orb_logic.py -v
python test_synthetic.py
```

## Next Steps (Phase 2+)
- Replace simulated data with real Angel One WebSocket integration
- Add authentication if needed
- Enhance frontend with charts, history, and trading controls
- Add volume filter for breakout validation
- Add audio notifications