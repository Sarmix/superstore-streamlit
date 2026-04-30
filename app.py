import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Superstore Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Datos ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("superstore.csv", encoding="latin-1")
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
    df["Year"]  = df["Order Date"].dt.year
    df["Month"] = df["Order Date"].dt.to_period("M").astype(str)
    df["Disc Bucket"] = pd.cut(
        df["Discount"],
        bins=[-0.01, 0, 0.10, 0.20, 0.30, 0.50, 0.81],
        labels=["0%", "1-10%", "11-20%", "21-30%", "31-50%", ">50%"],
    )
    return df

df = load_data()

# ── Colores ────────────────────────────────────────────────────────────────────
BLUE   = "#378ADD"
GREEN  = "#1D9E75"
RED    = "#E24B4A"
AMBER  = "#BA7517"
DIV    = [[0, "#E24B4A"], [0.5, "#FAE8C0"], [1, "#1D9E75"]]
REGION = {"West": GREEN, "East": BLUE, "Central": RED, "South": AMBER}
CAT    = {"Furniture": AMBER, "Office Supplies": BLUE, "Technology": GREEN}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtros")
    sel_years = st.multiselect("Año",      sorted(df["Year"].unique()),     default=sorted(df["Year"].unique()))
    sel_cats  = st.multiselect("Categoría", sorted(df["Category"].unique()), default=sorted(df["Category"].unique()))
    sel_regs  = st.multiselect("Región",    sorted(df["Region"].unique()),   default=sorted(df["Region"].unique()))
    sel_segs  = st.multiselect("Segmento",  sorted(df["Segment"].unique()),  default=sorted(df["Segment"].unique()))

dff = df[
    df["Year"].isin(sel_years) &
    df["Category"].isin(sel_cats) &
    df["Region"].isin(sel_regs) &
    df["Segment"].isin(sel_segs)
].copy()

total_sales  = dff["Sales"].sum()
total_profit = dff["Profit"].sum()
margen = (total_profit / total_sales * 100) if total_sales > 0 else 0

with st.sidebar:
    st.markdown("---")
    st.metric("Órdenes",  f"{len(dff):,}")
    st.metric("Ventas",   f"${total_sales:,.0f}")
    st.metric("Profit",   f"${total_profit:,.0f}")
    st.metric("Margen",   f"{margen:.1f}%")

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🛒 Superstore Sales — Dashboard")
st.caption("Dataset: Sample Superstore · 9,994 órdenes · 2014-2017 · Proyecto 2")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Órdenes",    f"{len(dff):,}")
c2.metric("Ventas",     f"${total_sales/1e6:.2f}M")
c3.metric("Profit",     f"${total_profit/1e3:.1f}K")
c4.metric("Margen",     f"{margen:.1f}%")
c5.metric("Categorías", f"{dff['Category'].nunique()}")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# H1 — Comparación por Categoría
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("H1 · Furniture vende casi tanto como Technology pero su margen es 7× menor")

cat_df = (
    dff.groupby("Category", as_index=False)
    .agg(Sales=("Sales","sum"), Profit=("Profit","sum"))
)
cat_df["Margin"] = cat_df["Profit"] / cat_df["Sales"] * 100

col1, col2 = st.columns(2)

with col1:
    fig = go.Figure()
    fig.add_bar(name="Ventas", x=cat_df["Category"], y=cat_df["Sales"],
                marker_color=BLUE, opacity=0.85)
    fig.add_bar(name="Profit", x=cat_df["Category"], y=cat_df["Profit"],
                marker_color=GREEN, opacity=0.85)
    fig.update_layout(
        title="Ventas vs Profit por Categoría ($)",
        barmode="group", plot_bgcolor="white",
        xaxis_title=None, yaxis_tickprefix="$",
        yaxis_gridcolor="#f0f0f0",
        legend=dict(orientation="h", y=1.12),
        margin=dict(t=60, b=20),
    )
    st.plotly_chart(fig, use_container_width=True, key="h1a")

with col2:
    fig2 = px.bar(
        cat_df.sort_values("Margin"),
        x="Margin", y="Category", orientation="h",
        color="Margin",
        color_continuous_scale=["#E24B4A", "#FAE8C0", "#1D9E75"],
        color_continuous_midpoint=10,
        text=cat_df.sort_values("Margin")["Margin"].apply(lambda v: f"{v:.1f}%"),
        title="Margen de ganancia por Categoría (%)",
    )
    fig2.update_traces(textposition="outside")
    fig2.update_layout(
        plot_bgcolor="white", coloraxis_showscale=False,
        xaxis_ticksuffix="%", xaxis_gridcolor="#f0f0f0",
        yaxis_title=None, margin=dict(t=60, b=20),
    )
    st.plotly_chart(fig2, use_container_width=True, key="h1b")

st.caption("💡 Furniture: $742K en ventas, 2.5% de margen. Technology y Office Supplies operan al 17%.")
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# H2 — Distribución por Sub-Categoría
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("H2 · Tables, Bookcases y Supplies se venden a pérdida neta")

sub_df = (
    dff.groupby("Sub-Category", as_index=False)
    .agg(Profit=("Profit","sum"))
    .sort_values("Profit")
)
fig3 = px.bar(
    sub_df, x="Profit", y="Sub-Category", orientation="h",
    color="Profit",
    color_continuous_scale=["#E24B4A", "#FAE8C0", "#1D9E75"],
    color_continuous_midpoint=0,
    text=sub_df["Profit"].apply(lambda v: f"${v:,.0f}"),
    title="Profit total por Sub-Categoría",
)
fig3.update_traces(textposition="outside")
fig3.update_layout(
    plot_bgcolor="white", coloraxis_showscale=False,
    xaxis_tickprefix="$", xaxis_gridcolor="#f0f0f0",
    yaxis_title=None, height=480, margin=dict(t=60, b=20),
)
fig3.add_vline(x=0, line_width=1.5, line_color="#888", line_dash="dash")
st.plotly_chart(fig3, use_container_width=True, key="h2")

st.caption("💡 Tables pierde $17,725 vendiendo $207K. Copiers es la más rentable: $55,617.")
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# H3 — Descuento vs Profit
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("H3 · Descuentos mayores al 20% invierten la rentabilidad")

col3, col4 = st.columns(2)

with col3:
    disc_df = (
        dff.groupby("Disc Bucket", observed=True)
        .agg(avg_profit=("Profit","mean"), n=("Profit","count"))
        .reset_index()
    )
    fig4 = px.bar(
        disc_df, x="Disc Bucket", y="avg_profit",
        color="avg_profit",
        color_continuous_scale=["#E24B4A", "#FAE8C0", "#1D9E75"],
        color_continuous_midpoint=0,
        text=disc_df["avg_profit"].apply(lambda v: f"${v:,.0f}"),
        title="Profit promedio por nivel de descuento",
    )
    fig4.update_traces(textposition="outside")
    fig4.update_layout(
        plot_bgcolor="white", coloraxis_showscale=False,
        xaxis_title="Nivel de descuento",
        yaxis_title="Profit promedio ($)", yaxis_tickprefix="$",
        yaxis_gridcolor="#f0f0f0", margin=dict(t=60, b=20),
    )
    fig4.add_hline(y=0, line_width=1.5, line_color="#888", line_dash="dash")
    st.plotly_chart(fig4, use_container_width=True, key="h3a")

with col4:
    samp = dff.sample(min(1200, len(dff)), random_state=42)
    fig5 = px.scatter(
        samp, x="Discount", y="Profit", color="Category",
        color_discrete_map=CAT,
        opacity=0.45,
        title="Scatter: Descuento vs Profit por Categoría",
    )
    fig5.update_layout(
        plot_bgcolor="white",
        xaxis_title="Descuento", xaxis_tickformat=".0%",
        xaxis_gridcolor="#f0f0f0",
        yaxis_title="Profit ($)", yaxis_tickprefix="$",
        yaxis_gridcolor="#f0f0f0",
        legend=dict(orientation="h", y=1.12),
        margin=dict(t=60, b=20),
    )
    fig5.add_vline(x=0.20, line_width=1.5, line_color=RED, line_dash="dash",
                   annotation_text="20% ⚠", annotation_position="top right")
    st.plotly_chart(fig5, use_container_width=True, key="h3b")

st.caption("💡 Umbral crítico: 20%. Por encima el profit colapsa de +$25 a -$156. Correlación: -0.22.")
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# H4 — Evolución Temporal
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("H4 · Las ventas crecen +51% en 4 años con pico estacional cada noviembre")

time_df = (
    dff.groupby("Month", as_index=False)
    .agg(Sales=("Sales","sum"))
    .sort_values("Month")
)
time_df["IsNov"] = time_df["Month"].str.endswith("-11")

fig6 = go.Figure()
fig6.add_trace(go.Scatter(
    x=time_df["Month"], y=time_df["Sales"],
    fill="tozeroy", fillcolor="rgba(55,138,221,0.10)",
    line=dict(color=BLUE, width=2),
    name="Ventas mensuales",
))
nov = time_df[time_df["IsNov"]]
fig6.add_trace(go.Scatter(
    x=nov["Month"], y=nov["Sales"],
    mode="markers", marker=dict(color=RED, size=10, symbol="circle"),
    name="Pico noviembre",
))
fig6.update_layout(
    title="Evolución mensual de Ventas (2014–2017)",
    plot_bgcolor="white",
    xaxis_title=None, xaxis_tickangle=45, xaxis_gridcolor="#f0f0f0",
    yaxis_title="Ventas ($)", yaxis_tickprefix="$", yaxis_gridcolor="#f0f0f0",
    legend=dict(orientation="h", y=1.12),
    margin=dict(t=60, b=60),
)
st.plotly_chart(fig6, use_container_width=True, key="h4a")

yr_df = (
    dff.groupby("Year", as_index=False)
    .agg(Sales=("Sales","sum"))
)
yr_df["Growth"] = yr_df["Sales"].pct_change() * 100

col5, col6 = st.columns(2)
with col5:
    fig7 = px.bar(
        yr_df, x="Year", y="Sales",
        color="Sales",
        color_continuous_scale=["#B5D4F4", "#185FA5"],
        text=yr_df["Sales"].apply(lambda v: f"${v/1e3:.0f}K"),
        title="Ventas anuales totales",
    )
    fig7.update_traces(textposition="outside")
    fig7.update_layout(
        plot_bgcolor="white", coloraxis_showscale=False,
        xaxis_title=None, yaxis_tickprefix="$", yaxis_gridcolor="#f0f0f0",
        margin=dict(t=60, b=20),
    )
    st.plotly_chart(fig7, use_container_width=True, key="h4b")

with col6:
    yr_g = yr_df.dropna(subset=["Growth"]).copy()
    fig8 = px.bar(
        yr_g, x="Year", y="Growth",
        color="Growth",
        color_continuous_scale=["#E24B4A", "#FAE8C0", "#1D9E75"],
        color_continuous_midpoint=0,
        text=yr_g["Growth"].apply(lambda v: f"{v:.1f}%"),
        title="Crecimiento anual de ventas (%)",
    )
    fig8.update_traces(textposition="outside")
    fig8.update_layout(
        plot_bgcolor="white", coloraxis_showscale=False,
        xaxis_title=None, yaxis_ticksuffix="%", yaxis_gridcolor="#f0f0f0",
        margin=dict(t=60, b=20),
    )
    fig8.add_hline(y=0, line_width=1.2, line_color="#888", line_dash="dash")
    st.plotly_chart(fig8, use_container_width=True, key="h4c")

st.caption("💡 Caída 2.8% en 2015, recuperación: +29% en 2016 y +20% en 2017. Nov es el mes récord cada año.")
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# H5 — Composición por Región
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("H5 · West lidera en rentabilidad — Central factura mucho pero gana poco")

reg_df = (
    dff.groupby("Region", as_index=False)
    .agg(Sales=("Sales","sum"), Profit=("Profit","sum"))
)
reg_df["Margin"] = reg_df["Profit"] / reg_df["Sales"] * 100

col7, col8, col9 = st.columns(3)

with col7:
    fig9 = px.pie(
        reg_df, values="Sales", names="Region",
        color="Region", color_discrete_map=REGION,
        hole=0.42, title="Composición de ventas por Región",
    )
    fig9.update_traces(textinfo="percent+label", textposition="outside")
    fig9.update_layout(showlegend=False, margin=dict(t=60, b=20))
    st.plotly_chart(fig9, use_container_width=True, key="h5a")

with col8:
    reg_long = reg_df.melt(id_vars="Region", value_vars=["Sales","Profit"],
                           var_name="Metrica", value_name="Valor")
    fig10 = px.bar(
        reg_long, x="Region", y="Valor", color="Metrica",
        barmode="group",
        color_discrete_map={"Sales": BLUE, "Profit": GREEN},
        title="Ventas vs Profit por Región",
    )
    fig10.update_layout(
        plot_bgcolor="white", legend_title=None,
        legend=dict(orientation="h", y=1.12),
        xaxis_title=None, yaxis_tickprefix="$", yaxis_gridcolor="#f0f0f0",
        margin=dict(t=60, b=20),
    )
    st.plotly_chart(fig10, use_container_width=True, key="h5b")

with col9:
    fig11 = px.bar(
        reg_df.sort_values("Margin"),
        x="Margin", y="Region", orientation="h",
        color="Margin",
        color_continuous_scale=["#E24B4A", "#FAE8C0", "#1D9E75"],
        color_continuous_midpoint=12,
        text=reg_df.sort_values("Margin")["Margin"].apply(lambda v: f"{v:.1f}%"),
        title="Margen de ganancia por Región",
    )
    fig11.update_traces(textposition="outside")
    fig11.update_layout(
        plot_bgcolor="white", coloraxis_showscale=False,
        xaxis_ticksuffix="%", xaxis_gridcolor="#f0f0f0",
        yaxis_title=None, margin=dict(t=60, b=20),
    )
    st.plotly_chart(fig11, use_container_width=True, key="h5c")

st.caption("💡 West: $725K y 14.9% de margen. Central: $501K pero solo 7.9% — el peor del negocio.")
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#aaa;font-size:12px'>"
    "Herramientas y Visualización de Datos · Proyecto 2 · Fundación Universitaria Los Libertadores"
    "</p>",
    unsafe_allow_html=True,
)
