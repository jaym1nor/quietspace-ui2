# The server for Team TWO's QuietSpace project
# Orignally by Jada Sowells.
# Updated and edited by Makell Williams and Google Gemini.
# Slight changes to update routing and handle more communication between dashboard and noise level pages.

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime

#create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo'
CORS(app)

#create WebSocket server instance
socketio = SocketIO(app,cors_allowed_origins='*')

#send confirmation that server is running
@app.route('/')
def home():
    return render_template('index.html') # Changed root to go to the room noise level page.

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/report')
def report():
    return render_template('reportingPage.html')

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
@socketio.on('noise_alert')
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