"""
app.py — Exupéry : Diagnostiqueur de Portefeuille
Interface Streamlit principale.
"""

import streamlit as st
from modules.charts import make_radar_sectoriel, SECTORS
from modules.market_data import (
    get_ticker_info, build_portfolio_sectors,
    get_benchmark_sectors, get_price_history,
    BENCHMARK_TICKERS, BENCHMARK_LABELS,
)
from modules.diagnostics import (
    compute_esan, compute_esap, compute_sector_std,
    compute_indice_correspondance, compute_hhi,
    compute_sector_gap_table, compute_performance,
    esan_label, indice_label, hhi_label,
)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration page
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Exupéry — Diagnostiqueur de Portefeuille",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Exupéry — Diagnostiqueur de Portefeuille")

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar : Benchmark
# ─────────────────────────────────────────────────────────────────────────────
benchmark_name = st.sidebar.selectbox(
    "Benchmark",
    list(BENCHMARK_TICKERS.keys()),
    index=0,
)

# ─────────────────────────────────────────────────────────────────────────────
# Formulaire de saisie du portefeuille
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.subheader("Mon portefeuille")

DEFAULT_POSITIONS = [
    {"ticker": "SPY",  "amount": 1000.0},
    {"ticker": "EEM",  "amount": 1000.0},
]

if "positions" not in st.session_state:
    st.session_state.positions = DEFAULT_POSITIONS.copy()

with st.sidebar.form("portfolio_form"):
    st.markdown("**Ajouter des positions :**")

    nb_lignes = st.number_input("Nombre de lignes", min_value=1, max_value=20,
                                 value=len(st.session_state.positions), step=1)

    inputs = []
    for i in range(int(nb_lignes)):
        col1, col2 = st.columns([2, 2])
        default_ticker = st.session_state.positions[i]["ticker"] if i < len(st.session_state.positions) else ""
        default_amount = st.session_state.positions[i]["amount"] if i < len(st.session_state.positions) else 1000.0
        with col1:
            t = st.text_input(f"Ticker {i+1}", value=default_ticker, key=f"t_{i}").upper().strip()
        with col2:
            a = st.number_input(f"Montant {i+1} (€)", value=default_amount,
                                min_value=0.0, step=100.0, key=f"a_{i}")
        inputs.append({"ticker": t, "amount": a})

    col_analyser, col_vider = st.columns(2)
    with col_analyser:
        analyser = st.form_submit_button("🔍 Analyser", use_container_width=True)
    with col_vider:
        vider = st.form_submit_button("🗑️ Vider", use_container_width=True)

if vider:
    st.session_state.positions = DEFAULT_POSITIONS.copy()
    st.rerun()

if analyser:
    st.session_state.positions = [p for p in inputs if p["ticker"]]

# ─────────────────────────────────────────────────────────────────────────────
# Calculs
# ─────────────────────────────────────────────────────────────────────────────
positions = [p for p in st.session_state.positions if p["ticker"] and p["amount"] > 0]

if not positions:
    st.info("Saisis ton portefeuille dans la barre latérale et clique sur Analyser.")
    st.stop()

# Récupération infos tickers
ticker_infos = {}
invalid_tickers = []
etf_no_breakdown = []

for p in positions:
    info = get_ticker_info(p["ticker"])
    ticker_infos[p["ticker"]] = info
    if not info["valid"]:
        invalid_tickers.append(p["ticker"])
    elif info["type"] == "ETF":
        from modules.market_data import get_etf_sector_weights
        if get_etf_sector_weights(p["ticker"]) is None:
            etf_no_breakdown.append(p["ticker"])

# Alertes
for t in invalid_tickers:
    st.error(f"🔴 **{t}** introuvable — essayez `{t}.PA`, `{t}.AS` ou `{t}.L`")

for t in etf_no_breakdown:
    st.warning(f"🟡 **{t}** : ETF sans décomposition sectorielle disponible (comptabilisé dans 'Autres')")

# Décomposition sectorielle
ptf_sectors   = build_portfolio_sectors(positions)
bench_sectors = get_benchmark_sectors(benchmark_name)
bench_label   = BENCHMARK_LABELS[benchmark_name]

# Indicateurs
esan_val  = compute_esan(ptf_sectors, bench_sectors)
esap_val  = compute_esap(ptf_sectors, bench_sectors)
std_val   = compute_sector_std(ptf_sectors, bench_sectors)
ic_val    = compute_indice_correspondance(ptf_sectors, bench_sectors)
hhi_val   = compute_hhi(positions)
gap_table = compute_sector_gap_table(ptf_sectors, bench_sectors)

esan_lvl, esan_color = esan_label(esan_val)
ic_lvl,   ic_color   = indice_label(ic_val)
hhi_lvl,  hhi_color  = hhi_label(hhi_val)

# ─────────────────────────────────────────────────────────────────────────────
# Onglets
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["Vue d'ensemble", "Diversification", "Risque & Corrélations", "Performance"]
)

# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 1 — Vue d'ensemble
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    # ── KPIs performance ─────────────────────────────────────────────────────
    total_amount = sum(p["amount"] for p in positions)

    main_ticker  = positions[0]["ticker"]
    bench_ticker = BENCHMARK_TICKERS[benchmark_name]

    prices_ptf   = get_price_history(main_ticker)
    prices_bench = get_price_history(bench_ticker)

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    if prices_ptf is not None and prices_bench is not None:
        kpis = compute_performance(prices_ptf, prices_bench)
        with kpi_col1:
            delta_str = f"{kpis['alpha']:+.1%} vs {bench_label}"
            st.metric("Performance", f"{kpis['perf_ptf']:.1%}", delta_str)
        with kpi_col2:
            st.metric("Volatilité annualisée", f"{kpis['vol_ptf']:.1%}")
        with kpi_col3:
            st.metric("Max Drawdown", f"{kpis['max_drawdown_ptf']:.1%}")
        with kpi_col4:
            st.metric("Ratio de Sharpe", f"{kpis['sharpe_ptf']:.2f}")
    else:
        with kpi_col1:
            st.metric("Valeur totale", f"{total_amount:,.0f} €")
        with kpi_col2:
            st.metric("Positions", len(positions))
        with kpi_col3:
            st.metric("HHI", f"{hhi_val:.3f}", hhi_lvl)
        with kpi_col4:
            st.metric("Indice Correspondance", f"{ic_val:.0f}/100", ic_lvl)

    st.markdown("---")

    # ── Radar + indicateurs ───────────────────────────────────────────────────
    col_radar, col_indic = st.columns([3, 2])

    with col_radar:
        fig = make_radar_sectoriel(
            portfolio_weights=ptf_sectors,
            benchmark_weights=bench_sectors,
            benchmark_label=bench_label,
        )
        st.plotly_chart(fig, use_container_width=True)

        # ESAN sous le radar
        st.markdown(
            f"<div style='text-align:center; font-size:14px; color:#6E6E8E;'>"
            f"ESAN : <b style='color:{esan_color}'>{esan_val:.1%}</b> — {esan_lvl}"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col_indic:
        st.markdown("### Indicateurs clés")

        st.markdown(
            f"**Indice de Correspondance**  \n"
            f"<span style='font-size:28px; color:{ic_color}'><b>{ic_val:.0f}</b></span>/100  \n"
            f"*{ic_lvl}*",
            unsafe_allow_html=True,
        )
        st.progress(int(ic_val) / 100)

        st.markdown("---")
        st.markdown(f"**HHI (concentration)** : `{hhi_val:.3f}` — *{hhi_lvl}*")
        st.markdown(f"**σ écart sectoriel** : `{std_val:.1%}`")
        st.markdown(f"**ESAP** : `{esap_val:.1%}`")
        st.markdown(f"**ESAN** : `{esan_val:.1%}` — *{esan_lvl}*")

        st.markdown("---")
        with st.expander("Détail par secteur"):
            import pandas as pd
            df_gap = pd.DataFrame(gap_table)
            df_gap["Portefeuille"] = df_gap["Portefeuille"].map("{:.1%}".format)
            df_gap["Benchmark"]    = df_gap["Benchmark"].map("{:.1%}".format)
            df_gap["Écart"]        = df_gap["Écart"].map("{:+.1%}".format)
            df_gap["|Écart|"]      = df_gap["|Écart|"].map("{:.1%}".format)
            st.dataframe(df_gap, hide_index=True, use_container_width=True)

    st.markdown("---")

    # ── Tableau des positions ─────────────────────────────────────────────────
    st.subheader("Positions")
    import pandas as pd
    rows = []
    for p in positions:
        info = ticker_infos.get(p["ticker"], {})
        poids = p["amount"] / total_amount if total_amount > 0 else 0
        rows.append({
            "Ticker":  p["ticker"],
            "Nom":     info.get("name", p["ticker"]),
            "Type":    info.get("type", "—"),
            "Secteur": info.get("sector", "—"),
            "Pays":    info.get("country", "—"),
            "Montant": f"{p['amount']:,.0f} €",
            "Poids":   f"{poids:.1%}",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 2 — Diversification
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    import plotly.graph_objects as go
    import plotly.express as px
    import pandas as pd

    col_d1, col_d2 = st.columns(2)

    # Donut sectoriel
    with col_d1:
        st.subheader("Répartition sectorielle")
        labels = [s for s in SECTORS if ptf_sectors.get(s, 0) > 0]
        values = [ptf_sectors.get(s, 0) for s in SECTORS if ptf_sectors.get(s, 0) > 0]
        fig_donut = go.Figure(go.Pie(
            labels=labels, values=values, hole=0.45,
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
        ))
        fig_donut.update_layout(showlegend=False, height=400,
                                 margin=dict(t=30, b=10, l=10, r=10))
        st.plotly_chart(fig_donut, use_container_width=True)

    # Barres sectorielles (ptf vs benchmark)
    with col_d2:
        st.subheader("Portefeuille vs Benchmark")
        df_bar = pd.DataFrame({
            "Secteur":     SECTORS,
            "Portefeuille": [ptf_sectors.get(s, 0) * 100 for s in SECTORS],
            bench_label:    [bench_sectors.get(s, 0) * 100 for s in SECTORS],
        })
        fig_bar = px.bar(
            df_bar.melt(id_vars="Secteur", var_name="Série", value_name="%"),
            x="Secteur", y="%", color="Série", barmode="group",
            color_discrete_map={"Portefeuille": "#E97132", bench_label: "#156082"},
            height=400,
        )
        fig_bar.update_layout(margin=dict(t=30, b=10, l=10, r=10),
                               xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)

    # Diagnostic synthétique
    st.markdown("---")
    st.subheader("Diagnostic")
    if ptf_sectors:
        dominant_sector = max(ptf_sectors, key=ptf_sectors.get)
        dominant_pct    = ptf_sectors[dominant_sector]
        first_line_w    = max(p["amount"] for p in positions) / total_amount if total_amount else 0

        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.metric("Secteur dominant", dominant_sector, f"{dominant_pct:.1%}")
        with col_s2:
            st.metric("1ère ligne", f"{first_line_w:.1%}",
                      "⚠️ > 20%" if first_line_w > 0.20 else "OK")
        with col_s3:
            st.metric("Concentration HHI", f"{hhi_val:.3f}", hhi_lvl)

# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 3 — Risque & Corrélations
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    import pandas as pd
    import plotly.figure_factory as ff

    tickers = [p["ticker"] for p in positions]

    if len(tickers) < 2:
        st.info("Ajoutez au moins 2 positions pour voir les corrélations.")
    else:
        with st.spinner("Chargement des données de corrélation..."):
            hist_data = {}
            for t in tickers:
                h = get_price_history(t)
                if h is not None:
                    hist_data[t] = h

        if len(hist_data) >= 2:
            df_prices = pd.DataFrame(hist_data).dropna()
            df_corr   = df_prices.pct_change().dropna().corr()

            # Heatmap
            st.subheader("Matrice de corrélation")
            z_text = [[f"{v:.2f}" for v in row] for row in df_corr.values]
            fig_corr = ff.create_annotated_heatmap(
                z=df_corr.values.tolist(),
                x=df_corr.columns.tolist(),
                y=df_corr.index.tolist(),
                annotation_text=z_text,
                colorscale="RdBu", reversescale=True,
                zmin=-1, zmax=1,
            )
            fig_corr.update_layout(height=400, margin=dict(t=30, b=30, l=30, r=30))
            st.plotly_chart(fig_corr, use_container_width=True)

            # Alertes corrélation élevée
            for i, t1 in enumerate(df_corr.columns):
                for j, t2 in enumerate(df_corr.columns):
                    if i < j and df_corr.loc[t1, t2] > 0.75:
                        st.warning(f"⚠️ Corrélation élevée : **{t1}** / **{t2}** = {df_corr.loc[t1, t2]:.2f}")
        else:
            st.warning("Données insuffisantes pour calculer les corrélations.")

# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 4 — Performance
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    import pandas as pd
    import plotly.graph_objects as go

    bench_ticker = BENCHMARK_TICKERS[benchmark_name]

    with st.spinner("Chargement des données de performance..."):
        prices_bench_hist = get_price_history(bench_ticker)

    if len(positions) == 1:
        prices_ptf_hist = get_price_history(positions[0]["ticker"])
    else:
        hists = {}
        for p in positions:
            h = get_price_history(p["ticker"])
            if h is not None:
                hists[p["ticker"]] = h / h.iloc[0]
        if hists:
            import pandas as pd_
            df_all = pd_.DataFrame(hists).dropna()
            weights = {p["ticker"]: p["amount"] / total_amount for p in positions if p["ticker"] in hists}
            df_all["ptf"] = sum(df_all[t] * w for t, w in weights.items())
            prices_ptf_hist = df_all["ptf"]
        else:
            prices_ptf_hist = None

    if prices_ptf_hist is not None and prices_bench_hist is not None:
        import pandas as pd
        df_perf = pd.DataFrame({
            "Portefeuille": prices_ptf_hist / prices_ptf_hist.iloc[0] - 1,
            bench_label:    prices_bench_hist / prices_bench_hist.iloc[0] - 1,
        }).dropna()

        fig_perf = go.Figure()
        fig_perf.add_trace(go.Scatter(
            x=df_perf.index, y=df_perf[bench_label],
            fill="tozeroy", name=bench_label,
            line=dict(color="#156082", width=1.5),
            fillcolor="rgba(21,96,130,0.15)",
        ))
        fig_perf.add_trace(go.Scatter(
            x=df_perf.index, y=df_perf["Portefeuille"],
            name="Portefeuille",
            line=dict(color="#E97132", width=2),
        ))
        fig_perf.update_layout(
            title="Performance relative (base 100)",
            yaxis_tickformat=".0%",
            height=450,
            legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center"),
            margin=dict(t=60, b=40, l=60, r=30),
        )
        st.plotly_chart(fig_perf, use_container_width=True)
    else:
        st.info("Données de performance non disponibles pour ce portefeuille.")
