from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import datetime
import json
from database import init_db, execute_query, execute_update
from orb_logic import ORBEngine, Direction

# Initialize FastAPI app
app = FastAPI(title="ORB Tactical Alert Dashboard", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class AlertBase(BaseModel):
    symbol: str
    alert_time: datetime.datetime
    direction: str
    breakout_price: float
    stop_loss: float
    target: float
    range_high: float
    range_low: float
    status: str = "PENDING"

class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    status: str

class AlertResponse(AlertBase):
    id: int
    created_at: datetime.datetime

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Remove broken connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Initialize ORB engines for watched symbols (in production, this would be dynamic)
ORB_ENGINES = {}

def get_or_create_orb_engine(symbol: str) -> ORBEngine:
    """Get or create an ORB engine for a symbol."""
    if symbol not in ORB_ENGINES:
        ORB_ENGINES[symbol] = ORBEngine(symbol)
    return ORB_ENGINES[symbol]

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        result = execute_query("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# Get all alerts
@app.get("/api/alerts", response_model=List[AlertResponse])
async def get_alerts():
    """Fetch all alerts for the current session."""
    try:
        rows = execute_query("""
            SELECT id, symbol, alert_time, direction, breakout_price, stop_loss, target,
                   range_high, range_low, status, created_at
            FROM alerts
            ORDER BY alert_time DESC
        """)

        alerts = []
        for row in rows:
            alerts.append(AlertResponse(
                id=row["id"],
                symbol=row["symbol"],
                alert_time=row["alert_time"],
                direction=row["direction"],
                breakout_price=row["breakout_price"],
                stop_loss=row["stop_loss"],
                target=row["target"],
                range_high=row["range_high"],
                range_low=row["range_low"],
                status=row["status"],
                created_at=row["created_at"]
            ))
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")

# Update alert status
@app.post("/api/alerts/{alert_id}/status")
async def update_alert_status(alert_id: int, alert_update: AlertUpdate):
    """Update the execution status of an alert."""
    if alert_update.status not in ["TRADED", "SKIPPED"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid status. Must be TRADED or SKIPPED."
        )

    try:
        affected_rows = execute_update(
            "UPDATE alerts SET status = ? WHERE id = ?",
            (alert_update.status, alert_id)
        )

        if affected_rows == 0:
            raise HTTPException(status_code=404, detail="Alert not found")

        return {"message": f"Alert {alert_id} status updated to {alert_update.status}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update alert: {str(e)}")

# WebSocket endpoint for real-time alerts
@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive - we'll receive messages from client if needed
            data = await websocket.receive_text()
            # Echo back or handle client messages if needed
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Simulate processing a tick (for testing with synthetic data)
@app.post("/api/simulate-tick")
async def simulate_tick(symbol: str, price: float):
    """Simulate receiving a tick and check for breakouts (for testing)."""
    try:
        orb = get_or_create_orb_engine(symbol)
        timestamp = datetime.datetime.now()

        # Add the tick to the ORB engine
        orb.add_tick(timestamp, price)

        # Check for breakout after adding the tick
        breakout_result = None
        if orb.is_range_locked:
            breakout_result = orb.check_breakout(timestamp, price)

        response = {
            "symbol": symbol,
            "timestamp": timestamp,
            "price": price,
            "range_info": orb.get_range_info(),
            "breakout_detected": breakout_result is not None
        }

        if breakout_result:
            direction, entry_price, stop_loss, target = breakout_result
            response["breakout_info"] = {
                "direction": direction.value,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "target": target
            }

            # Save the alert to database
            alert_id = execute_update("""
                INSERT INTO alerts
                (symbol, alert_time, direction, breakout_price, stop_loss, target, range_high, range_low)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                timestamp,
                direction.value,
                entry_price,
                stop_loss,
                target,
                orb.opening_range_high,
                orb.opening_range_low
            ))

            response["alert_id"] = alert_id

            # Broadcast alert via WebSocket
            alert_message = {
                "type": "NEW_ALERT",
                "payload": {
                    "symbol": symbol,
                    "direction": direction.value,
                    "breakout_price": entry_price,
                    "stop_loss": stop_loss,
                    "target": target
                }
            }
            await manager.broadcast(alert_message)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process tick: {str(e)}")

# Get ORB engine status for a symbol
@app.get("/api/orb/{symbol}")
async def get_orb_status(symbol: str):
    """Get the current ORB engine status for a symbol."""
    try:
        orb = get_or_create_orb_engine(symbol)
        return orb.get_range_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ORB status: {str(e)}")