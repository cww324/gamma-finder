# Gamma Finder - Claude Instructions

## Project Summary
Terminal-based dealer gamma exposure (GEX) dashboard. Pulls options chain
data from the Charles Schwab API and displays key gamma levels in an
interactive Textual TUI.

---

## Architecture Rules

- **Always use the `DataProvider` abstraction.** Never call `schwab-py`
  directly from outside `app/providers/schwab.py`. All data access goes
  through the `DataProvider` interface defined in `app/providers/base.py`.

- **Never hardcode the symbol.** SPY is the default but symbol is always
  a parameter. No string literals like `"SPY"` in business logic.

- **Data models live in `app/models.py`.** Import from there. Never
  redefine `OptionContract`, `OptionChain`, `GammaLadder`, or `GEXResult`
  elsewhere.

- **UI is Textual only.** Do not use `rich` directly. Textual wraps rich
  internally — use Textual widgets and layouts.

- **Calculations are pure functions.** `app/gamma.py`, `app/vanna.py`,
  `app/charm.py`, `app/flip.py` take data models as input and return
  results. No API calls, no UI code, no side effects in these files.

- **`main.py` is the only wiring point.** Provider selection, config
  loading, and CLI arg parsing happen in `main.py`. Keep other modules
  ignorant of CLI concerns.

---

## Testing Rules

- Always use `MockProvider` for tests. Never require a live Schwab
  connection to run tests.
- Mock fixture lives at `tests/fixtures/spy_chain.json`.
- Tests go in `tests/`.

---

## Code Style

- Python 3.11+
- Minimal code — no premature abstractions
- No docstrings on self-evident functions
- Type hints on all function signatures
- Prefer dataclasses for data models

---

## File Ownership (see AGENTS.md for full detail)

    app/models.py              ← data models, touch carefully
    app/providers/base.py      ← DataProvider interface, touch carefully
    app/providers/schwab.py    ← Schwab integration
    app/providers/mock.py      ← test/dev provider
    app/auth.py                ← Schwab OAuth
    app/gamma.py               ← GEX calculations
    app/vanna.py               ← Vanna exposure
    app/charm.py               ← Charm exposure
    app/flip.py                ← Gamma flip algorithm
    app/calculations.py        ← Orchestrates all calculations
    app/terminal_ui.py         ← Textual dashboard
    main.py                    ← CLI entry point and wiring

---

## Key Dependencies

- `schwab-py` — Schwab API client (handles OAuth)
- `textual` — terminal UI framework
- `pandas` — options chain data manipulation
- `numpy` — numerical calculations
- `python-dotenv` — environment config

---

## Environment Variables

    SCHWAB_API_KEY
    SCHWAB_SECRET
    SCHWAB_TOKEN_PATH
    DATA_PROVIDER       (schwab | mock)
