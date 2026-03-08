# Gamma Finder

Terminal-based options positioning dashboard using the Charles Schwab API.

------------------------------------------------------------------------

## Overview

Python terminal tool that calculates and visualizes **dealer gamma
exposure (GEX)** from an options chain.

The dashboard helps identify:

-   Net Gamma Regime
-   Gamma Flip Level
-   Call Wall
-   Put Wall
-   Gamma Ladder by Strike
-   0DTE Gamma Structure
-   Vanna Exposure
-   Charm Exposure

Intended for **market structure analysis**, not automated trading.

------------------------------------------------------------------------

# Core Concepts

## Gamma

Gamma measures the **rate of change of delta** with respect to price.

Dealers hedging options positions must adjust their hedge when gamma
changes. This hedging activity can influence price behavior.

------------------------------------------------------------------------

## Gamma Exposure (GEX)

Gamma exposure approximates how much hedging pressure exists at each
strike.

Formula:

    GEX = Gamma × OpenInterest × ContractMultiplier × SpotPrice²

Where:

-   Gamma = option gamma from the chain
-   OpenInterest = number of open contracts
-   ContractMultiplier = 100 for US equity options
-   SpotPrice = current underlying price

Sign convention to approximate dealer positioning:

    Call GEX  = +GEX
    Put GEX   = -GEX

    Net GEX = Sum(Call GEX) - Sum(Put GEX)

------------------------------------------------------------------------

## Vanna

Vanna measures **how delta changes when implied volatility moves**.

When IV spikes or collapses, dealers must re-hedge delta even if price
has not moved. This makes vanna exposure particularly important on
high-vol events like CPI prints, Fed announcements, and earnings.

    VannaExposure = Vanna × OpenInterest × ContractMultiplier × SpotPrice × IV

------------------------------------------------------------------------

## Charm

Charm measures **how delta decays with time**.

As expiration approaches, delta shifts and dealers must re-hedge. On
0DTE options, charm-driven flows can be significant into the close.

    CharmExposure = Charm × OpenInterest × ContractMultiplier

------------------------------------------------------------------------

# Gamma Ladder

Aggregate gamma exposure by strike.

Example:

    Strike   Net GEX
    ---------------------
    695      +120000
    690      +341000  ← CALL WALL
    685      +210000
    680      -150000
    675      -420000  ← PUT WALL

Interpretation:

-   Large positive gamma → price pinning / resistance
-   Large negative gamma → support or acceleration potential

------------------------------------------------------------------------

# Call Wall

Strike with the **largest positive net gamma concentration**.

    CallWall = strike where NetGEX is maximum

Often acts as resistance or a pinning zone. Useful for avoiding strikes
priced well beyond where the market is likely to trade.

------------------------------------------------------------------------

# Put Wall

Strike with the **largest negative net gamma concentration**.

    PutWall = strike where NetGEX is minimum

Often behaves as support or an acceleration level below which moves can
extend quickly.

------------------------------------------------------------------------

# Gamma Flip

Price where **net gamma changes sign**.

    NetGamma(price) = 0

    Above flip → Positive gamma regime (dealer hedging dampens moves)
    Below flip → Negative gamma regime (dealer hedging amplifies moves)

### Algorithm

**Step 1 - Price Grid**

    grid = range(spot * 0.97 → spot * 1.03)
    step = 0.5

**Step 2 - Recalculate Net Gamma at each grid price**

    GEX(price) = gamma × OI × 100 × price²

**Step 3 - Find Zero Crossing via linear interpolation**

    NetGamma(683) = +20k
    NetGamma(682) = -10k
    Flip ≈ 682.x

------------------------------------------------------------------------

# 0DTE Gamma

Same-day options heavily influence intraday hedging flows.

Computed as a separate ladder using only contracts with DTE = 0.

Outputs:

-   0DTE Call Wall
-   0DTE Put Wall
-   0DTE Net Gamma

------------------------------------------------------------------------

# A Note on Data Freshness

**Open Interest (OI)** is published once daily by the OCC (Options
Clearing Corporation). It reflects prior end-of-day positioning and
does **not** update intraday.

This means:

-   The structural gamma levels (walls, flip) are essentially fixed at
    market open and will not shift significantly during the day.
-   Think of these as the **map for the day**.

However, intraday refresh is still useful because:

-   Spot price updates continuously, showing where you are on the map.
-   IV changes cause the gamma flip level to drift.
-   Charm and vanna exposures shift as time and vol move.

Recommended usage: **run once at market open for structural levels,
optionally refresh every N minutes to track spot and flip drift.**

------------------------------------------------------------------------

# Data Source

**Charles Schwab API** via `schwab-py`

`schwab-py` is the community Python wrapper for the Schwab API. It
handles the full OAuth 2.0 flow including the one-time browser
authorization, token storage, and automatic background token refresh.

Required option chain fields:

-   strike
-   expiration
-   gamma
-   delta
-   vanna
-   charm
-   implied volatility
-   open interest
-   bid / ask
-   volume
-   underlying price

### Auth Setup (one-time)

1.  Register an app at developer.schwab.com and get your API key.
2.  Add credentials to `.env`.
3.  On first run, a browser window opens for Schwab login and approval.
4.  Token is saved locally. All future runs refresh silently.

------------------------------------------------------------------------

# Architecture

The data layer uses a pluggable `DataProvider` abstraction. This keeps
the calculation and display logic decoupled from the data source and
makes local testing easy without live API calls.

    DataProvider (abstract)
    ├── SchwabProvider     ← default, uses schwab-py
    └── MockProvider       ← reads saved JSON, for testing

------------------------------------------------------------------------

# Tech Stack

-   Python 3.11+
-   schwab-py
-   pandas
-   numpy
-   textual (interactive terminal UI - keyboard navigation, reactive widgets, auto-refresh)
-   python-dotenv

Optional:

-   scipy (for interpolation)

------------------------------------------------------------------------

# CLI Usage

Run dashboard:

    python main.py

Options:

    --symbol SPY        underlying symbol (default: SPY)
    --0dte              show 0DTE breakdown
    --max-dte 2         filter to near-term expirations only
    --refresh 30        auto-refresh every N seconds
    --export csv        export gamma ladder to CSV
    --export json       export gamma ladder to JSON
    --compact           condensed output
    --debug             show raw API response

------------------------------------------------------------------------

# Example Output

    ========================================
    GAMMA FINDER  |  SPY
    ========================================

    Spot Price:    684.92
    Gamma Regime:  NEGATIVE
    Gamma Flip:    682.40

    Call Wall:     690
    Put Wall:      675

    Gamma Ladder
    -----------------------------
    695   +122k
    690   +341k  ← CALL WALL
    685   +210k
    ►684  (spot)
    680   -150k
    675   -420k  ← PUT WALL

    Vanna Exposure:   -18.2M  (vol-driven hedging pressure)
    Charm Exposure:   +4.1M   (time-decay hedging pressure)

------------------------------------------------------------------------

# File Structure

    gamma-finder/
    │
    ├── main.py
    ├── requirements.txt
    ├── README.md
    ├── .env.example
    │
    ├── app/
    │   ├── auth.py
    │   ├── providers/
    │   │   ├── base.py          ← DataProvider abstract class
    │   │   ├── schwab.py        ← SchwabProvider
    │   │   └── mock.py          ← MockProvider (testing)
    │   ├── parser.py
    │   ├── gamma.py
    │   ├── vanna.py
    │   ├── charm.py
    │   ├── flip.py
    │   ├── calculations.py
    │   └── terminal_ui.py

------------------------------------------------------------------------

# Important Limitations

-   OI updates daily — intraday positioning changes are not captured
-   Dealer positioning is inferred, not observed
-   Vanna and charm calculations depend on IV accuracy from the chain
-   Results should be used as **context, not prediction**

------------------------------------------------------------------------

# Future Improvements

-   Support for SPX, QQQ, TSLA, NVDA, and other optionable symbols
    (symbol-agnostic design already in place via --symbol flag)
-   Gamma heatmap by expiration
-   Historical gamma snapshots
-   Chart overlay of gamma levels
-   Vanna and charm heatmaps

------------------------------------------------------------------------

# Disclaimer

This software is for **research and educational purposes only**.

It does not provide financial advice or trading recommendations.
