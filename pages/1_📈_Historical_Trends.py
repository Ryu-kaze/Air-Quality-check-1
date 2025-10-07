import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from data_collector import DataCollector
from visualization_utils import get_aqi_color

st.set_page_config(page_title="Historical Trends", page_icon="📈", layout="wide")

st.title("📈 Historical Air Quality Trends")
st.markdown("*Analyze historical patterns and time-series data*")

with st.sidebar:
    st.header("Analysis Settings")
    
    cities = ["Delhi", "Mumbai", "Kolkata", "Chennai", "Bangalore", "Hyderabad"]
    selected_city = st.selectbox("Select City", cities)
    
    days_back = st.slider("Historical Period (days)", 7, 90, 30)
    
    pollutants = st.multiselect(
        "Pollutants to Display",
        ["PM2.5", "PM10", "NO2", "AQI"],
        default=["PM2.5", "AQI"]
    )

if 'data_collector' not in st.session_state:
    st.session_state.data_collector = DataCollector()

try:
    with st.spinner(f"Fetching {days_back} days of historical data for {selected_city}..."):
        historical_data = st.session_state.data_collector.get_historical_data(
            selected_city, 
            days=days_back
        )
    
    if historical_data is not None and not historical_data.empty:
        st.success(f"✅ Loaded {len(historical_data)} data points")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_aqi = historical_data['aqi'].mean() if 'aqi' in historical_data.columns else 0
            st.metric("Average AQI", f"{avg_aqi:.1f}")
        
        with col2:
            max_aqi = historical_data['aqi'].max() if 'aqi' in historical_data.columns else 0
            st.metric("Peak AQI", f"{max_aqi:.1f}")
        
        with col3:
            avg_pm25 = historical_data['pm25'].mean() if 'pm25' in historical_data.columns else 0
            st.metric("Avg PM2.5", f"{avg_pm25:.1f} μg/m³")
        
        with col4:
            unhealthy_days = len(historical_data[historical_data['aqi'] > 150]) if 'aqi' in historical_data.columns else 0
            st.metric("Unhealthy Days", unhealthy_days)
        
        st.subheader("📊 Time Series Trends")
        
        for pollutant in pollutants:
            col_name = pollutant.lower().replace(".", "")
            
            if col_name in historical_data.columns:
                fig = px.line(
                    historical_data,
                    x='timestamp',
                    y=col_name,
                    title=f"{pollutant} Trend Over Time",
                    labels={'timestamp': 'Date', col_name: f'{pollutant} Level'}
                )
                
                fig.update_layout(
                    hovermode='x unified',
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📅 Daily Patterns")
        
        if 'timestamp' in historical_data.columns:
            historical_data['hour'] = pd.to_datetime(historical_data['timestamp']).dt.hour
            hourly_avg = historical_data.groupby('hour')[['pm25', 'pm10', 'aqi']].mean().reset_index()
            
            fig_hourly = go.Figure()
            
            if 'pm25' in hourly_avg.columns:
                fig_hourly.add_trace(go.Scatter(
                    x=hourly_avg['hour'],
                    y=hourly_avg['pm25'],
                    name='PM2.5',
                    mode='lines+markers'
                ))
            
            if 'aqi' in hourly_avg.columns:
                fig_hourly.add_trace(go.Scatter(
                    x=hourly_avg['hour'],
                    y=hourly_avg['aqi'],
                    name='AQI',
                    mode='lines+markers',
                    yaxis='y2'
                ))
            
            fig_hourly.update_layout(
                title='Average Hourly Patterns',
                xaxis=dict(title='Hour of Day'),
                yaxis=dict(title='PM2.5 (μg/m³)'),
                yaxis2=dict(title='AQI', overlaying='y', side='right'),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_hourly, use_container_width=True)
        
        st.subheader("📉 Distribution Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'aqi' in historical_data.columns:
                fig_hist = px.histogram(
                    historical_data,
                    x='aqi',
                    nbins=30,
                    title='AQI Distribution',
                    labels={'aqi': 'AQI Value'}
                )
                st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            if 'pm25' in historical_data.columns:
                fig_box = px.box(
                    historical_data,
                    y='pm25',
                    title='PM2.5 Distribution',
                    labels={'pm25': 'PM2.5 (μg/m³)'}
                )
                st.plotly_chart(fig_box, use_container_width=True)
        
    else:
        st.error("No historical data available for the selected period.")
        st.info("This could be due to API limitations or data availability issues.")
        
except Exception as e:
    st.error(f"Error loading historical data: {str(e)}")
    st.info("Please try selecting a different city or time period.")
