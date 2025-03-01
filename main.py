import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Set page config for better embedding
st.set_page_config(
    page_title="Local Market Analysis",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to make it more Notion-friendly
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("Local Market Analysis")

# Load data
@st.cache_data
def load_data():
    # This would normally read from a CSV file, but for this example we'll input the data manually
    data = pd.read_csv("data.csv")

    # Clean and process the data
    # Convert contract date to datetime
    data['Contract Date'] = pd.to_datetime(data['Contract Date'], dayfirst=True)

    # Convert contract amount to numeric
    data['Contract Amount'] = data['Contract Amount'].str.replace(',', '').astype(float)

    # Replace missing values in areas with 0
    for col in ['Covered Area', 'Covered Veranda', 'Total Covered']:
        data[col] = data[col].fillna(0)

    # Add a Year-Month column for timeline analysis
    data['Year-Month'] = data['Contract Date'].dt.strftime('%Y-%m')

    return data


data = load_data()

# Add a sidebar with filters
with st.sidebar:
    st.header("Filters")

    # Date range filter
    min_date = data['Contract Date'].min().date()
    max_date = data['Contract Date'].max().date()

    start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
    end_date = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

    # Project filter
    projects = ["All"] + sorted(data["Project"].unique().tolist())
    selected_project = st.selectbox("Select Project", projects)

    # Bedroom filter
    bedrooms = ["All"] + sorted(data["Bedrooms"].dropna().unique().tolist())
    selected_bedrooms = st.selectbox("Select Bedrooms", bedrooms)

    # Price range filter
    min_price = int(data["Contract Amount"].min())
    max_price = int(data["Contract Amount"].max())
    price_range = st.slider(
        "Price Range (€)",
        min_price,
        max_price,
        (min_price, max_price)
    )

# Apply filters
filter_conditions = (
        (data["Contract Date"].dt.date >= start_date) &
        (data["Contract Date"].dt.date <= end_date) &
        (data["Contract Amount"] >= price_range[0]) &
        (data["Contract Amount"] <= price_range[1])
)

if selected_project != "All":
    filter_conditions &= (data["Project"] == selected_project)

if selected_bedrooms != "All":
    filter_conditions &= (data["Bedrooms"] == selected_bedrooms)

filtered_data = data[filter_conditions]

# Create tabs for different dashboard sections
tab1, tab2, tab3 = st.tabs(["Sales Timeline", "Project Analysis", "Location Map"])

with tab1:
    st.header("Sales Timeline")

    # Show message if no data after filtering
    if filtered_data.empty:
        st.warning("No data available for the selected filters. Please adjust your filter criteria.")
    else:
        # Aggregate sales by month for timeline
        monthly_sales = filtered_data.groupby('Year-Month').agg(
            {'Contract Amount': 'sum', 'Unit ID': 'count'}
        ).reset_index()
        monthly_sales = monthly_sales.sort_values('Year-Month')

        # Create timeline chart
        fig = px.bar(
            monthly_sales,
            x='Year-Month',
            y='Contract Amount',
            title='Monthly Sales Volume',
            labels={'Year-Month': 'Month', 'Contract Amount': 'Total Sales (€)'},
            text_auto='.2s'
        )
        fig.update_layout(xaxis_tickangle=-45, height=500)
        st.plotly_chart(fig, use_container_width=True)

        # Line chart for number of units sold
        fig2 = px.line(
            monthly_sales,
            x='Year-Month',
            y='Unit ID',
            title='Number of Units Sold Monthly',
            labels={'Year-Month': 'Month', 'Unit ID': 'Units Sold'},
            markers=True
        )
        fig2.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.header("Project Analysis")

    # Show message if no data after filtering
    if filtered_data.empty:
        st.warning("No data available for the selected filters. Please adjust your filter criteria.")
    else:
        # Sales by project
        project_sales = filtered_data.groupby('Project').agg(
            {'Contract Amount': ['sum', 'mean', 'count'], 'Total Covered': 'mean'}
        ).reset_index()
        project_sales.columns = ['Project', 'Total Sales', 'Average Price', 'Units Sold', 'Average Size']
        project_sales['Price per m²'] = project_sales['Average Price'] / project_sales['Average Size'].replace(0,
                                                                                                               np.nan)

        # Sort projects by total sales
        project_sales = project_sales.sort_values('Total Sales', ascending=False)

        # Create horizontal bar chart for total sales by project
        fig3 = px.bar(
            project_sales,
            y='Project',
            x='Total Sales',
            title='Total Sales by Project',
            labels={'Total Sales': 'Total Sales (€)', 'Project': ''},
            text_auto='.2s',
            orientation='h'
        )
        fig3.update_layout(height=600)
        st.plotly_chart(fig3, use_container_width=True)

        # Two columns for price metrics
        col1, col2 = st.columns(2)

        with col1:
            # Average price by project
            fig4 = px.bar(
                project_sales,
                y='Project',
                x='Average Price',
                title='Average Unit Price by Project',
                labels={'Average Price': 'Average Price (€)', 'Project': ''},
                text_auto='.2s',
                orientation='h'
            )
            fig4.update_layout(height=500)
            st.plotly_chart(fig4, use_container_width=True)

        with col2:
            # Price per m² by project
            fig5 = px.bar(
                project_sales,
                y='Project',
                x='Price per m²',
                title='Average Price per m² by Project',
                labels={'Price per m²': 'Price per m² (€)', 'Project': ''},
                text_auto='.2s',
                orientation='h'
            )
            fig5.update_layout(height=500)
            st.plotly_chart(fig5, use_container_width=True)

        # Bedroom analysis
        st.subheader("Sales by Number of Bedrooms")

        # Filter out any rows with non-numeric bedroom values
        bedroom_data = filtered_data[pd.to_numeric(filtered_data['Bedrooms'], errors='coerce').notna()]

        if not bedroom_data.empty:
            # Sales by bedroom count
            bedroom_sales = bedroom_data.groupby('Bedrooms').agg(
                {'Contract Amount': ['sum', 'mean', 'count'], 'Total Covered': 'mean'}
            ).reset_index()
            bedroom_sales.columns = ['Bedrooms', 'Total Sales', 'Average Price', 'Units Sold', 'Average Size']
            bedroom_sales['Price per m²'] = bedroom_sales['Average Price'] / bedroom_sales['Average Size'].replace(0,
                                                                                                                   np.nan)

            # Create pie chart for bedroom distribution
            fig6 = px.pie(
                bedroom_sales,
                values='Units Sold',
                names='Bedrooms',
                title='Units Sold by Bedroom Count',
                hole=0.4
            )
            fig6.update_traces(textinfo='percent+label')

            # Bar chart for average price by bedroom
            fig7 = px.bar(
                bedroom_sales,
                x='Bedrooms',
                y='Average Price',
                title='Average Price by Bedroom Count',
                text_auto='.2s'
            )

            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig6, use_container_width=True)
            with col2:
                st.plotly_chart(fig7, use_container_width=True)
        else:
            st.info("No bedroom data available for the selected filters.")

with tab3:
    st.header("Sales Concentration by Project")

    # Show message if no data after filtering
    if filtered_data.empty:
        st.warning("No data available for the selected filters. Please adjust your filter criteria.")
    else:
        # Create a map with sales data points
        # Filter out rows with missing lat/long
        map_data = filtered_data.dropna(subset=['Latitude', 'Longitude'])

        if not map_data.empty:
            # Use a custom color scale based on contract amount
            map_data['size'] = np.sqrt(map_data['Contract Amount']) / 100  # Scale the point size

            # Custom location for analyzed plot
            custom_latitude = 34.707233  # Replace with your location's latitude
            custom_longitude = 33.053359  # Replace with your location's longitude

            # Add a new row to project_locations to represent your plot
            custom_plot = pd.DataFrame({
                'Project': ['Agios Athanasios 419'],
                'Latitude': [custom_latitude],
                'Longitude': [custom_longitude],
                'Total Sales': [0],  # No sales (specific to the plot)
                'Units Sold': [0],  # No units
                'Price per m²': [None],  # Non-applicable
                'size': [10]  # Fixed marker size for visibility or adjust as needed
            })

            # Group by project and get average coordinates and total sales
            project_locations = map_data.groupby('Project').agg({
                'Latitude': 'mean',
                'Longitude': 'mean',
                'Contract Amount': ['sum', 'count']
            }).reset_index()

            project_locations.columns = ['Project', 'Latitude', 'Longitude', 'Total Sales', 'Units Sold']
            project_locations['size'] = np.sqrt(project_locations['Total Sales']) / 100

            # Format total sales values with commas for hover data
            project_locations['Total Sales (Euro)'] = project_locations['Total Sales'].apply(
                lambda x: f"{x:,.2f} €")

            # Combine your plot with the existing project locations
            all_locations = pd.concat([project_locations, custom_plot], ignore_index=True)

            # Create the concentration map
            fig9 = px.scatter_mapbox(
                all_locations,
                lat="Latitude",
                lon="Longitude",
                hover_name="Project",
                hover_data={
                    "Total Sales (Euro)": True,
                    "Units Sold": True,
                    "Latitude": False,
                    "Longitude": False,
                    "size": False
                },
                color="Total Sales",
                size="size",
                size_max=25,
                zoom=13,
                height=600,
                color_continuous_scale=px.colors.sequential.Plasma
            )

            # Update map style
            fig9.update_layout(
                mapbox_style="open-street-map",
                margin={"r": 0, "t": 0, "l": 0, "b": 0}
            )

            # Display the map
            st.plotly_chart(fig9, use_container_width=True)
        else:
            st.info("No location data available for the selected filters.")

# Footer with disclaimer
st.markdown("---")
st.caption("Data last updated: March 2025 | Dashboard created for Notion embedding")