
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Smart Meter Analytics",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Smart Meter Data Dashboard")
st.write(
    "Real-World Household Energy Consumption Analytics"
)

st.sidebar.header("Dashboard Settings")

tariff = st.sidebar.number_input(
    "Illustrative electricity rate (₹/kWh)",
    min_value=0.0,
    value=8.0,
    step=0.5
)

uploaded_file = st.file_uploader(
    "Upload a London Smart Meter CSV file",
    type=["csv"]
)

if uploaded_file is None:
    st.info("Upload an LCL-June2015v2 CSV file to begin.")
    st.stop()

try:
    data = pd.read_csv(uploaded_file)
    data.columns = data.columns.str.strip()

    required = [
        "LCLid",
        "DateTime",
        "KWH/hh (per half hour)"
    ]

    if not all(column in data.columns for column in required):
        st.error("The CSV does not contain the expected columns.")
        st.write("Columns found:", data.columns.tolist())
        st.stop()

    data["DateTime"] = pd.to_datetime(
        data["DateTime"],
        errors="coerce"
    )

    data["KWH/hh (per half hour)"] = pd.to_numeric(
        data["KWH/hh (per half hour)"],
        errors="coerce"
    )

    data = data.dropna(
        subset=[
            "LCLid",
            "DateTime",
            "KWH/hh (per half hour)"
        ]
    )

    data = data[data["KWH/hh (per half hour)"] >= 0].copy()

    if data.empty:
        st.error("No valid readings were found in this file.")
        st.stop()

    data["Date"] = data["DateTime"].dt.date

    st.success(f"Loaded {len(data):,} valid readings.")

    households = sorted(data["LCLid"].unique())

    household = st.sidebar.selectbox(
        "Select household",
        households
    )

    household_data = data[
        data["LCLid"] == household
    ].copy()

    min_date = household_data["Date"].min()
    max_date = household_data["Date"].max()

    st.sidebar.subheader("📅 Date Range Filter")

    start_date = st.sidebar.date_input(
        "Start date",
        value=min_date,
        min_value=min_date,
        max_value=max_date
    )

    end_date = st.sidebar.date_input(
        "End date",
        value=max_date,
        min_value=min_date,
        max_value=max_date
    )

    if start_date > end_date:
        st.error("Start date must be before or equal to end date.")
        st.stop()

    household_data = household_data[
        (household_data["Date"] >= start_date)
        & (household_data["Date"] <= end_date)
    ].copy()

    if household_data.empty:
        st.warning("No readings found for the selected dates.")
        st.stop()

    # Calculate daily energy and estimated interval power.
    household_data["Estimated Interval Power (kW)"] = (
        household_data["KWH/hh (per half hour)"] / 0.5
    )

    daily = household_data.groupby(
        "Date",
        as_index=False
    ).agg(
        **{
            "Consumption (kWh)": (
                "KWH/hh (per half hour)",
                "sum"
            ),
            "Estimated Peak Demand (kW)": (
                "Estimated Interval Power (kW)",
                "max"
            )
        }
    )

    # Household comparison uses the same selected date range.
    st.subheader("🏠 Household Comparison")

    comparison_households = st.multiselect(
        "Select households to compare",
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

        comparison_daily = comparison_data.groupby(
            ["Date", "LCLid"],
            as_index=False
        )["KWH/hh (per half hour)"].sum()

        comparison_daily = comparison_daily.rename(
            columns={
                "KWH/hh (per half hour)": "Daily Consumption (kWh)"
            }
        )

        fig_comparison = px.line(
            comparison_daily,
            x="Date",
            y="Daily Consumption (kWh)",
            color="LCLid",
            title="Daily Energy Consumption by Household"
        )

        fig_comparison.update_layout(
            xaxis_title="Date",
            yaxis_title="Consumption (kWh)",
            legend_title="Household ID"
        )

        st.plotly_chart(
            fig_comparison,
            use_container_width=True,
            key="household_comparison_chart"
        )
    else:
        st.info("Select at least one household to see the comparison.")

    # Summary metrics.
    total_energy = daily["Consumption (kWh)"].sum()
    peak_demand = daily["Estimated Peak Demand (kW)"].max()
    estimated_cost = total_energy * tariff

    st.subheader("📊 Energy Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Consumption",
        f"{total_energy:,.2f} kWh"
    )

    col2.metric(
        "Estimated Peak Demand",
        f"{peak_demand:.2f} kW"
    )

    col3.metric(
        "Illustrative Cost",
        f"₹{estimated_cost:,.2f}"
    )

    st.caption(
        "The dataset is from London. The ₹/kWh rate is illustrative, "
        "not the actual tariff paid by these households."
    )

    # Flag unusually high daily consumption.
    average = daily["Consumption (kWh)"].mean()
    std_dev = daily["Consumption (kWh)"].std(ddof=0)
    threshold = average + std_dev

    daily["Usage Status"] = daily["Consumption (kWh)"].apply(
        lambda value: (
            "Unusually High" if value > threshold else "Normal"
        )
    )

    st.subheader("📈 Daily Electricity Consumption")

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
        title="Daily Consumption with High-Usage Alerts"
    )

    fig1.add_scatter(
        x=daily["Date"],
        y=daily["Consumption (kWh)"],
        mode="lines",
        name="Consumption Trend",
        line=dict(color="gray", width=1),
        showlegend=True
    )

    fig1.update_layout(
        xaxis_title="Date",
        yaxis_title="Consumption (kWh)"
    )

    st.plotly_chart(
        fig1,
        use_container_width=True,
        key="daily_consumption_chart"
    )

    st.subheader("⚡ Estimated Peak Demand")

    fig2 = px.bar(
        daily,
        x="Date",
        y="Estimated Peak Demand (kW)",
        title="Highest Estimated Interval Power per Day"
    )

    fig2.update_layout(
        xaxis_title="Date",
        yaxis_title="Estimated Power (kW)"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True,
        key="peak_demand_chart"
    )

    st.subheader("⚠️ Unusually High Consumption")

    st.write(f"Average daily consumption: {average:.2f} kWh")
    st.write(f"High-usage threshold: {threshold:.2f} kWh")

    abnormal = daily[
        daily["Consumption (kWh)"] > threshold
    ]

    if abnormal.empty:
        st.success("No unusually high daily readings were flagged.")
    else:
        st.warning(
            f"{len(abnormal)} unusually high day(s) detected."
        )
        st.dataframe(
            abnormal,
            use_container_width=True
        )

    st.subheader("📋 Daily Data")
    st.dataframe(daily, use_container_width=True)

    report = daily.copy()
    report["Illustrative Cost (₹)"] = (
        report["Consumption (kWh)"] * tariff
    )

    st.download_button(
        label="⬇️ Download Energy Report (CSV)",
        data=report.to_csv(index=False).encode("utf-8"),
        file_name="smart_meter_energy_report.csv",
        mime="text/csv",
        key="download_energy_report"
    )

    st.divider()

    st.subheader("📚 Dataset Information")

    st.write(
        "Source: London Smart Meter Energy Consumption dataset. "
        "The uploaded file contains household electricity readings "
        "recorded at half-hour intervals."
    )

    st.caption(
        "High-usage flags are statistical indicators, not proof of an "
        "electrical fault. Estimated interval power is calculated by "
        "dividing interval energy by 0.5 hours."
    )

except Exception as error:
    st.error(f"Could not process the CSV: {error}")
