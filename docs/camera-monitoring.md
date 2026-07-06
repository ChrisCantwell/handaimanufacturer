# Camera Monitoring Plan

Camera support should make HandAIManufacturer useful from another room without turning v0.1 into a full surveillance platform.

## Staged camera roadmap

### Stage 1 — Manual RTSP

The first implementation should accept a manually configured RTSP URL.

Example:

```yaml
cameras:
  - name: Printer Cam
    type: rtsp
    url: rtsp://example.local:554/stream1
```

Features:

- Show live preview in dashboard.
- Capture snapshot into current job folder.
- Capture before-print snapshot.
- Capture first-layer snapshot.

### Stage 2 — ONVIF discovery

Add ONVIF discovery and camera metadata.

Features:

- Discover compatible cameras on LAN.
- List camera names/IPs.
- Help user select stream URL.
- Store camera config locally.

### Stage 3 — Monitoring helpers

Add optional monitoring conveniences.

Features:

- Periodic progress snapshots.
- Timelapse assembly.
- Manual “flag possible failure” notes.
- Snapshot comparison experiments.

## Security considerations

- RTSP URLs often include usernames/passwords. Never commit real camera URLs.
- Camera config belongs in local config, environment, or secret storage.
- Do not expose camera streams publicly through HandAIManufacturer.
- Avoid browser popup notifications; show status inside the dashboard.

## Job folder integration

Suggested structure:

```text
jobs/job-YYYYMMDD-HHMMSS-part-name/
  source.stl
  sliced.gcode
  slice.log
  job.json
  snapshots/
    before-print.jpg
    first-layer.jpg
    progress-001.jpg
```

## First useful UI layout

- Left: printer status and controls.
- Right: camera preview.
- Bottom: current job log/events.