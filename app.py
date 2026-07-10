# The server for Team TWO's QuietSpace project
# Orignally by Jada Sowells.
# Updated and edited by Makell Williams and Google Gemini.
# Slight changes to update routing and handle more communication between dashboard and noise level pages.

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

load_dotenv()

from db.collections import init_collections, rooms, noise_reports

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set.")

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins=ALLOWED_ORIGINS)


def _find_room(room_identifier: str):
    """Looks up a room by exact name or room number. Uses $eq to prevent injection."""
    doc = rooms().find_one({"name": {"$eq": room_identifier}})
    if doc:
        return doc
    return rooms().find_one({"name": {"$eq": f"Study Room {room_identifier}"}})


# Page routes
@app.route("/")
def home():
    return render_template('index.html') # Changed root to go to the room noise level page.

@app.route("/dashboard")
def dashboard():
    return render_template('dashboard.html')

@app.route("/report")
def report():
    return render_template("reportingPage.html")

# REST endpoints
@app.route("/api/staff/dashboard-data")
def staff_dashboard_data():
    # Returns recent alerts and reports from MongoDB for the staff dashboard."""
    recent = list(
        noise_reports()
        .find({}, {"_id": 0, "room_name": 1, "source": 1, "status": 1,
                   "noise_type": 1, "severity": 1, "reported_at": 1})
        .sort("reported_at", -1)
        .limit(50)
    )
    for r in recent:
        r["reported_at"] = r["reported_at"].isoformat()
 
    total_alerts  = noise_reports().count_documents({"source": "alert"})
    total_reports = noise_reports().count_documents({"source": "report"})
 
    return jsonify({
        "summary": {
            "total_alerts":    total_alerts,
            "total_reports":   total_reports,
            "total_incidents": total_alerts + total_reports,
            "last_updated":    datetime.now(timezone.utc).isoformat(),
        },
        "recent_activity": recent,
    })


# Socket.IO events
@socketio.on("connect")
def handle_connect():
    log.info("Client connected: %s", request.sid)
    emit("connection_response", {"data": "Connected to server"})


@socketio.on("disconnect")
def handle_disconnect():
    log.info("Client disconnected: %s", request.sid)


#main event handler for noise alerts
@socketio.on('noise_alert')
def handle_noise_alert(data):
    if not isinstance(data, dict):
        return

    room_identifier = str(data.get("room", "")).strip()
    status          = str(data.get("status", "")).strip()

    if not room_identifier or not status:
        log.warning("noise_alert: missing room or status from %s", request.sid)
        return

    log.info("Alert: Room %s is %s", room_identifier, status)
    now      = datetime.now(timezone.utc)
    room_doc = _find_room(room_identifier)

    noise_reports().insert_one({
        "room_id":       room_doc["_id"] if room_doc else None,
        "room_name":     room_doc["name"] if room_doc else f"Room {room_identifier}",
        "source":        "alert",
        "status":        status,
        "reported_at":   now,
        "noise_type":    None,
        "severity":      None,
        "details":       None,
        "other_details": None,
        "resolved":      False,
        "resolved_by":   None,
        "resolved_at":   None,
    })

    socketio.emit("noise_update", {
        "room":      room_identifier,
        "status":    status,
        "timestamp": now.isoformat(),
    })


@socketio.on("submit_report")
def handle_report(data):
    print(f"Report received from Room {data.get('room')}")
    print(f"Noise Type: {data.get('noiseType')}")
    print(f"Details: {data.get('details')}")
    report = {
        'room': data.get('room'),
        'noiseType': data.get('noiseType'),
        'details': data.get('details'),
        'otherDetails': data.get('otherNoiseDetails'),
        'timestamp': datetime.now().isoformat()
    } 
    emit('report_received', {'success':True, 'message': 'Report Submitted Successfully'})

    socketio.emit('dashboard_new_report', report) # Small addition for the future dashboard to receive the report from the report page.

@socketio.on('change_settings') # Event handler for staff changing settings for a specific room.
def handle_change_settings(data):
    print(f"[CONFIG CHANGE] An Admin updated thresholds for Room {data.get('room')}: Green Max={data.get('greenMax')}, Yellow Max={data.get('yellowMax')}, Cooldown Timer={data.get('countdownMins')}, Mic Sensitivity = {data.get('micSensitivity')}, Noise cancelation = {data.get('noiseCancelation')}", )
    socketio.emit('apply_new_settings', data) # Send this to the network so the correct room will receive this change in settings.


@socketio.on('room_ping') # Event handler for room pinging updates.
def handle_room_ping(data):
    # Log it locally if you want to verify, or leave it quiet to avoid terminal clutter
    print(f"Heartbeat: Room {data.get('room')} is currently {data.get('status')} (Level: {data.get('level')})")

    payload = { # Get this info down here...
        'room': data.get('room'),
        'level': data.get('level'),
        'status': data.get('status'),
        'timestamp': datetime.now().isoformat()
    }
    socketio.emit('live_room_ping', payload) #...then send to dashboard to update that page with the latest info.

#Run server
if __name__=='__main__':
    socketio.run(app, debug=True,  host='0.0.0.0', port=5000)
