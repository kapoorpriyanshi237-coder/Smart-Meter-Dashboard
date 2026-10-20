
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Smart Meter Analytics",
    page_icon="⚡",
    layout="wide"
)

# -------------------- CUSTOM DESIGN --------------------

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1450px;
    }

    .hero {
        padding: 1.5rem;
        border-radius: 16px;
        background: linear-gradient(120deg, #102a43, #176b87);
        color: white;
        margin-bottom: 1.2rem;
    }

    .hero h1 {
        color: white;
        margin-bottom: 0.4rem;
    }

    .hero p {
        color: #e6f4f7;
        font-size: 1rem;
        margin-bottom: 0;
    }

    div[data-testid="stMetric"] {
        background: var(--secondary-background-color);
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }

    div[data-testid="stMetricLabel"] {
        font-weight: 600;
    }

    h2, h3 {
        padding-top: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>⚡ Smart Meter Data Dashboard</h1>
    <p>
        Understand electricity consumption, compare households,
        monitor estimated peak demand and identify unusually
        high-usage days using real-world smart meter data.
    </p>
</div>
""", unsafe_allow_html=True)

st.caption("Consumer Energy Analytics | Real-world London smart meter dataset")
st.divider()

# -------------------- SIDEBAR --------------------

st.sidebar.title("⚙️ Dashboard Settings")
st.sidebar.write("Configure your analysis below.")

tariff = st.sidebar.number_input(
    "Illustrative electricity rate (₹/kWh)",
    min_value=0.0,
    value=8.0,
    step=0.5,
    help="This is an example rate, not the actual London electricity tariff."
)

st.sidebar.info(
    "Upload a compatible London Smart Meter CSV file to explore the data."
)

# -------------------- FILE UPLOAD --------------------

uploaded_file = st.file_uploader(
    "📂 Upload Smart Meter CSV",
    type=["csv"],
    help="Expected columns: LCLid, DateTime, KWH/hh (per half hour)"
)

if uploaded_file is None:
    st.info("👆 Upload your LCL-June2015v2 CSV file to get started.")

    st.markdown("### What this dashboard provides")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 🏠 Household Comparison")
        st.write("Compare daily electricity consumption across households.")

    with col2:
        st.markdown("#### 📊 Energy Analytics")
        st.write("Review consumption, estimated peak demand and illustrative cost.")

    with col3:
        st.markdown("#### 🚨 High-Usage Alerts")
        st.write("Identify days with unusually high energy consumption.")

    st.stop()

# -------------------- LOAD AND VALIDATE DATA --------------------

try:
    data = pd.read_csv(uploaded_file)
    data.columns = data.columns.str.strip()

    required = [
        "LCLid",
        "DateTime",
        "KWH/hh (per half hour)"
    ]

    missing_columns = [
        column for column in required
        if column not in data.columns
    ]

    if missing_columns:
        st.error(
            "This CSV is missing required columns: "
            + ", ".join(missing_columns)
        )
        st.write("Columns found:", data.columns.tolist())
        st.stop()

    original_rows = len(data)

    data["LCLid"] = data["LCLid"].astype("string").str.strip()
    data["DateTime"] = pd.to_datetime(
        data["DateTime"],
        errors="coerce"
    )
    data["KWH/hh (per half hour)"] = pd.to_numeric(
        data["KWH/hh (per half hour)"],
        errors="coerce"
    )

    data = data.dropna(subset=required)

    data = data[
        (data["LCLid"] != "")
        & (data["KWH/hh (per half hour)"] >= 0)
    ].copy()

    if data.empty:
        st.error("No valid, non-negative energy readings were found.")
        st.stop()

    data["Date"] = data["DateTime"].dt.date

    households = sorted(data["LCLid"].unique().tolist())

    st.success(f"Successfully loaded {len(data):,} valid readings.")

    if len(data) < original_rows:
        st.caption(
            f"{original_rows - len(data):,} invalid or incomplete rows "
            "were excluded from the analysis."
        )

    # -------------------- HOUSEHOLD AND DATE FILTERS --------------------

    st.sidebar.divider()
    st.sidebar.subheader("🏠 Household Selection")

    household = st.sidebar.selectbox(
        "Select household for detailed analysis",
        options=households
    )

    household_data = data[data["LCLid"] == household].copy()

    min_date = household_data["Date"].min()
    max_date = household_data["Date"].max()

    st.sidebar.subheader("📅 Date Range")

    start_date = st.sidebar.date_input(
        "Start date",
        value=min_date,
        min_value=min_date,
        max_value=max_date,
        key="start_date"
    )

    end_date = st.sidebar.date_input(
        "End date",
        value=max_date,
        min_value=min_date,
        max_value=max_date,
        key="end_date"
    )

    if start_date > end_date:
        st.error("Start date must be before or equal to the end date.")
        st.stop()

    household_data = household_data[
        (household_data["Date"] >= start_date)
        & (household_data["Date"] <= end_date)
    ].copy()

    if household_data.empty:
        st.warning("No readings were found for this date range.")
        st.stop()

    # -------------------- DAILY CALCULATIONS --------------------

    interval_column = "KWH/hh (per half hour)"

    household_data["Estimated Interval Power (kW)"] = (
        household_data[interval_column] / 0.5
    )

    daily = household_data.groupby(
        "Date",
        as_index=False
    ).agg(
        **{
            "Consumption (kWh)": (interval_column, "sum"),
            "Estimated Peak Demand (kW)": (
                "Estimated Interval Power (kW)",
                "max"
            )
        }
    )

    # -------------------- HOUSEHOLD COMPARISON --------------------

    st.subheader("🏠 Household Comparison")
    st.write(
        "Select one or more households to compare their daily "
        "electricity consumption over the selected date range."
    )

    comparison_households = st.multiselect(
        "Households to compare",
        options=households,
        default=[household],
        key="comparison_households"
    )

    if comparison_households:
        comparison_data = data[
            data["LCLid"].isin(comparison_households)
            & (data["Date"] >= start_date)
            & (data["Date"] <= end_date)
        ].copy()

        if comparison_data.empty:
            st.info("No comparison readings exist for this date range.")
        else:
            comparison_daily = comparison_data.groupby(
                ["Date", "LCLid"],
                as_index=False
            )[interval_column].sum()

            comparison_daily = comparison_daily.rename(
                columns={
                    interval_column: "Daily Consumption (kWh)"
                }
            )

            fig_comparison = px.line(
                comparison_daily,
                x="Date",
                y="Daily Consumption (kWh)",
                color="LCLid",
                markers=True,
                title="Daily Energy Consumption by Household",
                labels={
                    "Date": "Date",
                    "Daily Consumption (kWh)": "Energy (kWh)",
                    "LCLid": "Household"
                },
                template="plotly_white"
            )

            fig_comparison.update_layout(
                legend_title="Household ID",
                hovermode="x unified"
            )

            st.plotly_chart(
                fig_comparison,
                use_container_width=True,
                key="household_comparison_chart"
            )
    else:
        st.info("Select at least one household to view the comparison.")

    st.divider()

    # -------------------- ENERGY SUMMARY --------------------

    st.subheader("📊 Energy Summary")

    total_energy = daily["Consumption (kWh)"].sum()
    peak_demand = daily["Estimated Peak Demand (kW)"].max()
    estimated_cost = total_energy * tariff
    average_daily = daily["Consumption (kWh)"].mean()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Consumption",
        f"{total_energy:,.2f} kWh"
    )

    col2.metric(
        "Estimated Peak Demand",
        f"{peak_demand:,.2f} kW"
    )

    col3.metric(
        "Illustrative Cost",
        f"₹{estimated_cost:,.2f}"
    )

    col4.metric(
        "Average Daily Usage",
        f"{average_daily:,.2f} kWh"
    )

    st.caption(
        "Cost is an illustrative estimate using your selected rate. "
        "It is not the actual tariff paid by the London households."
    )

    st.divider()

    # -------------------- HIGH-USAGE DETECTION --------------------

    average = daily["Consumption (kWh)"].mean()
    std_dev = daily["Consumption (kWh)"].std(ddof=0)
    threshold = average + std_dev

    daily["Usage Status"] = daily["Consumption (kWh)"].apply(
        lambda value: (
            "Unusually High" if value > threshold else "Normal"
        )
    )

    # -------------------- DAILY CONSUMPTION CHART --------------------

    st.subheader("📈 Daily Electricity Consumption")
    st.write(
        "View daily energy consumption and the days flagged by "
        "the statistical high-usage rule."
    )

    fig1 = px.scatter(
        daily,
        x="Date",
        y="Consumption (kWh)",
        color="Usage Status",
        color_discrete_map={
            "Normal": "#2878B5",
            "Unusually High": "#E53935"
        },
        hover_data=["Usage Status"],
        title="Daily Consumption and High-Usage Alerts",
        template="plotly_white"
    )

    fig1.add_scatter(
        x=daily["Date"],
        y=daily["Consumption (kWh)"],
        mode="lines",
        name="Consumption Trend",
        line=dict(color="#607D8B", width=2),
        showlegend=True
    )

    fig1.update_layout(
        xaxis_title="Date",
        yaxis_title="Energy Consumption (kWh)",
        hovermode="x unified"
    )

    st.plotly_chart(
        fig1,
        use_container_width=True,
        key="daily_consumption_chart"
    )

    # -------------------- PEAK DEMAND CHART --------------------

    st.subheader("⚡ Estimated Peak Demand")

    fig2 = px.bar(
        daily,
        x="Date",
        y="Estimated Peak Demand (kW)",
        title="Highest Estimated Interval Power per Day",
        template="plotly_white",
        color_discrete_sequence=["#176B87"]
    )

    fig2.update_layout(
        xaxis_title="Date",
        yaxis_title="Estimated Power (kW)",
        hovermode="x unified"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True,
        key="peak_demand_chart"
    )

    st.caption(
        "Estimated interval power is calculated as interval energy "
        "divided by 0.5 hours. It is an estimate based on the "
        "half-hourly readings, not a direct instantaneous measurement."
    )

    st.divider()

    # -------------------- HIGH-USAGE ALERTS --------------------

    st.subheader("🚨 Unusually High Consumption")

    st.write(f"Average daily consumption: **{average:.2f} kWh**")
    st.write(f"High-usage threshold: **{threshold:.2f} kWh**")

    abnormal = daily[
        daily["Consumption (kWh)"] > threshold
    ].copy()

    if abnormal.empty:
        st.success("No days crossed the high-usage threshold.")
    else:
        st.warning(
            f"{len(abnormal)} day(s) crossed the high-usage threshold."
        )
        st.dataframe(
            abnormal,
            use_container_width=True,
            hide_index=True
        )

    st.caption(
        "These alerts indicate unusually high usage relative to the "
        "selected period. They do not prove an electrical fault."
    )

    st.divider()

    # -------------------- DAILY DATA TABLE --------------------

    st.subheader("📋 Daily Energy Data")

    st.dataframe(
        daily,
        use_container_width=True,
        hide_index=True
    )

    # -------------------- DOWNLOAD REPORT --------------------

    report = daily.copy()
    report["Illustrative Cost (₹)"] = (
        report["Consumption (kWh)"] * tariff
    )

    report_csv = report.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="⬇️ Download Energy Report (CSV)",
        data=report_csv,
        file_name="smart_meter_energy_report.csv",
        mime="text/csv",
        key="download_energy_report"
    )

    # -------------------- DATASET INFORMATION --------------------

    st.divider()
    st.subheader("📚 Dataset Information")

    st.markdown(
        """
        **Dataset:** London Smart Meter Energy Consumption

        **Reading interval:** Every 30 minutes

        **Important fields:**
        - `LCLid`: Household identifier
        - `DateTime`: Date and time of the reading
        - `KWH/hh (per half hour)`: Energy consumed during a half-hour interval

        **Source:** [London Datastore — SmartMeter Energy Consumption
        Data in London Households](https://data.london.gov.uk/dataset/
        smartmeter-energy-consumption-data-in-london-households-vqm0d)
        """
    )

    st.caption(
        "The dashboard analyses the uploaded file only. "
        "High-usage flags use the selected household's daily average "
        "plus one standard deviation. The illustrative ₹/kWh rate "
        "does not represent the actual London electricity tariff."
    )

except Exception as error:
    st.error(f"Could not process the CSV: {error}")
    st.info(
        "Check that the uploaded file is a valid CSV with the required "
        "columns and supported date values."
    )
