# AI Provider Design

AI support should be designed as an optional provider layer, not a requirement for the core app.

## Design rule

The core app must work without AI:

```text
Upload STL -> slice -> upload -> monitor -> log
```

AI adds a separate path:

```text
Describe part -> generate CAD source -> export STL -> slice -> upload -> monitor -> log
```

## First provider target: Codex CLI

The first planned AI provider is Codex CLI.

Initial posture:

- HandAIManufacturer detects whether `codex` is installed.
- Codex manages its own authentication outside HandAIManufacturer.
- HandAIManufacturer does not store ChatGPT passwords, OAuth tokens, or API keys.
- The provider runs Codex against a controlled workspace folder.
- Outputs are reviewed before downstream slicing.

## Provider interface sketch

```python
class AIProvider:
    def available(self) -> bool:
        ...

    def generate_design(self, request: DesignRequest) -> DesignResult:
        ...

    def revise_design(self, request: RevisionRequest) -> DesignResult:
        ...
```

## Output requirements

AI providers should prefer editable CAD source over opaque mesh output.

Preferred artifacts:

- `part.scad` for OpenSCAD designs.
- `part.py` for CadQuery designs.
- `measurements.md` for human-provided dimensions.
- `prompt.md` for the actual request.
- `decision_log.md` for assumptions and rationale.
- Generated `part.stl` only after review/export.

## Human review gates

AI-generated designs should not go straight to print.

Required gates:

1. Human reviews generated source/summary.
2. STL is rendered/exported.
3. Slicer preview or metadata is reviewed.
4. G-code upload occurs.
5. Separate print-start confirmation occurs.

## Failure doctrine

If a print fails or a part does not fit, the system should capture:

- What was measured.
- What was assumed.
- What changed from the previous version.
- The resulting STL/G-code.
- The physical fit notes.
- Photos or camera snapshots where available.

The next AI request should include that history instead of starting from scratch.