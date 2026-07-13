# Backend Setup (GitHub Codespaces)

## Quick Setup (3 Commands)

### Original instructions by Jada Sowells, slightly updated by Makell Williams

Open your Codespace terminal and run these in order:

```bash
# 1. Install everything
pip install -r requirements.txt
wget -O static/socket.io.min.js https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.5/socket.io.min.js

# 2. Run the server
python app.py
```

---

## Test It

- Staff Dashboard: `http://localhost:5000/dashboard`
- Room Noise Display :'http://127.0.0.1:5000/?room=1' (Room number can be changed to any if needed. I.e, 311 can be 101, 20, 5, etc)
- Report Page: `http://localhost:5000/report?room=1` (Room number can be changed to any.)

Click "Start Microphone" → Make noise → Wait 30 seconds → Alert sends to server.

**Faster test (skip the cooldown wait):**

In browser console (F12), type:
```javascript
socket.emit('noise_alert', { room: "404", status: "Too Loud!" });
```

Check your terminal for:
```
Alert received: Room 404 is Too Loud!
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | `pip install Flask flask-cors flask-socketio eventlet python-socketio requests websocket-client` |
| `io is not defined` | `wget -O static/socket.io.min.js https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.5/socket.io.min.js` |
| Port 5000 in use | Change `port=5000` to `port=5001` in `app.py` |
