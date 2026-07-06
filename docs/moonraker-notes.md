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
  name: Example Moonraker Printer
  url: http://PRINTER-IP-HERE:7125
```

Use the printer's actual Moonraker URL only in `config.local.yaml` or another local-only configuration file.

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
  "printer_name": "Example Moonraker Printer",
  "printer_url_redacted": "http://PRINTER-IP-HERE:7125",
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
  - id: printer-1
    type: moonraker
    name: Example Moonraker Printer
    url: http://PRINTER-IP-HERE:7125
```