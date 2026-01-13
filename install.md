# Dakar 2026 Stage Visualizer - Installation Guide

A live timing visualizer for the Dakar Rally 2026, showing real-time stage positions, waypoint times, and overall rally standings.

## Prerequisites

You need Python 3.7+ and Flask installed.

---

## Step 1: Install Python

### macOS

Python 3 comes pre-installed on recent macOS versions. To check:
```bash
python3 --version
```

If not installed, use Homebrew:
```bash
brew install python3
```

Or download from [python.org](https://www.python.org/downloads/macos/)

### Windows

Download and install from [python.org](https://www.python.org/downloads/windows/)

**Important:** During installation, check "Add Python to PATH"

Or use winget:
```powershell
winget install Python.Python.3.12
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-pip
```

### Linux (Fedora/RHEL)

```bash
sudo dnf install python3 python3-pip
```

---

## Step 2: Install Dependencies

Install Flask and requests:

```bash
pip3 install flask requests
```

Or on Windows:
```powershell
pip install flask requests
```

---

## Step 3: Run the Visualizer

Navigate to the project directory and run:

```bash
python3 dakar2026_stage_viz.py
```

Or on Windows:
```powershell
python dakar2026_stage_viz.py
```

---

## Step 4: Open in Browser

Once running, open your browser and go to:

```
http://localhost:5001
```

---

## Features

- **Live timing data** from the official World Rally-Raid Championship API
- **Category tabs**: Bikes, Cars, Classic, Mission 1000
- **Class filtering**: Ultimate, T3, SSV, Stock, Trucks, etc.
- **Waypoint columns** showing stage times at each checkpoint
- **Stage position** ranked at the furthest reached waypoint
- **Auto-refresh** every 15 seconds with countdown timer
- **Sortable columns** - click any header to sort

---

## Troubleshooting

### Port already in use

If you see "Address already in use", another process is using port 5001. Either:
- Stop the other process
- Or edit `dakar2026_stage_viz.py` and change the port number at the bottom:
  ```python
  app.run(host='0.0.0.0', port=5002, debug=True)
  ```

### SSL Warning

You may see a LibreSSL warning on macOS - this is harmless and can be ignored.

### No data showing

- Check your internet connection
- The API may be temporarily unavailable
- Try selecting a different stage that has active timing data
