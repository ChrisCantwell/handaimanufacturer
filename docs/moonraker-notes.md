# Moonraker Integration Notes

Moonraker is the first planned printer-control adapter for HandAIManufacturer.

## Adapter responsibilities

- Query server/printer info.
- Query print status.
- List G-code files.
- Upload G-code.
- Start/pause/resume/cancel when explicitly requested.
- Capture and log API errors.

## Configuration

```yaml
printer:
  type: moonraker
  name: Ender-3 V3
  url: http://192.168.1.188:7125
```

The example IP is from the original development machine and must not be hardcoded in application source.

## Useful endpoint categories

- Server info
- Printer info
- Object/status query
- File list
- File upload
- Print control
- History, where available

## Safety defaults

- Uploading G-code is allowed after slicing.
- Starting a print requires a separate operator confirmation.
- The adapter should support a dry-run/test mode.
- Failed or ambiguous Moonraker responses should stop the workflow and be logged.

## Logging fields

Suggested metadata for Moonraker interactions:

```json
{
  "printer_name": "Ender-3 V3",
  "printer_url_redacted": "http://192.168.1.188:7125",
  "action": "upload_gcode",
  "request_time": "...",
  "response_time": "...",
  "http_status": 200,
  "moonraker_result": "success",
  "filename": "part.gcode"
}
```

## Future multi-printer support

Printer configuration should be list-based eventually, even if v0.1 supports only one printer.

```yaml
printers:
  - id: ender3v3
    type: moonraker
    name: Ender-3 V3
    url: http://192.168.1.188:7125
```