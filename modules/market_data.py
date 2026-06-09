"""
market_data.py
Récupération et mise en cache des données de marché via yfinance.
Base de fallback hardcodée pour les ETFs européens.
Version améliorée pour maximiser la prise en compte des ETFs.
"""

import time
import re
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
    "information technology":      "Tech",
    "software":                    "Tech",
    "semiconductors":              "Tech",

    "financial services":          "Finance",
    "financials":                  "Finance",
    "banks":                       "Finance",
    "banking":                     "Finance",
    "insurance":                   "Finance",
    "capital markets":             "Finance",

    "healthcare":                  "Santé",
    "health care":                 "Santé",
    "biotechnology":               "Santé",
    "pharmaceuticals":             "Santé",
    "medical devices":             "Santé",

    "consumer cyclical":           "Conso. Cycl.",
    "consumer discretionary":      "Conso. Cycl.",
    "retail":                      "Conso. Cycl.",
    "automobiles":                 "Conso. Cycl.",
    "travel":                      "Conso. Cycl.",

    "communication services":      "Com",
    "telecommunications":          "Com",
    "telecom":                     "Com",
    "media":                       "Com",
    "internet content & information": "Com",

    "energy":                      "Énergie",
    "oil & gas":                   "Énergie",

    "consumer defensive":          "Conso. Base",
    "consumer staples":            "Conso. Base",
    "household & personal products": "Conso. Base",

    "industrials":                 "Industrie",
    "industrial":                  "Industrie",
    "aerospace & defense":         "Industrie",
    "transportation":              "Industrie",

    "basic materials":             "Matériaux",
    "materials":                   "Matériaux",
    "chemicals":                   "Matériaux",
    "metals & mining":             "Matériaux",

    "utilities":                   "Services",

    "real estate":                 "Immo.",

    "cash":                        "Liquidités",
    "money market":                "Liquidités",
    "short government":            "Liquidités",

    "other":                       "Autres",
}


def _map_sector(raw: str) -> str:
    if not raw:
        return "Autres"
    return _YF_SECTOR_MAP.get(str(raw).lower().strip(), "Autres")


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
# Helpers robustes ETF
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_weights(weights: dict[str, float] | None) -> dict[str, float] | None:
    """
    Nettoie et renormalise un dictionnaire de poids.
    Accepte des poids en décimal (0.25) ou parfois en % (25).
    """
    if not weights:
        return None

    cleaned = {}
    for k, v in weights.items():
        try:
            val = float(v)
            if val < 0:
                continue
            cleaned[k] = cleaned.get(k, 0.0) + val
        except Exception:
            continue

    if not cleaned:
        return None

    total = sum(cleaned.values())
    if total == 0:
        return None

    cleaned = {k: v / total for k, v in cleaned.items()}
    return cleaned


def _canon_ticker(ticker: str) -> str:
    """
    Forme canonique d'un ticker pour matching robuste :
    - uppercase
    - supprime suffixes de place (.PA, .AS, .L, .DE...)
    - supprime ponctuation
    """
    t = (ticker or "").upper().strip()
    t = re.sub(r"\.[A-Z]+$", "", t)
    t = re.sub(r"[^A-Z0-9]", "", t)
    return t


def _build_db_aliases() -> dict[str, str]:
    """
    Construit une table d'alias à partir des tickers déjà présents dans ETF_SECTOR_DB.
    """
    aliases = {}
    for original in ETF_SECTOR_DB.keys():
        aliases[_canon_ticker(original)] = original
    return aliases


def _get_info_safe(ticker: str) -> dict:
    """
    Tente de récupérer t.info sans faire planter le flux.
    """
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}


ETF_DB_ALIASES = _build_db_aliases()

# Alias manuels supplémentaires pour maximiser la reconnaissance - la base de yahoo finance est assez restreinte donc on maximise l'assimilation 
ETF_DB_ALIASES.update({
    # =========================
    # MSCI WORLD / DEVELOPED WORLD
    # =========================
    "CW8": "CW8.PA",
    "EWLD": "EWLD.PA",
    "WPEA": "WPEA.PA",
    "IWDA": "URTH",
    "SWDA": "URTH",
    "EUNL": "URTH",
    "LCWD": "URTH",
    "XDWD": "URTH",
    "SWRD": "URTH",
    "XMWO": "URTH",
    "HMWD": "URTH",
    "WRD": "URTH",
    "XDWL": "URTH",
    "IWRD": "IWRD.L",
    "IWORLD": "URTH",
    "MWRD": "URTH",
    "DVRD": "URTH",
    "WDMX": "URTH",
    "DMWO": "URTH",

    # =========================
    # ACWI / ALL-WORLD / TOTAL WORLD
    # =========================
    "ACWI": "ACWI",
    "VT": "VT",
    "IUSQ": "ACWI",
    "ISAC": "ACWI",
    "SSAC": "ACWI",
    "VWCE": "VT",
    "VWRL": "VT",
    "VWRA": "VT",
    "VWRP": "VT",
    "FWRA": "VT",
    "FWRG": "VT",
    "AWRD": "ACWI",
    "ALLW": "ACWI",
    "WRLD": "ACWI",
    "GLBL": "ACWI",
    "ALLC": "ACWI",
    "MSAC": "ACWI",
    "XAWO": "ACWI",
    "XAWR": "ACWI",

    # =========================
    # S&P 500 / US LARGE CAP
    # =========================
    "SPY": "SPY",
    "IVV": "IVV",
    "VOO": "VOO",
    "SXR8": "SPY",
    "CSPX": "SPY",
    "CSSPX": "SPY",
    "VUSA": "SPY",
    "VUAA": "SPY",
    "SPYL": "SPY",
    "SP5": "SPY",
    "SPXP": "SPY",
    "IUSE": "SPY",
    "G500": "SPY",
    "SPX5": "SPY",
    "SPXX": "SPY",
    "SPPW": "SPY",
    "SPXD": "SPY",
    "SPXE": "SPY",
    "SP5L": "SPY",
    "SP5A": "SPY",
    "500U": "SPY",
    "US500": "SPY",
    "SP500": "SPY",

    # =========================
    # US TOTAL MARKET / BROAD US
    # =========================
    "VTI": "VTI",
    "ITOT": "VTI",
    "SCHB": "VTI",
    "IWV": "VTI",
    "TMWR": "VTI",
    "USTM": "VTI",
    "BUSA": "VTI",
    "USBR": "VTI",
    "XTOT": "VTI",

    # =========================
    # NASDAQ-100 / US MEGA GROWTH
    # =========================
    "QQQ": "QQQ",
    "QQQM": "QQQ",
    "CNDX": "QQQ",
    "CSNDX": "QQQ",
    "EQQQ": "QQQ",
    "SXRV": "QQQ",
    "XNAS": "QQQ",
    "NQSE": "QQQ",
    "CNX1": "QQQ",
    "NASD": "QQQ",
    "NDXU": "QQQ",
    "USTQ": "QQQ",
    "QQQS": "QQQ",
    "NDQ": "QQQ",

    # =========================
    # USA STYLE / FACTOR / BROAD PROXIES
    # =========================
    "VUG": "SPY",
    "VTV": "SPY",
    "IWF": "SPY",
    "IWD": "SPY",
    "IWB": "SPY",
    "IWO": "SPY",
    "IWN": "SPY",
    "SCHG": "SPY",
    "SCHV": "SPY",
    "DGRO": "SPY",
    "SCHD": "SPY",
    "QUAL": "SPY",
    "MTUM": "SPY",
    "USMV": "SPY",
    "SIZE": "SPY",
    "VLUE": "SPY",
    "SPLV": "SPY",
    "RPV": "SPY",
    "RPG": "SPY",
    "VBR": "SPY",
    "VBK": "SPY",
    "VB": "SPY",
    "IJR": "SPY",
    "IWM": "SPY",
    "VTWO": "SPY",
    "IJS": "SPY",
    "IJT": "SPY",
    "IUSV": "SPY",
    "IUSG": "SPY",
    "FNDX": "SPY",
    "DGRW": "SPY",
    "NOBL": "SPY",
    "SPYG": "SPY",
    "SPYV": "SPY",
    "SPTM": "SPY",
    "ONEQ": "QQQ",

    # =========================
    # EUROPE / PAN-EUROPE
    # =========================
    "VGK": "VGK",
    "IEUR": "IEUR",
    "IMEU": "VGK",
    "MEUD": "VGK",
    "MSE": "VGK",
    "EUNK": "VGK",
    "EXSA": "VGK",
    "IEUX": "VGK",
    "HEDJ": "VGK",
    "ESE": "ESE.PA",
    "LYXEL": "LYXEL.PA",
    "STXE": "VGK",
    "EURO": "VGK",
    "PEU": "VGK",
    "EURL": "VGK",
    "EROX": "VGK",
    "EUX": "VGK",

    # =========================
    # EUROZONE / EMU
    # =========================
    "EZU": "EZU",
    "FEZ": "EZU",
    "CSEMU": "EZU",
    "EMU": "EZU",
    "EUE": "EZU",
    "EZON": "EZU",
    "EMUX": "EZU",

    # =========================
    # UK / JAPAN / SWITZERLAND / DEV. EX-US
    # =========================
    "EWU": "VGK",
    "ISF": "VGK",
    "CUKX": "VGK",
    "EWJ": "URTH",
    "DXJ": "URTH",
    "JPXN": "URTH",
    "HEWJ": "URTH",
    "CSJP": "URTH",
    "EWGS": "URTH",
    "EWL": "VGK",
    "CHSPI": "VGK",
    "VEA": "URTH",
    "IDEV": "URTH",
    "SCHF": "URTH",
    "IEFA": "URTH",

    # =========================
    # EMERGING MARKETS / EM BROAD
    # =========================
    "EEM": "EEM",
    "VWO": "VWO",
    "PAEEM": "PAEEM.PA",
    "IEMA": "EEM",
    "EMIM": "EEM",
    "VFEM": "EEM",
    "EIMI": "EEM",
    "SCHE": "EEM",
    "VFEA": "EEM",
    "XMME": "EEM",
    "CSEM": "EEM",
    "XCS6": "EEM",
    "EEMS": "EEM",
    "SPEM": "EEM",
    "IEMG": "EEM",
    "XCEM": "EEM",
    "EMXC": "EEM",
    "EMKT": "EEM",
    "EMBROAD": "EEM",

    # =========================
    # CHINA / INDIA / ASIA / LATAM / COUNTRY PROXIES
    # =========================
    "FXI": "EEM",
    "MCHI": "EEM",
    "KWEB": "EEM",
    "ASHR": "EEM",
    "PGJ": "EEM",
    "CQQQ": "EEM",
    "GXC": "EEM",
    "CNXT": "EEM",
    "INDA": "EEM",
    "SMIN": "EEM",
    "EPI": "EEM",
    "PIN": "EEM",
    "INDY": "EEM",
    "AAXJ": "EEM",
    "GMF": "EEM",
    "EWY": "EEM",
    "EWT": "EEM",
    "EWH": "EEM",
    "EWS": "EEM",
    "EWM": "EEM",
    "EPHE": "EEM",
    "THD": "EEM",
    "EIDO": "EEM",
    "IDX": "EEM",
    "ILF": "EEM",
    "EWW": "EEM",
    "EWZ": "EEM",
    "ARGT": "EEM",
    "ECH": "EEM",
    "GXG": "EEM",
    "TUR": "EEM",
    "GREK": "EEM",
    "RSX": "EEM",
    "ERUS": "EEM",
    "EZA": "EEM",
    "NGE": "EEM",

    # =========================
    # SECTOR ETFs — TECHNOLOGY
    # =========================
    "XLK": "XLK",
    "VGT": "XLK",
    "IYW": "XLK",
    "RYT": "XLK",
    "FTEC": "XLK",
    "IGM": "XLK",
    "SOXX": "XLK",
    "SMH": "XLK",
    "PSI": "XLK",

    # =========================
    # SECTOR ETFs — FINANCIALS
    # =========================
    "XLF": "XLF",
    "VFH": "XLF",
    "IYF": "XLF",
    "KRE": "XLF",
    "KBE": "XLF",
    "IAI": "XLF",
    "FNCL": "XLF",

    # =========================
    # SECTOR ETFs — HEALTHCARE
    # =========================
    "XLV": "XLV",
    "VHT": "XLV",
    "IYH": "XLV",
    "IBB": "XLV",
    "XBI": "XLV",
    "FHLC": "XLV",
    "PPH": "XLV",

    # =========================
    # SECTOR ETFs — CONSUMER DISCRETIONARY
    # =========================
    "XLY": "XLY",
    "VCR": "XLY",
    "RTH": "XLY",
    "PEJ": "XLY",
    "FXD": "XLY",

    # =========================
    # SECTOR ETFs — COMMUNICATION
    # =========================
    "XLC": "XLC",
    "VOX": "XLC",
    "IYZ": "XLC",
    "FCOM": "XLC",

    # =========================
    # SECTOR ETFs — ENERGY
    # =========================
    "XLE": "XLE",
    "VDE": "XLE",
    "IYE": "XLE",
    "OIH": "XLE",
    "XOP": "XLE",
    "IXC": "XLE",
    "FENY": "XLE",

    # =========================
    # SECTOR ETFs — CONSUMER STAPLES
    # =========================
    "XLP": "XLP",
    "VDC": "XLP",
    "IYK": "XLP",
    "KXI": "XLP",
    "FSTA": "XLP",

    # =========================
    # SECTOR ETFs — INDUSTRIALS
    # =========================
    "XLI": "XLI",
    "VIS": "XLI",
    "IYJ": "XLI",
    "ITA": "XLI",
    "PAVE": "XLI",
    "RGI": "XLI",
    "FIDU": "XLI",

    # =========================
    # SECTOR ETFs — MATERIALS
    # =========================
    "XLB": "XLB",
    "VAW": "XLB",
    "IYM": "XLB",
    "PICK": "XLB",
    "MXI": "XLB",
    "FMAT": "XLB",

    # =========================
    # SECTOR ETFs — UTILITIES
    # =========================
    "XLU": "XLU",
    "VPU": "XLU",
    "IDU": "XLU",
    "JXI": "XLU",
    "FUTY": "XLU",

    # =========================
    # SECTOR ETFs — REAL ESTATE
    # =========================
    "XLRE": "XLRE",
    "VNQ": "XLRE",
    "IYR": "XLRE",
    "REET": "XLRE",
    "SCHH": "XLRE",
    "RWR": "XLRE",
    "USRT": "XLRE",

    # =========================
    # THEMATIC / CLEAN TECH / ROBOTICS / AI / CLOUD
    # proxifiés vers Tech ou broad market
    # =========================
    "BOTZ": "XLK",
    "ROBO": "XLK",
    "ARKK": "XLK",
    "ARKW": "XLK",
    "ARKQ": "XLK",
    "SKYY": "XLK",
    "WCLD": "XLK",
    "CLOU": "XLK",
    "AIQ": "XLK",
    "IRBO": "XLK",
    "ICLN": "XLI",
    "INRG": "XLI",
    "LIT": "XLB",
    "BATT": "XLB",
    "DRIV": "XLY",
    "HERO": "XLC",

    # =========================
    # REITS / PROPERTY GLOBAL
    # =========================
    "REET": "XLRE",
    "GLRE": "XLRE",
    "VNQI": "XLRE",
    "IFGL": "XLRE",

    # =========================
    # DIVIDEND / QUALITY / LOW VOL UCITS-LIKE
    # broad market proxies
    # =========================
    "FUSD": "SPY",
    "SPYD": "SPY",
    "VHYL": "VT",
    "VYMI": "VT",
    "HDV": "SPY",
    "DVY": "SPY",
    "SDY": "SPY",
    "IDV": "VT",
    "DEM": "EEM",
    "QDVG": "SPY",
    "QDVX": "SPY",
    # =========================================================
    # SANTÉ / HEALTHCARE / BIOTECH / PHARMA / MEDTECH
    # =========================================================
    "HLTW": "XLV",
    "XLV": "XLV",
    "VHT": "XLV",
    "IYH": "XLV",
    "FHLC": "XLV",
    "IXJ": "XLV",
    "IXJLN": "XLV",
    "IXJL": "XLV",
    "XDWH": "XLV",
    "WHEA": "XLV",
    "HEAL": "XLV",
    "DRDR": "XLV",
    "HTWO": "XLV",
    "IBB": "XLV",
    "XBI": "XLV",
    "PBE": "XLV",
    "PPH": "XLV",
    "IHE": "XLV",
    "IHI": "XLV",
    "GNOM": "XLV",
    "SBIO": "XLV",
    "ARKG": "XLV",
    "BTEC": "XLV",
    "CURE": "XLV",
    "RXI": "XLV",
    "PJP": "XLV",
    "IEIH": "XLV",
    "MEDI": "XLV",

    # =========================================================
    # IMMOBILIER / REIT / PROPERTY
    # =========================================================
    "XLRE": "XLRE",
    "VNQ": "XLRE",
    "IYR": "XLRE",
    "SCHH": "XLRE",
    "USRT": "XLRE",
    "RWR": "XLRE",
    "REET": "XLRE",
    "IFGL": "XLRE",
    "VNQI": "XLRE",
    "IWDP": "XLRE",
    "DPYA": "XLRE",
    "GLRE": "XLRE",
    "HPRD": "XLRE",
    "IPRP": "XLRE",
    "IWDPA": "XLRE",
    "SPDRRE": "XLRE",
    "REETLN": "XLRE",
    "REMX": "XLRE",
    "MORT": "XLRE",
    "REM": "XLRE",
    "SRET": "XLRE",
    "SRVR": "XLRE",
    "INDS": "XLRE",
    "VPN": "XLRE",

    # =========================================================
    # TECHNOLOGIE / SEMI / SOFTWARE / CLOUD / CYBER / AI
    # =========================================================
    "XLK": "XLK",
    "VGT": "XLK",
    "IYW": "XLK",
    "FTEC": "XLK",
    "IGM": "XLK",
    "RYT": "XLK",
    "SOXX": "XLK",
    "SMH": "XLK",
    "PSI": "XLK",
    "XSD": "XLK",
    "WCLD": "XLK",
    "SKYY": "XLK",
    "CLOU": "XLK",
    "HACK": "XLK",
    "CIBR": "XLK",
    "BUG": "XLK",
    "BOTZ": "XLK",
    "ROBO": "XLK",
    "IRBO": "XLK",
    "AIQ": "XLK",
    "ARKK": "XLK",
    "ARKW": "XLK",
    "ARKQ": "XLK",
    "QTUM": "XLK",
    "IUIT": "XLK",
    "QDVE": "XLK",
    "TDIV": "XLK",
    "LRNZ": "XLK",
    "KOMP": "XLK",
    "FINX": "XLK",
    "ESPO": "XLK",
    "NERD": "XLK",
    "SNSR": "XLK",
    "FIVG": "XLK",
    "WTAI": "XLK",

    # =========================================================
    # FINANCE / BANKS / INSURANCE / FINTECH
    # =========================================================
    "XLF": "XLF",
    "VFH": "XLF",
    "IYF": "XLF",
    "FNCL": "XLF",
    "KRE": "XLF",
    "KBE": "XLF",
    "IAI": "XLF",
    "EUFN": "XLF",
    "IXG": "XLF",
    "FXO": "XLF",
    "PXF": "XLF",
    "FTXO": "XLF",
    "BNKS": "XLF",
    "BANK": "XLF",
    "IYFUS": "XLF",
    "INSU": "XLF",
    "IPAY": "XLF",
    "FINX": "XLF",
    "ARKF": "XLF",
    "KIE": "XLF",

    # =========================================================
    # INDUSTRIE / AEROSPACE / INFRA / TRANSPORT
    # =========================================================
    "XLI": "XLI",
    "VIS": "XLI",
    "IYJ": "XLI",
    "FIDU": "XLI",
    "ITA": "XLI",
    "PAVE": "XLI",
    "RGI": "XLI",
    "AIRR": "XLI",
    "IFRA": "XLI",
    "GRID": "XLI",
    "JETS": "XLI",
    "XTN": "XLI",
    "IYT": "XLI",
    "BDRY": "XLI",
    "SHPP": "XLI",
    "XAR": "XLI",
    "MILN": "XLI",
    "MOTI": "XLI",

    # =========================================================
    # MATÉRIAUX / MINING / METALS / URANIUM / BATTERY MATERIALS
    # =========================================================
    "XLB": "XLB",
    "VAW": "XLB",
    "IYM": "XLB",
    "FMAT": "XLB",
    "MXI": "XLB",
    "PICK": "XLB",
    "XME": "XLB",
    "COPX": "XLB",
    "SIL": "XLB",
    "SLVP": "XLB",
    "URA": "XLB",
    "URNM": "XLB",
    "LIT": "XLB",
    "BATT": "XLB",
    "REMX": "XLB",
    "KRBN": "XLB",
    "CARB": "XLB",
    "WOOD": "XLB",
    "CUT": "XLB",

    # =========================================================
    # UTILITIES / WATER / CLEAN UTILITIES
    # =========================================================
    "XLU": "XLU",
    "VPU": "XLU",
    "IDU": "XLU",
    "FUTY": "XLU",
    "JXI": "XLU",
    "RYU": "XLU",
    "UTES": "XLU",
    "FIW": "XLU",
    "PHO": "XLU",
    "PIO": "XLU",
    "CGW": "XLU",
    "AQWA": "XLU",

    # =========================================================
    # ÉNERGIE / OIL & GAS / CLEAN ENERGY
    # =========================================================
    "XLE": "XLE",
    "VDE": "XLE",
    "IYE": "XLE",
    "FENY": "XLE",
    "IXC": "XLE",
    "OIH": "XLE",
    "XOP": "XLE",
    "PXE": "XLE",
    "PXJ": "XLE",
    "ICLN": "XLE",
    "INRG": "XLE",
    "QCLN": "XLE",
    "PBW": "XLE",
    "TAN": "XLE",
    "FAN": "XLE",
    "LITEN": "XLE",

    # =========================================================
    # COMMUNICATION / MEDIA / TELECOM / INTERNET
    # =========================================================
    "XLC": "XLC",
    "VOX": "XLC",
    "IYZ": "XLC",
    "FCOM": "XLC",
    "IXP": "XLC",
    "SOCL": "XLC",
    "FDN": "XLC",
    "PNQI": "XLC",
    "XWEB": "XLC",
    "EMQQ": "XLC",
    "HERO": "XLC",
    "ESPO": "XLC",
    "GAMR": "XLC",

    # =========================================================
    # CONSOMMATION CYCLIQUE / RETAIL / AUTO / LUXURY / TRAVEL
    # =========================================================
    "XLY": "XLY",
    "VCR": "XLY",
    "RTH": "XLY",
    "PEJ": "XLY",
    "FXD": "XLY",
    "ONLN": "XLY",
    "IBUY": "XLY",
    "CLIX": "XLY",
    "AWAY": "XLY",
    "CARZ": "XLY",
    "DRIV": "XLY",
    "BJK": "XLY",
    "BETZ": "XLY",
    "LUXE": "XLY",

    # =========================================================
    # CONSOMMATION DE BASE / STAPLES / FOOD / AGRI
    # =========================================================
    "XLP": "XLP",
    "VDC": "XLP",
    "IYK": "XLP",
    "FSTA": "XLP",
    "KXI": "XLP",
    "PBJ": "XLP",
    "MOO": "XLP",
    "VEGI": "XLP",
    "FTXG": "XLP",

    # =========================================================
    # DIVIDEND / QUALITY / LOW VOL / VALUE / GROWTH
    # broad proxies utiles
    # =========================================================
    "SCHD": "SPY",
    "DGRO": "SPY",
    "HDV": "SPY",
    "DVY": "SPY",
    "SDY": "SPY",
    "NOBL": "SPY",
    "SPYD": "SPY",
    "DGRW": "SPY",
    "FUSD": "SPY",
    "SPHQ": "SPY",
    "USMV": "SPY",
    "SPLV": "SPY",
    "QUAL": "SPY",
    "MTUM": "SPY",
    "VLUE": "SPY",
    "SIZE": "SPY",
    "IWF": "SPY",
    "IWD": "SPY",
    "VUG": "SPY",
    "VTV": "SPY",
    "VB": "SPY",
    "VBR": "SPY",
    "VBK": "SPY",
    "IJR": "SPY",
    "IWM": "SPY",
    "VTWO": "SPY",
    "IJS": "SPY",
    "IJT": "SPY",
    "IUSG": "SPY",
    "IUSV": "SPY",
    "RPG": "SPY",
    "RPV": "SPY",

    # =========================================================
    # MONDE / ALL WORLD / UCITS supplémentaires
    # =========================================================
    "IQQW": "URTH",
    "XDWDG": "URTH",
    "SUSW": "URTH",
    "SAWD": "URTH",
    "WSRI": "URTH",
    "XZW0": "URTH",
    "MWRD": "URTH",
    "GLDW": "URTH",

    # =========================================================
    # EUROPE / EM supplémentaires
    # =========================================================
    "EUNA": "VGK",
    "EUN2": "VGK",
    "EUNH": "VGK",
    "SMEU": "VGK",
    "XMES": "VGK",
    "XMZB": "VGK",
    "IQQ0": "VGK",

    "EUNM": "EEM",
    "EMQQ": "EEM",
    "CEMA": "EEM",
    "AEME": "EEM",
    "XMEM": "EEM",
    "EMXC": "EEM",
    "XCEM": "EEM",
    "FRDM": "EEM",
    "DGS": "EEM",
    "EEMS": "EEM",
})

ETF_PROXY_KEYWORDS = {
    "URTH": [
        "MSCI WORLD", "WORLD", "DEVELOPED WORLD", "GLOBAL EQUITY", "GLOBAL STOCK",
        "CORE MSCI WORLD", "WORLD UCITS", "MSCI WORLD UCITS",
        "WORLD INDEX", "DEVELOPED MARKETS", "MSCI DM", "FTSE DEVELOPED"
    ],
    "ACWI": [
        "ACWI", "ALL COUNTRY WORLD", "ALL-WORLD", "FTSE ALL-WORLD",
        "MSCI ACWI", "GLOBAL ALL CAP", "TOTAL WORLD", "ALL COUNTRY", "ALL WORLD"
    ],
    "SPY": [
        "S&P 500", "SP500", "S&P500", "CORE S&P 500", "US LARGE CAP",
        "USA LARGE CAP", "US LARGE BLEND", "SPDR S&P 500", "S&P UCITS"
    ],
    "VTI": [
        "TOTAL MARKET", "TOTAL STOCK MARKET", "US TOTAL MARKET",
        "BROAD MARKET", "US BROAD MARKET", "TOTAL US MARKET"
    ],
    "QQQ": [
        "NASDAQ 100", "NASDAQ100", "NDX", "QQQ", "NASDAQ-100"
    ],
    "VGK": [
        "MSCI EUROPE", "EUROPE", "STOXX EUROPE", "PAN EUROPE",
        "EUROPE UCITS", "EUROPE LARGE CAP", "EUROPE EQUITY"
    ],
    "EZU": [
        "EURO STOXX", "EUROZONE", "EMU", "EURO AREA"
    ],
    "EEM": [
        "EMERGING", "EMERGENTS", "MSCI EM", "MSCI EMERGING", "EM",
        "EMERGING MARKETS", "EMERGING MARKET", "CHINA", "INDIA", "ASIA EX JAPAN"
    ],

    "XLK": ["TECHNOLOGY", "INFORMATION TECHNOLOGY", "TECH", "DIGITAL", "SOFTWARE", "SEMICONDUCTOR"],
    "XLF": ["FINANCIAL", "FINANCE", "BANKS", "INSURANCE", "FINANCIAL SERVICES"],
    "XLV": ["HEALTHCARE", "HEALTH CARE", "HEALTH", "BIOTECH", "PHARMA"],
    "XLE": ["ENERGY", "OIL", "GAS"],
    "XLI": ["INDUSTRIAL", "INDUSTRIALS", "AEROSPACE", "TRANSPORT"],
    "XLY": ["CONSUMER DISCRETIONARY", "CONSUMER CYCLICAL", "RETAIL", "AUTOMOBILE"],
    "XLP": ["CONSUMER STAPLES", "CONSUMER DEFENSIVE", "STAPLES"],
    "XLB": ["MATERIALS", "BASIC MATERIALS", "CHEMICALS", "MINING"],
    "XLU": ["UTILITIES", "UTILITY"],
    "XLRE": ["REAL ESTATE", "REIT", "PROPERTY"],
    "XLC": ["COMMUNICATION", "COMMUNICATION SERVICES", "TELECOM", "MEDIA"],
}

def _infer_proxy_ticker(ticker: str, info: dict) -> str | None:
    """
    Essaie de trouver un ETF proxy à partir du ticker, du nom, de la catégorie, etc.
    """
    canon = _canon_ticker(ticker)

    # 1) matching direct via alias DB
    if canon in ETF_DB_ALIASES:
        return ETF_DB_ALIASES[canon]

    # 2) matching sur nom / catégorie / family
    text_parts = [
        info.get("longName", ""),
        info.get("shortName", ""),
        info.get("category", ""),
        info.get("fundFamily", ""),
        info.get("legalType", ""),
        info.get("fundInceptionDate", ""),
    ]
    blob = " ".join([str(x).upper() for x in text_parts if x])

    # 3) matching heuristique par mots-clés
    for proxy, keywords in ETF_PROXY_KEYWORDS.items():
        if any(k in blob for k in keywords):
            return proxy

    # 4) heuristiques ticker ultra larges
    if any(x in canon for x in [
        "CW8", "EWLD", "IWDA", "SWDA", "WRD", "LCWD", "EUNL", "WPEA", "XDWD", "IWRD"
    ]):
        return "URTH"

    if any(x in canon for x in [
        "ACWI", "VWCE", "VWRL", "VT", "ISAC", "SSAC"
    ]):
        return "ACWI"

    if any(x in canon for x in [
        "SP5", "SXR8", "VUSA", "VUAA", "CSPX", "SPY", "VOO", "IVV", "SPYL", "CSSPX"
    ]):
        return "SPY"

    if any(x in canon for x in [
        "VTI", "ITOT", "SCHB"
    ]):
        return "VTI"

    if any(x in canon for x in [
        "QQQ", "QQQM", "CNDX", "SXRV", "EQQQ", "CSNDX", "NDX"
    ]):
        return "QQQ"

    if any(x in canon for x in [
        "VGK", "IEUR", "IMEU", "MEUD", "ESE", "LYXEL", "EZU"
    ]):
        return "VGK"

    if any(x in canon for x in [
        "EEM", "VWO", "IEMA", "EMIM", "VFEM", "PAEEM", "INDA", "FXI", "MCHI", "KWEB", "ASHR", "AAXJ"
    ]):
        return "EEM"

    # Sectoriels
    if any(x in canon for x in ["XLK", "VGT", "IYW"]):
        return "XLK"
    if any(x in canon for x in ["XLF", "VFH", "IYF"]):
        return "XLF"
    if any(x in canon for x in ["XLV", "VHT", "IYH"]):
        return "XLV"
    if any(x in canon for x in ["XLY", "VCR", "RTH"]):
        return "XLY"
    if any(x in canon for x in ["XLC", "VOX", "IYZ"]):
        return "XLC"
    if any(x in canon for x in ["XLE", "VDE", "IYE"]):
        return "XLE"
    if any(x in canon for x in ["XLP", "VDC", "IYK"]):
        return "XLP"
    if any(x in canon for x in ["XLI", "VIS", "IYJ"]):
        return "XLI"
    if any(x in canon for x in ["XLB", "VAW", "IYM"]):
        return "XLB"
    if any(x in canon for x in ["XLU", "VPU", "IDU"]):
        return "XLU"
    if any(x in canon for x in ["XLRE", "VNQ", "IYR"]):
        return "XLRE"

    # ETF style / factor -> broad US proxy
    if any(x in canon for x in [
        "VUG", "VTV", "IWF", "IWD", "QUAL", "MTUM", "USMV", "SIZE", "VLUE"
    ]):
        return "SPY"

    return None

# ─────────────────────────────────────────────────────────────────────────────
# Fonctions principales
# ─────────────────────────────────────────────────────────────────────────────

def get_ticker_info(ticker: str) -> dict:
    """
    Retourne les infos de base d'un ticker (nom, secteur, pays, type).
    Résultat mis en cache 1h.
    Version plus robuste pour les ETFs.
    """
    key = f"info_{ticker}"
    cached = _cache_get(key)
    if cached:
        return cached

    info = _get_info_safe(ticker)

    quote_type = str(info.get("quoteType", "")).upper()
    long_name  = info.get("longName") or info.get("shortName") or ticker
    raw_sector = info.get("sector", "Autres")
    country    = info.get("country", "N/A")

    canon = _canon_ticker(ticker)
    inferred_proxy = _infer_proxy_ticker(ticker, info)

    is_etf = (
        quote_type in {"ETF", "MUTUALFUND", "INDEX"} or
        canon in ETF_DB_ALIASES or
        inferred_proxy is not None or
        "ETF" in str(long_name).upper()
    )

    result = {
        "ticker":  ticker,
        "name":    long_name,
        "sector":  _map_sector(raw_sector),
        "country": country,
        "type":    "ETF" if is_etf else "Action",
        "valid":   bool(info) or canon in ETF_DB_ALIASES or inferred_proxy is not None,
    }

    _cache_set(key, result)
    return result


def get_etf_sector_weights(ticker: str) -> dict[str, float] | None:
    """
    Retourne la décomposition sectorielle d'un ETF.
    Ordre de priorité :
    1. base hardcodée exacte
    2. alias / ticker canonique
    3. yfinance funds_data.sector_weightings
    4. proxy déduit du nom/catégorie/ticker
    5. None si rien de fiable
    """
    if ticker in ETF_SECTOR_DB:
        return _normalize_weights(ETF_SECTOR_DB[ticker])

    canon = _canon_ticker(ticker)
    if canon in ETF_DB_ALIASES:
        base_ticker = ETF_DB_ALIASES[canon]
        return _normalize_weights(ETF_SECTOR_DB.get(base_ticker))

    key = f"etf_sectors_{ticker}"
    cached = _cache_get(key)
    if cached is not None:
        return cached

    info = _get_info_safe(ticker)

    try:
        t = yf.Ticker(ticker)
        raw = t.funds_data.sector_weightings
        if raw:
            weights = {}
            for sector_raw, w in raw.items():
                mapped = _map_sector(str(sector_raw))
                try:
                    weights[mapped] = weights.get(mapped, 0.0) + float(w)
                except Exception:
                    pass

            weights = _normalize_weights(weights)
            if weights:
                _cache_set(key, weights)
                return weights
    except Exception:
        pass

    proxy = _infer_proxy_ticker(ticker, info)
    if proxy and proxy in ETF_SECTOR_DB:
        proxied = _normalize_weights(ETF_SECTOR_DB[proxy])
        _cache_set(key, proxied)
        return proxied

    _cache_set(key, None)
    return None


def get_price_history(ticker: str, period: str = "1y"):
    """
    Retourne l'historique de prix de clôture (pandas Series).
    """
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
    Version plus robuste : renormalise les décompositions ETF et limite les pertes dans 'Autres'.
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
                etf_sectors = _normalize_weights(etf_sectors)
                for sector, sw in etf_sectors.items():
                    sector_totals[sector] = sector_totals.get(sector, 0.0) + weight * sw
            else:
                sector_totals["Autres"] = sector_totals.get("Autres", 0.0) + weight

        else:
            sector = info["sector"]
            sector_totals[sector] = sector_totals.get(sector, 0.0) + weight

    return _normalize_weights(sector_totals) or {}


def get_benchmark_sectors(benchmark_name: str) -> dict[str, float]:
    """
    Retourne la décomposition sectorielle du benchmark sélectionné.
    """
    ticker = BENCHMARK_TICKERS.get(benchmark_name, "URTH")
    sectors = get_etf_sector_weights(ticker)
    if sectors:
        return _normalize_weights(sectors)
    return _normalize_weights(ETF_SECTOR_DB["URTH"]) or {}
