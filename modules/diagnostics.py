"""
diagnostics.py
Calculs financiers : KPIs, ESAN, HHI, Indice de Correspondance.
"""

import math
from modules.charts import SECTORS


# ─────────────────────────────────────────────────────────────────────────────
# Utilitaires
# ─────────────────────────────────────────────────────────────────────────────

def _normalize(weights: dict[str, float]) -> dict[str, float]:
    """S'assure que les poids somment à 1 sur les secteurs Exupéry."""
    total = sum(weights.get(s, 0.0) for s in SECTORS)
    if total == 0:
        return {s: 0.0 for s in SECTORS}
    return {s: weights.get(s, 0.0) / total for s in SECTORS}


# ─────────────────────────────────────────────────────────────────────────────
# KPIs performance (nécessite l'historique de prix)
# ─────────────────────────────────────────────────────────────────────────────

def compute_performance(prices_ptf, prices_bench) -> dict:
    """
    Calcule les KPIs à partir de séries de prix (pandas Series).

    Returns
    -------
    dict avec : perf_ptf, perf_bench, alpha, vol_ptf, vol_bench,
                max_drawdown_ptf, sharpe_ptf
    """
    result = {}

    try:
        ret_ptf   = prices_ptf.pct_change().dropna()
        ret_bench = prices_bench.pct_change().dropna()

        # Performance totale
        result["perf_ptf"]   = float((prices_ptf.iloc[-1]  / prices_ptf.iloc[0])  - 1)
        result["perf_bench"] = float((prices_bench.iloc[-1] / prices_bench.iloc[0]) - 1)
        result["alpha"]      = result["perf_ptf"] - result["perf_bench"]

        # Volatilité annualisée
        result["vol_ptf"]   = float(ret_ptf.std()   * math.sqrt(252))
        result["vol_bench"] = float(ret_bench.std() * math.sqrt(252))

        # Max Drawdown portefeuille
        cumulative  = (1 + ret_ptf).cumprod()
        rolling_max = cumulative.cummax()
        drawdown    = (cumulative - rolling_max) / rolling_max
        result["max_drawdown_ptf"] = float(drawdown.min())

        # Ratio de Sharpe (taux sans risque = 3%)
        rf = 0.03
        annual_ret = float(ret_ptf.mean() * 252)
        result["sharpe_ptf"] = (annual_ret - rf) / result["vol_ptf"] if result["vol_ptf"] > 0 else 0.0

    except Exception:
        result = {
            "perf_ptf": 0.0, "perf_bench": 0.0, "alpha": 0.0,
            "vol_ptf": 0.0, "vol_bench": 0.0,
            "max_drawdown_ptf": 0.0, "sharpe_ptf": 0.0,
        }

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Indicateurs sectoriels
# ─────────────────────────────────────────────────────────────────────────────

def compute_sector_gap_table(ptf: dict[str, float], bench: dict[str, float]) -> list[dict]:
    """
    Calcule le tableau détaillé des écarts sectoriels.
    """
    ptf_n   = _normalize(ptf)
    bench_n = _normalize(bench)

    rows = []
    for s in SECTORS:
        wp = ptf_n.get(s, 0.0)
        wb = bench_n.get(s, 0.0)
        e  = wp - wb
        rows.append({
            "Secteur":      s,
            "Portefeuille": wp,
            "Benchmark":    wb,
            "Écart":        e,
            "|Écart|":      abs(e),
        })
    return rows


def compute_esan(ptf: dict[str, float], bench: dict[str, float]) -> float:
    """
    ESAN : écart sectoriel pondéré neutre.
    Formule : Σ ((wi_ptf + wi_bench) / 2) × |ei|
    Seuils : < 5% faible · 5–12% modéré · > 12% élevé
    """
    ptf_n   = _normalize(ptf)
    bench_n = _normalize(bench)

    return sum(
        ((ptf_n.get(s, 0.0) + bench_n.get(s, 0.0)) / 2) * abs(ptf_n.get(s, 0.0) - bench_n.get(s, 0.0))
        for s in SECTORS
    )


def compute_esap(ptf: dict[str, float], bench: dict[str, float]) -> float:
    """
    ESAP : écart pondéré par poids portefeuille.
    Formule : Σ wi_ptf × |ei|
    """
    ptf_n   = _normalize(ptf)
    bench_n = _normalize(bench)

    return sum(
        ptf_n.get(s, 0.0) * abs(ptf_n.get(s, 0.0) - bench_n.get(s, 0.0))
        for s in SECTORS
    )


def compute_sector_std(ptf: dict[str, float], bench: dict[str, float]) -> float:
    """
    σ — Écart-type des écarts sectoriels.
    Formule : sqrt(Σ(ei − ē)² / n)
    """
    ptf_n   = _normalize(ptf)
    bench_n = _normalize(bench)

    ecarts = [ptf_n.get(s, 0.0) - bench_n.get(s, 0.0) for s in SECTORS]
    mean_e = sum(ecarts) / len(ecarts)
    variance = sum((e - mean_e) ** 2 for e in ecarts) / len(ecarts)
    return math.sqrt(variance)


def compute_indice_correspondance(ptf: dict[str, float], bench: dict[str, float]) -> float:
    """
    Indice de Correspondance (0–100).
    Basé sur l'Active Share inverse : (1 − 0.5 × Σ|wi_ptf − wi_bench|) × 100
    100 = identique · 0 = aucun overlap
    Seuils : ≥ 70 proche · 40–70 modéré · < 40 très différent
    """
    ptf_n   = _normalize(ptf)
    bench_n = _normalize(bench)

    active_share = 0.5 * sum(abs(ptf_n.get(s, 0.0) - bench_n.get(s, 0.0)) for s in SECTORS)
    return max(0.0, (1 - active_share) * 100)


def compute_hhi(positions: list[dict]) -> float:
    """
    HHI — Herfindahl-Hirschman Index (concentration par ligne).
    Formule : Σ wi²
    Seuils : > 0.18 notable · > 0.25 forte
    """
    total = sum(p["amount"] for p in positions)
    if total == 0:
        return 0.0
    return sum((p["amount"] / total) ** 2 for p in positions)


# ─────────────────────────────────────────────────────────────────────────────
# Labels et interprétations
# ─────────────────────────────────────────────────────────────────────────────

def esan_label(esan: float) -> tuple[str, str]:
    """Retourne (niveau, couleur_hex) pour l'ESAN."""
    if esan < 0.05:
        return "Faible", "#2E7D32"
    elif esan < 0.12:
        return "Modéré", "#F9A825"
    else:
        return "Élevé", "#C62828"


def indice_label(score: float) -> tuple[str, str]:
    """Retourne (niveau, couleur_hex) pour l'Indice de Correspondance."""
    if score >= 70:
        return "Proche du benchmark", "#2E7D32"
    elif score >= 40:
        return "Écart modéré", "#F9A825"
    else:
        return "Très différent", "#C62828"


def hhi_label(hhi: float) -> tuple[str, str]:
    """Retourne (niveau, couleur_hex) pour le HHI."""
    if hhi > 0.25:
        return "Concentration forte", "#C62828"
    elif hhi > 0.18:
        return "Concentration notable", "#F9A825"
    else:
        return "Bien diversifié", "#2E7D32"
