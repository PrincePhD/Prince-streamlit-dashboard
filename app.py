import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Interactive Dashboard", page_icon="📊", layout="wide")
st.title("📊 Interactive Sales Dashboard")
st.caption("Explore the data with the filters in the sidebar, or upload your own CSV.")


@st.cache_data
def load_sample() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2025-01-01", "2025-12-31", freq="D")
    rows = []
    for d in dates:
        for region in ["North", "South", "East", "West"]:
            for category in ["Electronics", "Clothing", "Home", "Sports"]:
                units = int(rng.poisson(20))
                price = rng.uniform(10, 200)
                rows.append([d, region, category, units, round(units * price, 2)])
    return pd.DataFrame(rows, columns=["date", "region", "category", "units", "revenue"])


uploaded = st.sidebar.file_uploader("Upload CSV (optional)", type="csv")
if uploaded:
    df = pd.read_csv(uploaded)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
else:
    df = load_sample()

# ---- Sidebar filters ----
st.sidebar.header("Filters")
numeric_cols = df.select_dtypes("number").columns.tolist()
cat_cols = df.select_dtypes(exclude="number").columns.difference(["date"]).tolist()

for col in cat_cols[:3]:
    options = sorted(df[col].dropna().unique())
    chosen = st.sidebar.multiselect(col.title(), options, default=options)
    df = df[df[col].isin(chosen)]

if "date" in df.columns:
    lo, hi = df["date"].min().date(), df["date"].max().date()
    start, end = st.sidebar.date_input("Date range", (lo, hi), min_value=lo, max_value=hi)
    df = df[(df["date"].dt.date >= start) & (df["date"].dt.date <= end)]

if df.empty:
    st.warning("No data matches the current filters.")
    st.stop()

metric = st.sidebar.selectbox("Metric", numeric_cols, index=numeric_cols.index("revenue") if "revenue" in numeric_cols else 0)

# ---- KPIs ----
c1, c2, c3 = st.columns(3)
c1.metric(f"Total {metric}", f"{df[metric].sum():,.0f}")
c2.metric(f"Average {metric}", f"{df[metric].mean():,.1f}")
c3.metric("Rows", f"{len(df):,}")

# ---- Charts ----
left, right = st.columns(2)
if "date" in df.columns:
    ts = df.set_index("date")[metric].resample("W").sum().reset_index()
    left.plotly_chart(px.line(ts, x="date", y=metric, title=f"Weekly {metric}"), use_container_width=True)

if cat_cols:
    group = cat_cols[0]
    by_cat = df.groupby(group, as_index=False)[metric].sum()
    right.plotly_chart(px.bar(by_cat, x=group, y=metric, color=group, title=f"{metric.title()} by {group}"), use_container_width=True)

if len(cat_cols) > 1:
    pie = df.groupby(cat_cols[1], as_index=False)[metric].sum()
    st.plotly_chart(px.pie(pie, names=cat_cols[1], values=metric, title=f"{metric.title()} share by {cat_cols[1]}"), use_container_width=True)

with st.expander("View raw data"):
    st.dataframe(df, use_container_width=True)
    st.download_button("Download filtered CSV", df.to_csv(index=False), "filtered_data.csv", "text/csv")
