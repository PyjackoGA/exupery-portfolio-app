"""
market_data.py
Récupération et mise en cache des données de marché via yfinance.
Base de fallback hardcodée pour les ETFs européens.
"""

import time
import yfinance as yf

# ─────────────────────────────────────────────────────────────────────────────
# Cache simple en mémoire (TTL = 1 heure)
# ─────────────────────────────────────────────────────────────────────────────
_CACHE: dict = {}
_CACHE_TTL = 3600  # secondes


def _cache_get(key: str):
    entry = _CACHE.get(key)
    if entry and (time.time() - entry["ts"]) < _CACHE_TTL:
        return entry["data"]
    return None


def _cache_set(key: str, data):
    _CACHE[key] = {"data": data, "ts": time.time()}


# ─────────────────────────────────────────────────────────────────────────────
# Mapping secteurs yfinance → secteurs Exupéry
# ─────────────────────────────────────────────────────────────────────────────
_YF_SECTOR_MAP = {
    "technology":                  "Tech",
    "financial services":          "Finance",
    "financials":                  "Finance",
    "healthcare":                  "Santé",
    "health care":                 "Santé",
    "consumer cyclical":           "Conso. Cycl.",
    "consumer discretionary":      "Conso. Cycl.",
    "communication services":      "Com",
    "energy":                      "Énergie",
    "consumer defensive":          "Conso. Base",
    "consumer staples":            "Conso. Base",
    "industrials":                 "Industrie",
    "basic materials":             "Matériaux",
    "materials":                   "Matériaux",
    "utilities":                   "Services",
    "real estate":                 "Immo.",
    "cash":                        "Liquidités",
    "other":                       "Autres",
}


def _map_sector(raw: str) -> str:
    return _YF_SECTOR_MAP.get(raw.lower().strip(), "Autres")


# ─────────────────────────────────────────────────────────────────────────────
# Base sectorielle hardcodée — ETFs non couverts par yfinance
# ─────────────────────────────────────────────────────────────────────────────
ETF_SECTOR_DB: dict[str, dict[str, float]] = {
    # ── MSCI World ──────────────────────────────────────────────────────────
    "CW8.PA":  {"Tech": 0.2519, "Finance": 0.1617, "Santé": 0.0976,
                "Conso. Cycl.": 0.0929, "Com": 0.0838, "Énergie": 0.0391,
                "Conso. Base": 0.0576, "Industrie": 0.1210, "Matériaux": 0.0369,
                "Services": 0.0273, "Immo.": 0.0188, "Liquidités": 0.0115, "Autres": 0.0003},
    "EWLD.PA": {"Tech": 0.2519, "Finance": 0.1617, "Santé": 0.0976,
                "Conso. Cycl.": 0.0929, "Com": 0.0838, "Énergie": 0.0391,
                "Conso. Base": 0.0576, "Industrie": 0.1210, "Matériaux": 0.0369,
                "Services": 0.0273, "Immo.": 0.0188, "Liquidités": 0.0115, "Autres": 0.0003},
    "WPEA.PA": {"Tech": 0.2519, "Finance": 0.1617, "Santé": 0.0976,
                "Conso. Cycl.": 0.0929, "Com": 0.0838, "Énergie": 0.0391,
                "Conso. Base": 0.0576, "Industrie": 0.1210, "Matériaux": 0.0369,
                "Services": 0.0273, "Immo.": 0.0188, "Liquidités": 0.0115, "Autres": 0.0003},
    "URTH":    {"Tech": 0.2519, "Finance": 0.1617, "Santé": 0.0976,
                "Conso. Cycl.": 0.0929, "Com": 0.0838, "Énergie": 0.0391,
                "Conso. Base": 0.0576, "Industrie": 0.1210, "Matériaux": 0.0369,
                "Services": 0.0273, "Immo.": 0.0188, "Liquidités": 0.0115, "Autres": 0.0003},
    "ACWI":    {"Tech": 0.2400, "Finance": 0.1580, "Santé": 0.0950,
                "Conso. Cycl.": 0.0900, "Com": 0.0800, "Énergie": 0.0420,
                "Conso. Base": 0.0580, "Industrie": 0.1180, "Matériaux": 0.0390,
                "Services": 0.0280, "Immo.": 0.0200, "Liquidités": 0.0120, "Autres": 0.0200},
    "VT":      {"Tech": 0.2400, "Finance": 0.1580, "Santé": 0.0950,
                "Conso. Cycl.": 0.0900, "Com": 0.0800, "Énergie": 0.0420,
                "Conso. Base": 0.0580, "Industrie": 0.1180, "Matériaux": 0.0390,
                "Services": 0.0280, "Immo.": 0.0200, "Liquidités": 0.0120, "Autres": 0.0200},
    "IWRD.L":  {"Tech": 0.2519, "Finance": 0.1617, "Santé": 0.0976,
                "Conso. Cycl.": 0.0929, "Com": 0.0838, "Énergie": 0.0391,
                "Conso. Base": 0.0576, "Industrie": 0.1210, "Matériaux": 0.0369,
                "Services": 0.0273, "Immo.": 0.0188, "Liquidités": 0.0115, "Autres": 0.0003},
    # ── S&P 500 ─────────────────────────────────────────────────────────────
    "SPY":     {"Tech": 0.3200, "Finance": 0.1320, "Santé": 0.1270,
                "Conso. Cycl.": 0.1050, "Com": 0.0890, "Énergie": 0.0380,
                "Conso. Base": 0.0590, "Industrie": 0.0840, "Matériaux": 0.0240,
                "Services": 0.0250, "Immo.": 0.0230, "Liquidités": 0.0100, "Autres": 0.0040},
    "IVV":     {"Tech": 0.3200, "Finance": 0.1320, "Santé": 0.1270,
                "Conso. Cycl.": 0.1050, "Com": 0.0890, "Énergie": 0.0380,
                "Conso. Base": 0.0590, "Industrie": 0.0840, "Matériaux": 0.0240,
                "Services": 0.0250, "Immo.": 0.0230, "Liquidités": 0.0100, "Autres": 0.0040},
    "VOO":     {"Tech": 0.3200, "Finance": 0.1320, "Santé": 0.1270,
                "Conso. Cycl.": 0.1050, "Com": 0.0890, "Énergie": 0.0380,
                "Conso. Base": 0.0590, "Industrie": 0.0840, "Matériaux": 0.0240,
                "Services": 0.0250, "Immo.": 0.0230, "Liquidités": 0.0100, "Autres": 0.0040},
    "VTI":     {"Tech": 0.3000, "Finance": 0.1300, "Santé": 0.1280,
                "Conso. Cycl.": 0.1000, "Com": 0.0850, "Énergie": 0.0380,
                "Conso. Base": 0.0600, "Industrie": 0.0900, "Matériaux": 0.0250,
                "Services": 0.0260, "Immo.": 0.0300, "Liquidités": 0.0080, "Autres": 0.0000},
    # ── Europe ──────────────────────────────────────────────────────────────
    "VGK":     {"Tech": 0.0890, "Finance": 0.1960, "Santé": 0.1430,
                "Conso. Cycl.": 0.1120, "Com": 0.0450, "Énergie": 0.0750,
                "Conso. Base": 0.1280, "Industrie": 0.1560, "Matériaux": 0.0740,
                "Services": 0.0420, "Immo.": 0.0180, "Liquidités": 0.0120, "Autres": 0.0100},
    "IEUR":    {"Tech": 0.0890, "Finance": 0.1960, "Santé": 0.1430,
                "Conso. Cycl.": 0.1120, "Com": 0.0450, "Énergie": 0.0750,
                "Conso. Base": 0.1280, "Industrie": 0.1560, "Matériaux": 0.0740,
                "Services": 0.0420, "Immo.": 0.0180, "Liquidités": 0.0120, "Autres": 0.0100},
    "EZU":     {"Tech": 0.0790, "Finance": 0.2100, "Santé": 0.1390,
                "Conso. Cycl.": 0.1050, "Com": 0.0470, "Énergie": 0.0640,
                "Conso. Base": 0.1350, "Industrie": 0.1680, "Matériaux": 0.0790,
                "Services": 0.0440, "Immo.": 0.0160, "Liquidités": 0.0140, "Autres": 0.0000},
    "ESE.PA":  {"Tech": 0.0890, "Finance": 0.1960, "Santé": 0.1430,
                "Conso. Cycl.": 0.1120, "Com": 0.0450, "Énergie": 0.0750,
                "Conso. Base": 0.1280, "Industrie": 0.1560, "Matériaux": 0.0740,
                "Services": 0.0420, "Immo.": 0.0180, "Liquidités": 0.0120, "Autres": 0.0100},
    "LYXEL.PA":{"Tech": 0.0890, "Finance": 0.1960, "Santé": 0.1430,
                "Conso. Cycl.": 0.1120, "Com": 0.0450, "Énergie": 0.0750,
                "Conso. Base": 0.1280, "Industrie": 0.1560, "Matériaux": 0.0740,
                "Services": 0.0420, "Immo.": 0.0180, "Liquidités": 0.0120, "Autres": 0.0100},
    # ── Émergents ───────────────────────────────────────────────────────────
    "EEM":     {"Tech": 0.2350, "Finance": 0.2200, "Santé": 0.0380,
                "Conso. Cycl.": 0.1400, "Com": 0.1050, "Énergie": 0.0520,
                "Conso. Base": 0.0560, "Industrie": 0.0650, "Matériaux": 0.0720,
                "Services": 0.0090, "Immo.": 0.0180, "Liquidités": 0.0120, "Autres": 0.0180},
    "VWO":     {"Tech": 0.2350, "Finance": 0.2200, "Santé": 0.0380,
                "Conso. Cycl.": 0.1400, "Com": 0.1050, "Énergie": 0.0520,
                "Conso. Base": 0.0560, "Industrie": 0.0650, "Matériaux": 0.0720,
                "Services": 0.0090, "Immo.": 0.0180, "Liquidités": 0.0120, "Autres": 0.0180},
    "PAEEM.PA":{"Tech": 0.2350, "Finance": 0.2200, "Santé": 0.0380,
                "Conso. Cycl.": 0.1400, "Com": 0.1050, "Énergie": 0.0520,
                "Conso. Base": 0.0560, "Industrie": 0.0650, "Matériaux": 0.0720,
                "Services": 0.0090, "Immo.": 0.0180, "Liquidités": 0.0120, "Autres": 0.0180},
    # ── Sectoriels US ───────────────────────────────────────────────────────
    "XLK":     {"Tech": 1.0},
    "XLF":     {"Finance": 1.0},
    "XLV":     {"Santé": 1.0},
    "XLE":     {"Énergie": 1.0},
    "XLI":     {"Industrie": 1.0},
    "XLY":     {"Conso. Cycl.": 1.0},
    "XLP":     {"Conso. Base": 1.0},
    "XLB":     {"Matériaux": 1.0},
    "XLU":     {"Services": 1.0},
    "XLRE":    {"Immo.": 1.0},
    "XLC":     {"Com": 1.0},
    "QQQ":     {"Tech": 0.5800, "Com": 0.1700, "Conso. Cycl.": 0.1200,
                "Santé": 0.0620, "Industrie": 0.0280, "Autres": 0.0400},
}

# ─────────────────────────────────────────────────────────────────────────────
# Base géographique hardcodée
# ─────────────────────────────────────────────────────────────────────────────
ETF_GEO_DB: dict[str, dict[str, float]] = {
    "CW8.PA":   {"Amérique du Nord": 0.70, "Europe": 0.15, "Japon": 0.06, "Autres": 0.09},
    "EWLD.PA":  {"Amérique du Nord": 0.70, "Europe": 0.15, "Japon": 0.06, "Autres": 0.09},
    "WPEA.PA":  {"Amérique du Nord": 0.70, "Europe": 0.15, "Japon": 0.06, "Autres": 0.09},
    "URTH":     {"Amérique du Nord": 0.70, "Europe": 0.15, "Japon": 0.06, "Autres": 0.09},
    "ACWI":     {"Amérique du Nord": 0.63, "Europe": 0.13, "Japon": 0.05, "Émergents": 0.12, "Autres": 0.07},
    "VT":       {"Amérique du Nord": 0.63, "Europe": 0.13, "Japon": 0.05, "Émergents": 0.12, "Autres": 0.07},
    "IWRD.L":   {"Amérique du Nord": 0.70, "Europe": 0.15, "Japon": 0.06, "Autres": 0.09},
    "SPY":      {"Amérique du Nord": 1.0},
    "IVV":      {"Amérique du Nord": 1.0},
    "VOO":      {"Amérique du Nord": 1.0},
    "VTI":      {"Amérique du Nord": 1.0},
    "QQQ":      {"Amérique du Nord": 1.0},
    "VGK":      {"Europe": 1.0},
    "IEUR":     {"Europe": 1.0},
    "EZU":      {"Europe": 1.0},
    "ESE.PA":   {"Europe": 1.0},
    "LYXEL.PA": {"Europe": 1.0},
    "EEM":      {"Émergents": 1.0},
    "VWO":      {"Émergents": 1.0},
    "PAEEM.PA": {"Émergents": 1.0},
}

# ─────────────────────────────────────────────────────────────────────────────
# Benchmarks
# ─────────────────────────────────────────────────────────────────────────────
BENCHMARK_TICKERS = {
    "MSCI World":     "URTH",
    "S&P 500":        "SPY",
    "MSCI Europe":    "VGK",
    "MSCI Émergents": "EEM",
}

BENCHMARK_LABELS = {
    "MSCI World":     "MSCI W",
    "S&P 500":        "S&P 500",
    "MSCI Europe":    "MSCI Europe",
    "MSCI Émergents": "MSCI EM",
}


# ─────────────────────────────────────────────────────────────────────────────
# Fonctions principales
# ─────────────────────────────────────────────────────────────────────────────

def get_ticker_info(ticker: str) -> dict:
    """
    Retourne les infos de base d'un ticker (nom, secteur, pays, type).
    Résultat mis en cache 1h.
    """
    key = f"info_{ticker}"
    cached = _cache_get(key)
    if cached:
        return cached

    try:
        t = yf.Ticker(ticker)
        info = t.info
        result = {
            "ticker":  ticker,
            "name":    info.get("longName") or info.get("shortName") or ticker,
            "sector":  _map_sector(info.get("sector", "Autres")),
            "country": info.get("country", "N/A"),
            "type":    "ETF" if info.get("quoteType", "").upper() == "ETF" else "Action",
            "valid":   True,
        }
    except Exception:
        result = {
            "ticker": ticker, "name": ticker,
            "sector": "Autres", "country": "N/A",
            "type": "Action", "valid": False,
        }

    _cache_set(key, result)
    return result


def get_etf_sector_weights(ticker: str) -> dict[str, float] | None:
    """
    Retourne la décomposition sectorielle d'un ETF.
    1. Cherche d'abord dans la base hardcodée.
    2. Si absent, tente yfinance funds_data.
    3. Retourne None si aucune décomposition disponible.
    """
    # Base hardcodée en priorité
    if ticker in ETF_SECTOR_DB:
        return ETF_SECTOR_DB[ticker]

    key = f"etf_sectors_{ticker}"
    cached = _cache_get(key)
    if cached is not None:
        return cached

    try:
        t = yf.Ticker(ticker)
        raw = t.funds_data.sector_weightings
        if raw:
            weights = {}
            for sector_raw, w in raw.items():
                mapped = _map_sector(sector_raw)
                weights[mapped] = weights.get(mapped, 0.0) + float(w)
            _cache_set(key, weights)
            return weights
    except Exception:
        pass

    _cache_set(key, None)
    return None


def get_price_history(ticker: str, period: str = "1y"):
    """
    Retourne l'historique de prix de clôture (pandas Series).
    """
    import pandas as pd
    key = f"hist_{ticker}_{period}"
    cached = _cache_get(key)
    if cached is not None:
        return cached

    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period)["Close"]
        if hist.empty:
            _cache_set(key, None)
            return None
        _cache_set(key, hist)
        return hist
    except Exception:
        _cache_set(key, None)
        return None


def build_portfolio_sectors(positions: list[dict]) -> dict[str, float]:
    """
    Construit la décomposition sectorielle du portefeuille en look-through.
    """
    total = sum(p["amount"] for p in positions)
    if total == 0:
        return {}

    sector_totals: dict[str, float] = {}

    for pos in positions:
        ticker = pos["ticker"]
        amount = pos["amount"]
        weight = amount / total

        info = get_ticker_info(ticker)

        if info["type"] == "ETF":
            etf_sectors = get_etf_sector_weights(ticker)
            if etf_sectors:
                for sector, sw in etf_sectors.items():
                    sector_totals[sector] = sector_totals.get(sector, 0.0) + weight * sw
            else:
                sector_totals["Autres"] = sector_totals.get("Autres", 0.0) + weight
        else:
            sector = info["sector"]
            sector_totals[sector] = sector_totals.get(sector, 0.0) + weight

    return sector_totals


def get_benchmark_sectors(benchmark_name: str) -> dict[str, float]:
    """
    Retourne la décomposition sectorielle du benchmark sélectionné.
    """
    ticker = BENCHMARK_TICKERS.get(benchmark_name, "URTH")
    sectors = get_etf_sector_weights(ticker)
    if sectors:
        return sectors
    return ETF_SECTOR_DB["URTH"]
