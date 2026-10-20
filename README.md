# Smart Meter Data Dashboard for Consumer Energy Analytics

## Project Overview
This project is a Python-based dashboard that helps users analyse smart meter electricity consumption data. It displays daily energy consumption, estimated peak demand, illustrative electricity cost, and unusual usage patterns.

## Features
- Upload smart meter data through a CSV file.
- Select a household and filter data by date.
- Compare electricity consumption across households.
- View total consumption, estimated peak demand, estimated cost, and average daily usage.
- Visualise daily consumption and peak demand using interactive graphs.
- Identify unusually high usage using a statistical threshold.
- Download the daily analysis report as a CSV file.

## Technologies Used
- Python
- Streamlit
- Pandas
- Plotly

## Dataset
The project uses smart meter energy consumption data from the London Datastore.

Dataset source: https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d

## How to Run the Project
1. Install Python.
2. Install the required libraries using `pip install -r requirements.txt`.
3. Run the application using `python -m streamlit run app.py`.
4. Open the local URL displayed in the terminal.

## Notes
- The electricity rate is an illustrative value and should be adjusted for the applicable tariff.
- Peak demand is estimated from half-hourly energy readings.
- High-usage alerts indicate unusual consumption relative to the selected data; they do not confirm a meter fault.

## Future Improvements
- Deploy the dashboard online.
- Add more energy analytics and visualisations.
- Improve abnormal usage detection.
