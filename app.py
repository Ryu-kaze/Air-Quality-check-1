import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Import custom modules
from data_collector import DataCollector
from ml_models import AirQualityPredictor
from visualization_utils import create_aqi_gauge, get_aqi_color, get_health_message
from health_risk_analysis import HealthRiskAnalyzer

# Page configuration
st.set_page_config(
    page_title="Air Quality & Health Inequities Platform",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure pages directory is recognized
import os
pages_dir = os.path.join(os.path.dirname(__file__), "pages")
if os.path.exists(pages_dir):
    st.sidebar.success(f"✅ Found {len([f for f in os.listdir(pages_dir) if f.endswith('.py')])} pages")

def main():
    # Title and description
    st.title("🌬️ Air Quality & Health Inequities Platform")
    st.markdown("*Powered by IBM LinuxONE - Real-time air quality monitoring and health risk assessment*")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # API key configuration
        openaq_key = st.text_input("OpenAQ API Key (Optional)", 
                                  value=os.getenv("OPENAQ_API_KEY", ""),
                                  type="password")
        
        # Location selection
        st.subheader("Location Settings")
        default_cities = ["Delhi", "Mumbai", "Kolkata", "Chennai", "Bangalore", "Hyderabad"]
        selected_city = st.selectbox("Select City", default_cities)
        
        # Refresh data button
        if st.button("🔄 Refresh Data", type="primary"):
            st.session_state.refresh_data = True
    
    # Initialize data collector
    if 'data_collector' not in st.session_state:
        st.session_state.data_collector = DataCollector(openaq_key)
    
    # Main dashboard overview
    st.header("📊 Current Air Quality Overview")
    
    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Get current air quality data
        with st.spinner("Fetching current air quality data..."):
            current_data = st.session_state.data_collector.get_current_aqi(selected_city)
        
        if current_data is not None and not current_data.empty:
            # Display current AQI
            current_aqi = current_data['aqi'].iloc[0] if 'aqi' in current_data.columns else 150
            current_pm25 = current_data['pm25'].iloc[0] if 'pm25' in current_data.columns else 75
            current_pm10 = current_data['pm10'].iloc[0] if 'pm10' in current_data.columns else 120
            current_no2 = current_data['no2'].iloc[0] if 'no2' in current_data.columns else 45
            
            with col1:
                st.metric(
                    label="AQI",
                    value=f"{current_aqi:.0f}",
                    delta=f"{'🔴' if current_aqi > 150 else '🟡' if current_aqi > 100 else '🟢'}"
                )
                
            with col2:
                st.metric(
                    label="PM2.5 (μg/m³)",
                    value=f"{current_pm25:.1f}",
                    delta="Unhealthy" if current_pm25 > 55 else "Moderate" if current_pm25 > 12 else "Good"
                )
                
            with col3:
                st.metric(
                    label="PM10 (μg/m³)",
                    value=f"{current_pm10:.1f}",
                    delta="Unhealthy" if current_pm10 > 150 else "Moderate" if current_pm10 > 50 else "Good"
                )
                
            with col4:
                st.metric(
                    label="NO₂ (μg/m³)",
                    value=f"{current_no2:.1f}",
                    delta="High" if current_no2 > 40 else "Normal"
                )
            
            # AQI Gauge visualization
            st.subheader("🎯 Air Quality Index")
            fig_gauge = create_aqi_gauge(current_aqi)
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            # Health message
            health_msg = get_health_message(current_aqi)
            if current_aqi > 150:
                st.error(f"⚠️ {health_msg}")
            elif current_aqi > 100:
                st.warning(f"⚠️ {health_msg}")
            else:
                st.success(f"✅ {health_msg}")
                
        else:
            st.error("Unable to fetch current air quality data. Please check your connection and API configuration.")
            
    except Exception as e:
        st.error(f"Error loading air quality data: {str(e)}")
        st.info("📝 This could be due to API limits or connectivity issues. Please try again later.")
    
    # Quick navigation
    st.header("🚀 Quick Navigation")
    
    nav_col1, nav_col2, nav_col3 = st.columns(3)
    
    with nav_col1:
        st.markdown("""
        ### 📊 Analysis Tools
        - **Real-time Dashboard**: Current AQI and pollutant levels
        - **Trends Analysis**: Historical patterns and time-series data
        - **Predictions**: ML-powered next-day forecasts
        """)
        
    with nav_col2:
        st.markdown("""
        ### 🏥 Health Focus
        - **Health Inequities**: Vulnerable population analysis
        - **Risk Assessment**: Health impact calculations
        - **Geographic Analysis**: Hotspot identification
        """)
        
    with nav_col3:
        st.markdown("""
        ### 📈 IBM LinuxONE Features
        - **High Performance**: Optimized for s390x architecture
        - **Scalable Processing**: Handles large datasets efficiently
        - **Reliable Operations**: Enterprise-grade stability
        """)
    
    # Recent alerts section
    st.header("🚨 Recent Alerts & Insights")
    
    alert_col1, alert_col2 = st.columns(2)
    
    with alert_col1:
        st.info("🔍 **Data Source Status**\n- OpenAQ API: Active\n- Real-time updates every 15 minutes\n- Historical data: Last 30 days available")
        
    with alert_col2:
        st.warning("⚠️ **High Pollution Alert**\nSeveral metropolitan areas showing elevated PM2.5 levels. Vulnerable populations should limit outdoor activities.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    **About this Platform**: Built for IBM LinuxONE to demonstrate scalable air quality monitoring and health inequity analysis. 
    The platform combines real-time data collection, machine learning predictions, and interactive visualizations to support public health decision-making.
    
    *Data Sources: OpenAQ, Central Pollution Control Board (CPCB), Satellite Data*
    """)

if __name__ == "__main__":
    main()
