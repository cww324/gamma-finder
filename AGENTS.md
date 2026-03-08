# Agent Build Plan

This file describes the agent-based development strategy for Gamma Finder.
Each agent has a defined scope, clear inputs/outputs, and owned files.
Agents should not modify files outside their ownership without explicit instruction.

------------------------------------------------------------------------

## Build Order

    [Agent 1 - Contracts]
           ↓
    [Agent 2 - Data]   [Agent 3 - Calculations]   (run in parallel)
           ↓                      ↓
    [Agent 4 - UI + Wiring]

------------------------------------------------------------------------

## Agent 1 - Contracts

**Run this agent first. Everything else depends on it.**

### Goal
Define the shared data models and abstract interfaces that all other
agents build against. No business logic, no API calls, no UI. Just
types and contracts.

### Tasks
- Create `app/providers/base.py` — abstract `DataProvider` class with
  method signatures: `get_option_chain(symbol)`, `get_spot_price(symbol)`
- Create `app/models.py` — dataclasses or TypedDicts for:
  - `OptionContract` (strike, expiration, gamma, delta, vanna, charm,
    iv, open_interest, volume, bid, ask, option_type, dte)
  - `OptionChain` (symbol, spot_price, contracts: list[OptionContract])
  - `GEXResult` (strike, call_gex, put_gex, net_gex, abs_net_gex)
  - `GammaLadder` (rows: list[GEXResult], call_wall, put_wall, flip_level,
    net_regime, vanna_exposure, charm_exposure)
- Create `app/__init__.py` (empty)
- Create `app/providers/__init__.py` (empty)

### Owns
    app/__init__.py
    app/models.py
    app/providers/__init__.py
    app/providers/base.py

### Output Contract
All other agents import from `app.models` and `app.providers.base`.
Do not change these files after Agent 1 completes without coordinating
with affected agents.

------------------------------------------------------------------------

## Agent 2 - Data Layer

**Depends on: Agent 1**

Run in parallel with Agent 3 after Agent 1 completes.

### Goal
Implement the Schwab API integration and a mock provider for testing.
The rest of the app should never need to know which provider is active.

### Tasks
- Create `app/providers/schwab.py` — implement `SchwabProvider`:
  - Use `schwab-py` to authenticate and call `get_option_chain()`
  - Parse raw Schwab response into `OptionChain` / `OptionContract` models
  - Handle token file path from `.env`
- Create `app/providers/mock.py` — implement `MockProvider`:
  - Reads a saved JSON fixture from `tests/fixtures/spy_chain.json`
  - Returns an `OptionChain` object matching the same interface
  - Used for all testing and UI development without a live API connection
- Create `app/auth.py` — Schwab OAuth helper:
  - First-run browser auth flow
  - Token file save/load
  - Expose a simple `get_client()` function for use by `SchwabProvider`
- Create `tests/fixtures/spy_chain.json` — realistic sample SPY options
  chain data (can be fabricated, just needs to match `OptionChain` shape)
- Create `.env.example` with required keys:
  - `SCHWAB_API_KEY`
  - `SCHWAB_SECRET`
  - `SCHWAB_TOKEN_PATH`
  - `DATA_PROVIDER` (schwab | mock)

### Owns
    app/auth.py
    app/providers/schwab.py
    app/providers/mock.py
    tests/
    tests/fixtures/
    tests/fixtures/spy_chain.json
    .env.example

------------------------------------------------------------------------

## Agent 3 - Calculations

**Depends on: Agent 1**

Run in parallel with Agent 2 after Agent 1 completes.

### Goal
Implement all financial calculations. Takes an `OptionChain` as input,
returns a `GammaLadder`. Pure functions only — no API calls, no UI.

### Tasks
- Create `app/gamma.py`:
  - `build_gamma_ladder(chain: OptionChain, weighted: bool = False) -> list[GEXResult]`
  - Use pandas for the core calculation — groupby strike+side, pivot, derive net
  - Standard GEX (default):
      `gex = gamma * oi * 100 * spot²`
  - Delta-weighted GEX (--weighted flag):
      `gex = gamma * oi * 100 * spot² * abs(delta)`
      This down-weights far OTM contracts with negligible real hedging impact.
      Note: delta-weighted is a heuristic metric, not standard GEX — label it
      clearly in output.
  - Sign: calls stored as positive magnitude, puts stored as positive magnitude,
    net_gex = call_gex - put_gex. Do not use a separate signed_gex column.
  - Walls:
      `call_wall = ladder.loc[ladder["net_gex"].idxmax(), "strike"]`
      `put_wall  = ladder.loc[ladder["net_gex"].idxmin(), "strike"]`
  - Null handling: treat None or 0 gamma/delta/oi as 0 — do not let NaN
    propagate through calculations. Filter or fillna before computing.
- Create `app/vanna.py`:
  - `calculate_vanna_exposure(chain: OptionChain) -> float`
  - VannaExposure = Vanna × OI × 100 × spot × IV (summed across chain)
- Create `app/charm.py`:
  - `calculate_charm_exposure(chain: OptionChain) -> float`
  - CharmExposure = Charm × OI × 100 (summed across chain)
- Create `app/flip.py`:
  - `find_gamma_flip(chain: OptionChain, spot: float) -> float | None`
  - Sweep price grid from spot * 0.97 → spot * 1.03 in 0.5 increments
  - Recalculate net GEX at each grid price
  - Return interpolated zero-crossing price
- Create `app/calculations.py`:
  - Orchestrator: takes `OptionChain` + config, returns fully populated `GammaLadder`
  - Calls gamma, vanna, charm, flip modules
  - Derives call_wall, put_wall, net_regime from ladder
  - Produces three ladders every run:
      - `full`   — all expirations
      - `0dte`   — DTE = 0 only
      - `nearterm` — DTE 0-2 only
  - Accepts `weighted: bool` flag and passes it through to `build_gamma_ladder`

### Owns
    app/gamma.py
    app/vanna.py
    app/charm.py
    app/flip.py
    app/calculations.py

------------------------------------------------------------------------

## Agent 4 - UI + Wiring

**Depends on: Agent 1, Agent 2, Agent 3**

Run this agent last after all others complete.

### Goal
Build the Textual terminal dashboard and wire everything together in
`main.py`. Uses `MockProvider` during development so no live Schwab
connection is needed.

### Tasks
- Create `app/terminal_ui.py` — Textual app:
  - Layout: header bar, key metrics panel, gamma ladder table, footer
  - Key metrics panel shows: spot, regime, flip level, call wall, put wall,
    vanna exposure, charm exposure
  - Gamma ladder table: strike, call GEX, put GEX, net GEX, abs net GEX
    with color coding (green positive, red negative), spot marker (►),
    wall markers. Tabs or toggle to switch between full / 0DTE / near-term
    ladder views.
  - Keyboard shortcuts:
    - `s` → symbol input prompt
    - `r` → force refresh
    - `0` → toggle 0DTE filter
    - `e` → export current ladder to CSV
    - `q` → quit
  - Auto-refresh via Textual timer (interval set by --refresh flag)
- Create `main.py` — CLI entry point:
  - Parse CLI args: --symbol, --0dte, --max-dte, --refresh, --export,
    --weighted, --compact, --debug
  - Load `.env`
  - Instantiate the correct `DataProvider` based on `DATA_PROVIDER` env var
  - Pass provider + config into the Textual app and run it
- Create `requirements.txt`

### Owns
    app/terminal_ui.py
    main.py
    requirements.txt

------------------------------------------------------------------------

## Notes for All Agents

- Import data models exclusively from `app.models`
- Import the provider interface from `app.providers.base`
- Do not hardcode the symbol SPY anywhere — always treat symbol as a
  parameter
- Do not modify files owned by another agent
- Write clean, minimal code — no premature abstractions
