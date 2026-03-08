# SPY Gamma Dashboard (V2)

Terminal-based options positioning dashboard for SPY using the Charles
Schwab API.

------------------------------------------------------------------------

## Overview

This project builds a Python terminal tool that calculates and
visualizes **gamma exposure (GEX)** from the SPY options chain.

The dashboard helps identify:

-   Net Gamma Regime
-   Gamma Flip Level
-   Call Wall
-   Put Wall
-   Gamma Ladder by Strike
-   0DTE Gamma Structure

This tool is intended for **market structure analysis**, not automated
trading.

------------------------------------------------------------------------

# Core Concepts

## Gamma

Gamma measures the **rate of change of delta** with respect to price.

Dealers hedging options positions must adjust their hedge when gamma
changes.

This hedging activity can influence price behavior.

------------------------------------------------------------------------

## Gamma Exposure (GEX)

Gamma exposure approximates how much hedging pressure exists at each
strike.

Simplified formula:

    GEX = Gamma × OpenInterest × ContractMultiplier × SpotPrice²

Where:

-   Gamma = option gamma
-   OpenInterest = number of open contracts
-   ContractMultiplier = 100 for US equity options
-   SpotPrice = current SPY price

For ranking only, a simpler version may be used:

    GEX_simple = Gamma × OpenInterest

------------------------------------------------------------------------

## Sign Convention

To approximate dealer positioning:

    Call GEX  = +GEX
    Put GEX   = -GEX

This creates **net gamma exposure**:

    Net GEX = Sum(Call GEX) - Sum(Put GEX)

------------------------------------------------------------------------

# Gamma Ladder

Aggregate gamma exposure **by strike**.

Example:

    Strike   Net GEX
    ---------------------
    695      +120000
    690      +341000  ← CALL WALL
    685      +210000
    680      -150000
    675      -420000  ← PUT WALL

Interpretation:

-   Large positive gamma → price pinning
-   Large negative gamma → acceleration potential

------------------------------------------------------------------------

# Call Wall

Definition:

The strike with the **largest positive gamma concentration**.

Approximation:

    CallWall = strike where NetGEX is maximum

Meaning:

Often acts as **resistance or pinning zone**.

------------------------------------------------------------------------

# Put Wall

Definition:

Strike with **largest negative gamma concentration**.

Approximation:

    PutWall = strike where NetGEX is minimum

Meaning:

Often behaves as **support or acceleration level**.

------------------------------------------------------------------------

# Gamma Flip

Gamma Flip is the price where **net gamma changes sign**.

    NetGamma(price) = 0

Above flip → Positive gamma regime\
Below flip → Negative gamma regime

------------------------------------------------------------------------

# Gamma Flip Algorithm

### Step 1 --- Price Grid

Generate prices around current spot.

Example:

    grid = range(spot*0.97 → spot*1.03)
    step = 0.5

### Step 2 --- Recalculate Net Gamma

For each price:

    GEX(price) = gamma × OI × 100 × price²

Aggregate across all strikes.

------------------------------------------------------------------------

### Step 3 --- Find Zero Crossing

Detect where net gamma switches sign.

Example:

    NetGamma(683) = +20k
    NetGamma(682) = -10k

Flip ≈ 682.x

Use **linear interpolation**.

------------------------------------------------------------------------

# 0DTE Gamma

Same-day options heavily influence hedging.

Compute a separate ladder using:

    DTE = 0

Outputs:

-   0DTE Call Wall
-   0DTE Put Wall
-   0DTE Net Gamma

------------------------------------------------------------------------

# Data Source

Primary source: **Charles Schwab API**

Required option chain fields:

-   strike
-   expiration
-   gamma
-   delta
-   implied volatility
-   open interest
-   bid
-   ask
-   volume
-   underlying price

------------------------------------------------------------------------

# Tech Stack

-   Python 3.11+
-   pandas
-   numpy
-   rich (terminal UI)
-   httpx or requests
-   python-dotenv

Optional:

-   scipy
-   matplotlib

------------------------------------------------------------------------

# CLI Usage

Run dashboard:

    python main.py

Options:

    --symbol SPY
    --0dte
    --max-dte 2
    --export csv
    --export json
    --compact
    --debug

------------------------------------------------------------------------

# Example Output

    ========================================
    SPY GAMMA DASHBOARD
    ========================================

    Underlying: SPY
    Spot Price: 684.92

    Gamma Regime: NEGATIVE
    Gamma Flip: 682.40

    Call Wall: 690
    Put Wall: 675

    Gamma Ladder
    -----------------------------
    695   +122k
    690   +341k
    685   +210k
    680   -150k
    675   -420k

------------------------------------------------------------------------

# File Structure

    spy-gamma-dashboard/
    │
    ├── main.py
    ├── requirements.txt
    ├── README.md
    ├── .env.example
    │
    ├── app/
    │   ├── auth.py
    │   ├── schwab_client.py
    │   ├── parser.py
    │   ├── gamma.py
    │   ├── flip.py
    │   ├── calculations.py
    │   └── terminal_ui.py

------------------------------------------------------------------------

# Important Limitations

This model estimates dealer positioning.

Limitations:

-   Open interest updates daily
-   Intraday positioning changes not fully captured
-   Dealer positioning inferred, not observed
-   Results should be used as **context, not prediction**

------------------------------------------------------------------------

# Future Improvements

Potential upgrades:

-   Gamma heatmap by expiration
-   Historical gamma snapshots
-   Chart overlay of gamma levels
-   Intraday auto-refresh
-   Support for SPX / QQQ

------------------------------------------------------------------------

# Disclaimer

This software is for **research and educational purposes only**.

It does not provide financial advice or trading recommendations.
