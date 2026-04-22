"""
====================================================
Luxury Housing Sales Analysis — Bengaluru
Streamlit Dashboard
====================================================
Run: streamlit run app.py
Pre-requisite: Run clean_and_load.py first to generate luxury_housing.db
"""

import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Luxury Housing — Bengaluru",
    page_icon="🏙️",
    layout="wide",
)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    conn = sqlite3.connect("luxury_housing.db")
    df = pd.read_sql("SELECT * FROM luxury_housing_sales", conn)
    conn.close()
    return df

df = load_data()

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.title("🔍 Filters")
st.sidebar.markdown("Use these to slice all charts below.")

all_devs = sorted(df["Developer_Name"].unique())
sel_devs = st.sidebar.multiselect("Developer / Builder", all_devs, default=all_devs)

all_quarters = sorted(df["Purchase_Quarter_Label"].unique())
sel_quarters = st.sidebar.multiselect("Fiscal Quarter", all_quarters, default=all_quarters)

all_markets = sorted(df["Micro_Market"].unique())
sel_markets = st.sidebar.multiselect("Micro-Market", all_markets, default=all_markets)

all_configs = sorted(df["Configuration"].unique())
sel_configs = st.sidebar.multiselect("Configuration", all_configs, default=all_configs)

all_status = sorted(df["Booking_Status"].unique())
sel_status = st.sidebar.multiselect("Booking Status", all_status, default=all_status)

# Apply filters
mask = (
    df["Developer_Name"].isin(sel_devs) &
    df["Purchase_Quarter_Label"].isin(sel_quarters) &
    df["Micro_Market"].isin(sel_markets) &
    df["Configuration"].isin(sel_configs) &
    df["Booking_Status"].isin(sel_status)
)
dff = df[mask]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🏙️ Luxury Housing Sales Analysis — Bengaluru")
st.markdown("**Real Estate Analytics Pipeline · Python → SQLite → Streamlit**")
st.divider()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Records",    f"{len(dff):,}")
k2.metric("Total Revenue",    f"₹{dff['Ticket_Price_Cr'].sum():,.0f} Cr")
k3.metric("Avg Ticket Size",  f"₹{dff['Ticket_Price_Cr'].mean():.2f} Cr")
k4.metric("Booked Units",     f"{(dff['Booking_Status']=='Booked').sum():,}")
k5.metric("Avg Price/Sqft",   f"₹{dff['Price_per_Sqft'].mean():,.0f}")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Market & Trends",
    "🏗️ Builder & Pricing",
    "📡 Channels & Amenities",
    "💬 Buyer Insights"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Market & Trends
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        # VIZ 1: Quarterly booking trend by micro-market (Line Chart)
        st.markdown("#### Quarterly Booking Trends by Micro-Market")
        top_markets = dff["Micro_Market"].value_counts().head(6).index.tolist()
        qdf = (
            dff[dff["Micro_Market"].isin(top_markets)]
            .groupby(["Purchase_Quarter_Label", "Micro_Market"])
            .size().reset_index(name="Booking_Count")
        )
        fig1 = px.line(
            qdf, x="Purchase_Quarter_Label", y="Booking_Count",
            color="Micro_Market", markers=True,
            labels={"Purchase_Quarter_Label": "Quarter",
                    "Booking_Count": "Booking Count"},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig1.update_layout(height=360, xaxis_tickangle=-30,
                           legend_title="Micro-Market", margin=dict(t=10, b=10))
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # VIZ 5: Configuration demand (Donut Chart)
        st.markdown("#### Configuration Demand")
        cfg_df = dff["Configuration"].value_counts().reset_index()
        cfg_df.columns = ["Configuration", "Booking_Count"]
        fig5 = px.pie(
            cfg_df, names="Configuration", values="Booking_Count",
            hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig5.update_traces(textposition="outside", textinfo="percent+label")
        fig5.update_layout(showlegend=False, height=360, margin=dict(t=10, b=10))
        st.plotly_chart(fig5, use_container_width=True)

    # VIZ 4: Booking conversion by micro-market (Stacked Column)
    st.markdown("#### Booking Conversion Rate by Micro-Market")
    conv_df = (
        dff.groupby(["Micro_Market", "Booking_Status"])
        .size().reset_index(name="Count")
    )
    total_per_market = conv_df.groupby("Micro_Market")["Count"].transform("sum")
    conv_df["Pct"] = (conv_df["Count"] / total_per_market * 100).round(1)
    top10_markets = dff["Micro_Market"].value_counts().head(10).index
    conv_df = conv_df[conv_df["Micro_Market"].isin(top10_markets)]
    fig4 = px.bar(
        conv_df, x="Micro_Market", y="Pct", color="Booking_Status",
        barmode="stack",
        color_discrete_map={"Booked": "#1D9E75", "Not Booked": "#E8593C"},
        labels={"Pct": "Percentage (%)", "Micro_Market": "Micro-Market"},
        text=conv_df["Pct"].astype(str) + "%",
    )
    fig4.update_traces(textposition="inside")
    fig4.update_layout(height=380, margin=dict(t=10, b=10),
                       legend_title="Booking Status")
    st.plotly_chart(fig4, use_container_width=True)

    # VIZ 8: Possession status vs buyer type (Clustered Column)
    st.markdown("#### Possession Status vs Booking Status by Buyer Type")
    poss_df = (
        dff.groupby(["Possession_Status", "Buyer_Type", "Booking_Status"])
        .size().reset_index(name="Count")
    )
    fig8 = px.bar(
        poss_df, x="Possession_Status", y="Count",
        color="Buyer_Type", barmode="group",
        facet_col="Booking_Status",
        color_discrete_sequence=px.colors.qualitative.Set1,
        labels={"Count": "Units", "Possession_Status": "Possession Status"},
    )
    fig8.update_layout(height=400, margin=dict(t=30, b=10),
                       legend_title="Buyer Type")
    st.plotly_chart(fig8, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Builder & Pricing
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    col3, col4 = st.columns(2)

    with col3:
        # VIZ 2: Builder performance — total + avg ticket (Bar)
        st.markdown("#### Developer Performance — Revenue & Avg Ticket")
        dev_df = (
            dff.groupby("Developer_Name")
            .agg(Total_Revenue=("Ticket_Price_Cr", "sum"),
                 Avg_Ticket=("Ticket_Price_Cr", "mean"),
                 Units=("Property_ID", "count"))
            .reset_index()
            .sort_values("Total_Revenue", ascending=False)
            .head(10)
        )
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            y=dev_df["Developer_Name"], x=dev_df["Total_Revenue"],
            name="Total Revenue (Cr)", orientation="h",
            marker_color="#1B5C8A",
        ))
        fig2.add_trace(go.Scatter(
            y=dev_df["Developer_Name"],
            x=dev_df["Avg_Ticket"] * 500,
            name="Avg Ticket (Cr) ×500",
            mode="markers",
            marker=dict(color="#E8593C", size=10, symbol="diamond"),
        ))
        fig2.update_layout(
            height=400, margin=dict(t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis_title="Revenue (Cr)",
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col4:
        # VIZ 7: Quarterly builder contribution (Heatmap / Matrix)
        st.markdown("#### Quarterly Builder Revenue Matrix")
        matrix_df = (
            dff.groupby(["Developer_Name", "Purchase_Quarter_Label"])
            ["Ticket_Price_Cr"].sum().round(1).reset_index()
        )
        pivot = matrix_df.pivot(
            index="Developer_Name",
            columns="Purchase_Quarter_Label",
            values="Ticket_Price_Cr"
        ).fillna(0)
        top_devs = dff.groupby("Developer_Name")["Ticket_Price_Cr"]\
            .sum().nlargest(8).index
        pivot = pivot.loc[pivot.index.isin(top_devs)]
        fig7 = px.imshow(
            pivot, aspect="auto",
            color_continuous_scale="Blues",
            labels=dict(x="Quarter", y="Developer", color="Revenue (Cr)"),
        )
        fig7.update_layout(height=400, margin=dict(t=10, b=10))
        st.plotly_chart(fig7, use_container_width=True)

    # VIZ 10: Top performers table
    st.markdown("#### Top 5 Developers — Revenue & Booking Success")
    top5 = (
        dff.groupby("Developer_Name")
        .agg(Revenue=("Ticket_Price_Cr", "sum"),
             Units=("Property_ID", "count"),
             Booked=("Booking_Flag", "sum"))
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .head(5)
    )
    top5["Booking_Rate_%"] = (top5["Booked"] / top5["Units"] * 100).round(1)
    top5["Revenue (Cr)"] = top5["Revenue"].round(1)
    st.dataframe(
        top5[["Developer_Name", "Units", "Revenue (Cr)", "Booked", "Booking_Rate_%"]]
        .rename(columns={"Developer_Name": "Developer"}),
        use_container_width=True, hide_index=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Channels & Amenities
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    col5, col6 = st.columns(2)

    with col5:
        # VIZ 6: Sales channel efficiency (100% Stacked)
        st.markdown("#### Sales Channel Efficiency (100% Stacked)")
        ch_df = (
            dff.groupby(["Sales_Channel", "Booking_Status"])
            .size().reset_index(name="Count")
        )
        total_ch = ch_df.groupby("Sales_Channel")["Count"].transform("sum")
        ch_df["Pct"] = (ch_df["Count"] / total_ch * 100).round(1)
        fig6 = px.bar(
            ch_df, x="Sales_Channel", y="Pct", color="Booking_Status",
            barmode="stack",
            color_discrete_map={"Booked": "#1D9E75", "Not Booked": "#E8593C"},
            labels={"Pct": "Percentage (%)", "Sales_Channel": "Sales Channel"},
            text=ch_df["Pct"].astype(str) + "%",
        )
        fig6.update_traces(textposition="inside")
        fig6.update_layout(height=380, margin=dict(t=10, b=10),
                           yaxis_title="Percentage (%)")
        st.plotly_chart(fig6, use_container_width=True)

    with col6:
        # VIZ 3: Amenity score vs booking conversion (Scatter/Bubble)
        st.markdown("#### Amenity Score vs Booking Conversion Rate")
        am_df = (
            dff.groupby(["Micro_Market", "Amenity_Band"])
            .agg(Avg_Amenity=("Amenity_Score", "mean"),
                 Booking_Rate=("Booking_Flag", "mean"),
                 Project_Count=("Property_ID", "count"))
            .reset_index()
        )
        am_df["Booking_Conversion_Rate"] = (am_df["Booking_Rate"] * 100).round(1)
        fig3 = px.scatter(
            am_df, x="Avg_Amenity", y="Booking_Conversion_Rate",
            size="Project_Count", color="Amenity_Band",
            hover_name="Micro_Market",
            labels={"Avg_Amenity": "Avg Amenity Score",
                    "Booking_Conversion_Rate": "Booking Conversion Rate (%)"},
            color_discrete_sequence=["#B4B2A9", "#1B5C8A", "#1D9E75", "#D85A30"],
        )
        fig3.update_layout(height=380, margin=dict(t=10, b=10))
        st.plotly_chart(fig3, use_container_width=True)

    # NRI buyer share
    st.markdown("#### 🌍 NRI Buyer Share by Micro-Market (Top 10)")
    nri_df = (
        dff.groupby("Micro_Market")
        .agg(NRI=("NRI_Flag", "sum"), Total=("Property_ID", "count"))
        .reset_index()
    )
    nri_df["NRI_Pct"] = (nri_df["NRI"] / nri_df["Total"] * 100).round(1)
    nri_df = nri_df.sort_values("NRI_Pct", ascending=False).head(10)
    fig_nri = px.bar(
        nri_df, x="NRI_Pct", y="Micro_Market", orientation="h",
        color="NRI_Pct", color_continuous_scale="teal",
        labels={"NRI_Pct": "NRI Buyer %", "Micro_Market": ""},
        text=nri_df["NRI_Pct"].astype(str) + "%",
    )
    fig_nri.update_traces(textposition="outside")
    fig_nri.update_layout(height=360, coloraxis_showscale=False,
                          margin=dict(t=10, b=10))
    st.plotly_chart(fig_nri, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Buyer Insights (Comments & Sentiment)
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("#### 💬 Buyer Comment Sentiment Analysis")
    st.markdown(
        "Sentiment derived from `Buyer_Comments` using keyword-based classification "
        "(Positive / Negative / Neutral). Used to build buyer personas."
    )

    col7, col8 = st.columns(2)

    with col7:
        # Sentiment distribution
        sent_df = dff["Comment_Sentiment"].value_counts().reset_index()
        sent_df.columns = ["Sentiment", "Count"]
        fig_sent = px.pie(
            sent_df, names="Sentiment", values="Count", hole=0.45,
            color="Sentiment",
            color_discrete_map={
                "Positive": "#1D9E75",
                "Negative": "#E8593C",
                "Neutral":  "#B4B2A9",
            },
        )
        fig_sent.update_traces(textinfo="percent+label", textposition="outside")
        fig_sent.update_layout(showlegend=False, height=360,
                                margin=dict(t=10, b=10))
        st.plotly_chart(fig_sent, use_container_width=True)

    with col8:
        # Sentiment by buyer type (persona building)
        persona_df = (
            dff.groupby(["Buyer_Type", "Comment_Sentiment"])
            .size().reset_index(name="Count")
        )
        fig_persona = px.bar(
            persona_df, x="Buyer_Type", y="Count",
            color="Comment_Sentiment", barmode="group",
            color_discrete_map={
                "Positive": "#1D9E75",
                "Negative": "#E8593C",
                "Neutral":  "#B4B2A9",
            },
            labels={"Count": "Number of Buyers", "Buyer_Type": "Buyer Type"},
        )
        fig_persona.update_layout(height=360, margin=dict(t=10, b=10),
                                   legend_title="Sentiment")
        st.plotly_chart(fig_persona, use_container_width=True)

    # Sentiment vs booking status
    st.markdown("#### Sentiment vs Booking Status")
    sent_book = (
        dff.groupby(["Comment_Sentiment", "Booking_Status"])
        .size().reset_index(name="Count")
    )
    total_sent = sent_book.groupby("Comment_Sentiment")["Count"].transform("sum")
    sent_book["Pct"] = (sent_book["Count"] / total_sent * 100).round(1)
    fig_sb = px.bar(
        sent_book, x="Comment_Sentiment", y="Pct",
        color="Booking_Status", barmode="stack",
        color_discrete_map={"Booked": "#1D9E75", "Not Booked": "#E8593C"},
        labels={"Pct": "Percentage (%)", "Comment_Sentiment": "Sentiment"},
        text=sent_book["Pct"].astype(str) + "%",
    )
    fig_sb.update_traces(textposition="inside")
    fig_sb.update_layout(height=360, margin=dict(t=10, b=10))
    st.plotly_chart(fig_sb, use_container_width=True)

    # Top comment themes
    st.markdown("#### Top Buyer Comment Themes")
    comment_counts = (
        dff[dff["Buyer_Comments"] != ""]["Buyer_Comments"]
        .value_counts()
        .head(10)
        .reset_index()
    )
    comment_counts.columns = ["Comment", "Frequency"]
    st.dataframe(comment_counts, use_container_width=True, hide_index=True)

# ── Raw data explorer ─────────────────────────────────────────────────────────
st.divider()
with st.expander("🔎 Explore Raw Data"):
    st.dataframe(dff.head(500), use_container_width=True)
    st.caption(f"Showing 500 of {len(dff):,} filtered rows")

st.markdown(
    "<div style='text-align:center;color:gray;font-size:12px;margin-top:20px'>"
    "Luxury Housing Sales Analysis · Bengaluru · "
    "Built with Python + SQLAlchemy + SQLite + Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
