# The server for Team TWO's QuietSpace project
# Orignally by Jada Sowells.
# Updated and edited by Makell Williams and Google Gemini.
# Slight changes to update routing and handle more communication between dashboard and noise level pages.

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import os # Somehow this import was missing
import logging # Somehow this import was missing
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import secrets

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
@app.route("/api/staff/dashboard-data") # CRUD - Reads the data.
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


@socketio.on("submit_report") # Report is created and sent to database and dashboard.
def handle_report(data):
    room_identifier = str(data.get('room', '')).strip() # Get room id.
    room_doc = _find_room(room_identifier) # Locates the target room we are look for.
    now = datetime.now(timezone.utc)

    report = {
        'room_id': room_doc["_id"] if room_doc else None,
        'room_name': room_doc["name"] if room_doc else f"Room{room_identifier}",
        'source': "report",
        'reported_at': now,
        'noise_type': data.get('noiseType'),
        'severity': data.get('severity'),
        'details': data.get('details'),
        'other_details': data.get("otherNoiseDetails"),
        'resolved': False,
        'resolved_by': None,
        'resolved_at': None,
    }

    # CRUD - The Create Part
    noise_reports().insert_one(report)
    emit('report_received', {'success':True, 'message': 'Report Submitted Successfully'})
    report['timestamp'] = now.isoformat()
    report['noise_type'] = data.get('noiseType') 
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


@socketio.on('resolve_incident') # CRUD - Update the report state to be resolved.
def handle_resolved_incident(data):
    report_id = data.get('report_id')

    if report_id: # If a report id is there, update that report to be resolved and say when it was resolved.
        noise_reports().update_one(
            {"_id": report_id},
            {"$set": {
                "resolved": True,
                "resolved_at": datetime.now(timezone.utc)
            }}
        )
        socketio.emit('incident_resolved', {"report_id": str(report_id)}) # Notify the dashboard of the resolved incident.

def purge_old_records(days_limit = 30): # CRUD - Handle deleting old reports.
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_limit) # Set a cutoff day, delete reports after they've stayed till this day.

    result = noise_reports().delete_many({"reported_at": {"#lt": cutoff_date}})
    log.info("Purged %d old noise reports.", result.deleted_count)


@app.route('/api/rooms', methods=['GET']) # CRUD READ, used to get rooms from database and put on the dashboard dynamically.
def get_all_rooms():
    try: # Try to get all rooms, sorted alphabetically.
        all_rooms = list(rooms().find({"is_active": True}).sort("name", 1))
        serialized_rooms = []
        for rm in all_rooms:
            serialized_rooms.append({
                "id": str(rm["_id"]),
                "name": rm["name"],
                "qr_token": rm["qr_token"]
            })
        return jsonify({"success": True, "rooms": serialized_rooms})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/api/rooms/create', methods=['POST']) # CRUD CREATE, handles adding new rooms from the dashboard to the database.
def create_room():
    data = request.json or {}
    room_no = str(data.get('roomNumber', '')).strip() # Get room number

    if not room_no: # Room must have a number.
        return jsonify({"success": False, "message": "Can't have an empty room number."}), 400
    
    full_name = f"Study Room {room_no}" # Give it a full name.

    if _find_room(room_no): # A simple check to see if a room of the entered number exists already.
        return jsonify({"success": False, "message": f"{full_name} already exists."}), 400
    
    token = secrets.token_hex(8)
    new_room = { # Fill the schema with the needed room info
        "name": full_name,
        "location":{"building": "Library", "floor": 3},
        "qr_token": token,
        "qr_url": f"http://localhost:5000/report?room={room_no}",
        "is_active": True,
        "capacity": 4,
        "tags": ["quiet-zone"],
        "created_at": datetime.now(timezone.utc)
    }

    rooms().insert_one(new_room) # Create the new room
    return jsonify({"success": True, "message": f"Successfully create {full_name}."})

@app.route('/api/rooms/delete', methods=['POST']) # CRUD DELETE, handles the deletion of rooms.
def delete_room():
    data = request.json or {}
    room_no = str(data.get('roomNumber', '')).strip() # Get room number

    if not room_no:
        return jsonify({"success": False, "message": "Room number is required."}), 400
    
    room_doc = _find_room(room_no) # Find that room
    if not room_doc:
        return jsonify({"success": False, "message": f"Room {room_no} not found."}), 400
    
    rooms().delete_one({"_id": room_doc["_id"]}) # Delete the room
    noise_reports().delete_many({"room_id": room_doc["_id"]}) # Clean up the noise report

    return jsonify({"success": True, "message": f"Successfully delete Room {room_no}"})


#Run server
if __name__=='__main__':
    try: # ADDED: A try except block to try and initialize the database as needed.
        init_collections()
        log.info("Database collection verified!")
    except Exception as e:
        log.warning("Couldn't initialize database collection!", e)

    socketio.run(app, debug=True,  host='0.0.0.0', port=5000)
