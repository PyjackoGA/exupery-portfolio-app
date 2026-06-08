import plotly.graph_objects as go

# ── Palette exacte issue du thème Excel 3.2.xlsm ─────────────────────────────
_COLOR_BENCHMARK      = "#156082"          # accent1 — bleu teal (MSCI W)
_COLOR_BENCHMARK_FILL = "rgba(21,96,130,0.50)"
_COLOR_PORTFOLIO      = "#E97132"          # accent2 — orange (Portefeuille)
_COLOR_PORTFOLIO_FILL = "rgba(248,181,138,0.50)"
_COLOR_TITLE          = "#6E6E8E"          # tx2 à 75% lum
_FONT                 = "Calibri, Arial, sans-serif"

# ── Secteurs (ordre horaire identique à l'Excel) ──────────────────────────────
SECTORS = [
    "Tech",
    "Finance",
    "Santé",
    "Conso. Cycl.",
    "Com",
    "Énergie",
    "Conso. Base",
    "Industrie",
    "Matériaux",
    "Services",
    "Immo.",
    "Liquidités",
    "Autres",
]


def make_radar_sectoriel(
    portfolio_weights: dict[str, float],
    benchmark_weights: dict[str, float],
    benchmark_label: str = "MSCI W",
) -> go.Figure:
    """
    Construit le radar "SCAN SECTORIELLE" Exupéry.

    Parameters
    ----------
    portfolio_weights : dict {secteur: poids en décimal, ex. 0.46}
    benchmark_weights : dict {secteur: poids en décimal}
    benchmark_label   : libellé affiché dans la légende (ex. "MSCI W", "S&P 500")

    Returns
    -------
    go.Figure Plotly prêt à être passé à st.plotly_chart()
    """
    # Valeurs en % dans l'ordre des secteurs
    ptf_vals   = [round(portfolio_weights.get(s, 0.0) * 100, 2) for s in SECTORS]
    bench_vals = [round(benchmark_weights.get(s, 0.0) * 100, 2) for s in SECTORS]

    # Fermeture du polygone (premier point répété en fin de liste)
    sectors_closed = SECTORS + [SECTORS[0]]
    ptf_closed     = ptf_vals + [ptf_vals[0]]
    bench_closed   = bench_vals + [bench_vals[0]]

    # Plage radiale autofit avec marge de 10 %
    max_val = max(max(ptf_vals), max(bench_vals), 1.0) * 1.10

    fig = go.Figure()

    # ── Trace 1 : Benchmark (affiché en dessous) ─────────────────────────────
    fig.add_trace(go.Scatterpolar(
        r=bench_closed,
        theta=sectors_closed,
        fill="toself",
        name=benchmark_label,
        line=dict(
            color=_COLOR_BENCHMARK,
            width=1.5,
            dash="dot",
        ),
        fillcolor=_COLOR_BENCHMARK_FILL,
        marker=dict(symbol="x", size=6, color=_COLOR_BENCHMARK),
        hovertemplate="<b>%{theta}</b><br>"
                      + benchmark_label
                      + " : %{r:.1f}%<extra></extra>",
    ))

    # ── Trace 2 : Portefeuille (affiché par-dessus) ───────────────────────────
    fig.add_trace(go.Scatterpolar(
        r=ptf_closed,
        theta=sectors_closed,
        fill="toself",
        name="Portefeuille",
        line=dict(
            color=_COLOR_PORTFOLIO,
            width=1.5,
            dash="dot",
        ),
        fillcolor=_COLOR_PORTFOLIO_FILL,
        marker=dict(symbol="x", size=6, color=_COLOR_PORTFOLIO),
        hovertemplate="<b>%{theta}</b><br>Portefeuille : %{r:.1f}%<extra></extra>",
    ))

    # ── Mise en forme ─────────────────────────────────────────────────────────
    fig.update_layout(
        title=dict(
            text="SCAN SECTORIELLE",
            font=dict(
                size=18,
                color=_COLOR_TITLE,
                family=_FONT,
            ),
            x=0.5,
            xanchor="center",
            y=0.97,
        ),
        polar=dict(
            bgcolor="white",
            radialaxis=dict(
                visible=False,
                range=[0, max_val],
            ),
            angularaxis=dict(
                tickfont=dict(
                    size=10,
                    color=_COLOR_BENCHMARK,
                    family=_FONT,
                ),
                linecolor=_COLOR_BENCHMARK,
                gridcolor=_COLOR_BENCHMARK,
                linewidth=0.75,
                gridwidth=0.75,
                direction="clockwise",
                rotation=90,
            ),
            gridshape="linear",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=9, color=_COLOR_TITLE, family=_FONT),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(t=80, b=50, l=80, r=80),
        height=600,
    )

    return fig
