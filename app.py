from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime
import json
import os
from collections import datetime

#create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo'
CORS(app)

#create WebSocket server instance
socketio = SocketIO(app,cors_allowed_origins='*')

#create lists for alerts and reports to be stored on a file
alerts_history = []
reports_history = []
LOG_FILE = 'logs.json'

#Check if file already exists and load existing logs
if os.path.exists(LOG_FILE):
    try:
        with open(LOG_FILE, 'r') as f:
            data = json.load(f)
            alerts_history = data.get('alerts', [])
            reports_history = data.get('reports', [])
    except:
        alerts_history = []
        reports_history = []

#save alerts and reports to file
def save_logs():
    data = {
        'alerts': alerts_history,
        'reports':reports_history,
        'last_updated':datetime.now().isoformat()
    }
    with open(LOG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

#generate statistics for each room so staff can keep track of noisier areas
def get_room_stats():
    room_alerts = dict(int)
    room_reports = dict(int)

    #count alerts and reports for each room
    for alert in alerts_history:
        room = alert.get('room','unknown')
        room_alerts[room] += 1
    
    for report in reports_history:
        room = report.get('room','unknown')
        room_reports[room] += 1

    #create a set of alerts and reports by room without repeats
    all_rooms = set(room_alerts.keys()) | set(room_reports.keys())

    stats = []
    for room in all_rooms:
        stats.append({
            'room': room,
            'alert_count': room_alerts.get(room, 0),
            'report_count': room_reports.get(room, 0),
            'total_incidents': room_alerts.get(room, 0) + room_reports.get(room, 0)
        })

    #sort each room so that the noisiest appear first
    stats.sort(key=lambda x: x['total_incidents'], reverse=True)
    return stats

#allow staff to track most recent alerts and reports
def get_recent_activity(limit=20):
    recent = []
    for alert in alerts_history[-limit]:
        recent.append({
            'type': 'alert',
            'room': alert.get('room', 'unknown'),
            'status': alert.get('status', 'Noise Alert'),
            'timestamp': alert.get('timestamp', datetime.now().isoformat()),
            'message': f"Loud noise detected in Room {alert.get('room', 'unknown')}"
        })
    
    for report in reports_history[-limit:]:
        recent.append({
            'type': 'report',
            'room': report.get('room', 'unknown'),
            'noiseType': report.get('noiseType', 'Unknown'),
            'timestamp': report.get('timestamp', datetime.now().isoformat()),
            'message': f"Report from Room {report.get('room', 'unknown')}: {report.get('noiseType', 'Noise issue')}"
        })
    #sort by most recent first
    recent.sort(key=lambda x: x.get('timestamp', ''), reverse = True)
    return recent[:limit]

#send confirmation that server is running
@app.route('/')
def home():
    return jsonify({"message": "Audio Detector Server is running!"})

@app.route('/dashboard')
def dashboard():
    return render_template('index.html')

@app.route('/report')
def report():
    return render_template('reportingPage.html')

#complete data history for the staff dashboard
@app.route('/api/staff/dashboard-data')
def staff_dashboard_data():
    return jsonify({
        'summary': {
            'total_alerts' : len(alerts_history),
            'total_reports' : len(reports_history),
            'total_incidents' : len(alerts_history) + len(reports_history),
            'last_updated' : datetime.now().isoformat()
        },
        'room_stats' : get_room_stats(),
        'recent_activity': get_recent_activity(),
        'alerts': alerts_history[-50:],
        'reports': reports_history[-50:]
    })

#----------WebSocket Events-------------
#track when clients connect or disconnect
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {'data': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

#main event handler for noise alerts
@socketio.on('noise_aleart') #meant to match misspelling on front-end to avoid error
def handle_noise_alert(data):
    print(f"Alert received: Room {data.get('room')} is {data.get('status')}")
    alert = {
        'room': data.get('room'),
        'status': data.get('status'),
        'timestamp': datetime.now().isoformat()
    }
    #broadcast to staff client
    socketio.emit('noise_update', alert)

#event handler for manual student reports
@socketio.on('submit_report')
def handle_report(data):
    print(f"Report received from Room {data.get('room')}")
    print(f"   Noise Type: {data.get('noiseType')}")
    print(f"   Details: {data.get('details')}")
    report = {
        'room': data.get('room'),
        'noiseType': data.get('noiseType'),
        'details': data.get('details'),
        'otherDetails': data.get('otherNoiseDetails'),
        'timestamp': datetime.now().isoformat()
    } 
    emit('report_received', {'success':True, 'message': 'Report Submitted Successfully'})


#Run server
if __name__=='__main__':
    socketio.run(app, debug=True,  host='0.0.0.0', port=5000)