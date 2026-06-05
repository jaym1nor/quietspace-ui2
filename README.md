# QuietSpace 🔇

> *Encouraging Quiet, One Space at a Time*

QuietSpace is a smart noise monitoring web application designed for library and campus study spaces. It uses real-time sound detection to automatically assess room noise levels and alert both students and staff when a space becomes too loud.

---

## Features

- **Live Noise Monitoring** — Captures sound levels via microphone and classifies rooms as Quiet, Warning, or Too Loud in real time
- **Three-Tier Alert System** — Color-coded status (🟢 Green / 🟡 Yellow / 🔴 Red) with automatic staff escalation on sustained high noise
- **QR Code Reporting** — Students can scan a room-specific QR code and submit anonymous noise reports without logging in
- **Staff Dashboard** — Live view of all room statuses and incoming student reports
- **Countdown Timer** — When a room goes red, a visible countdown prompts occupants to quiet down before staff are notified

---

## Project Structure

```
quietspace-ui2/
├── mock-UI/              # UI mockups and design references
├── static/               # Static assets (CSS, images, JS)
├── templates/            # HTML templates
├── index.html            # Main entry point / QuietScore display
├── reportingPage.html    # QR-linked student noise report form
├── reportingPage2.html   # Secondary reporting page
├── logo.png              # QuietSpace logo
├── testqrcode.png        # Sample QR code for testing
└── package.json          # Project dependencies
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Routing | react-router-dom |
| Charts / Data | Recharts |
| Hardware (prototype) | Laptop microphone |
| Hardware (planned) | Raspberry Pi + USB microphone |
| Tunnel / Public Access | Cloudflare Tunnel |

---

## Getting Started

### Prerequisites
- Node.js installed
- A modern browser with microphone access

### Installation

```bash
# Clone the repository
git clone https://github.com/jaym1nor/quietspace-ui2.git
cd quietspace-ui2

# Install dependencies
npm install
```

### Running the App

Open `index.html` in your browser, or serve it locally:

```bash
npx serve .
```

Then allow microphone access when prompted to begin live noise monitoring.

---

## How It Works

1. The microphone captures ambient sound and feeds readings into a sliding window average
2. The system compares the average against thresholds to assign a room status
3. If noise stays elevated long enough, the status escalates and a countdown timer appears
4. Students can submit reports via the QR code form; staff see them live on the dashboard

---

## Future Enhancements

- [ ] Raspberry Pi + external USB microphone deployment
- [ ] Multi-room expansion
- [ ] Admin controls for custom thresholds per room
- [ ] Machine learning for noise type classification (voices, door slams, etc.)
- [ ] Analytics dashboard with peak time tracking
- [ ] Predictive alerts for high-risk times and rooms

---

## Contributors

- Kanylia Reid
- Aiden Rankin
- Jayden Minor

> **Note:** This repository is a continuation of the original QuietSpace project developed in COMP 495 (Senior Project Design I) by Kanylia Reid, Aiden Rankin, and Jayden Minor (https://github.com/KanyliaR/quietspace-ui). Development in this repo is carried out independently for COMP 496 (Senior Project Design II) and may diverge from the direction taken by the original team.
