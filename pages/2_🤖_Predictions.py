import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from data_collector import DataCollector
from ml_models import AirQualityPredictor

st.set_page_config(page_title="AQI Predictions", page_icon="🤖", layout="wide")

st.title("🤖 Air Quality Predictions & Forecasts")
st.markdown("*ML-powered next-day air quality forecasts*")

with st.sidebar:
    st.header("Prediction Settings")
    
    cities = ["Delhi", "Mumbai", "Kolkata", "Chennai", "Bangalore", "Hyderabad"]
    selected_city = st.selectbox("Select City", cities)
    
    model_type = st.radio(
        "Prediction Model",
        ["Random Forest", "ARIMA", "Ensemble"],
        help="Choose the machine learning model for predictions"
    )
    
    forecast_hours = st.slider("Forecast Period (hours)", 6, 72, 24)

if 'data_collector' not in st.session_state:
    st.session_state.data_collector = DataCollector()

try:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Current Status & Short-term Forecast")
    
    with col2:
        if st.button("🔄 Generate New Predictions", type="primary"):
            st.session_state.refresh_predictions = True
    
    with st.spinner(f"Loading historical data for {selected_city}..."):
        historical_data = st.session_state.data_collector.get_historical_data(
            selected_city,
            days=30
        )
    
    if historical_data is not None and not historical_data.empty:
        predictor = AirQualityPredictor()
        
        with st.spinner("Training prediction models..."):
            if model_type == "Random Forest" or model_type == "Ensemble":
                try:
                    metrics = predictor.train_random_forest(historical_data, target_column='aqi')
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Model R² Score", f"{metrics.get('r2', 0):.3f}")
                    with col2:
                        st.metric("MAE", f"{metrics.get('mae', 0):.2f}")
                    with col3:
                        st.metric("RMSE", f"{metrics.get('rmse', 0):.2f}")
                except Exception as e:
                    st.warning(f"Random Forest training: {str(e)}")
            
            if model_type == "ARIMA" or model_type == "Ensemble":
                try:
                    arima_metrics = predictor.train_arima(historical_data, target_column='aqi')
                    if arima_metrics:
                        st.info(f"ARIMA model trained successfully")
                except Exception as e:
                    st.warning(f"ARIMA training: {str(e)}")
        
        st.subheader("🔮 Next 24-Hour Forecast")
        
        try:
            predictions = predictor.predict_next_day(historical_data, hours_ahead=forecast_hours)
            
            if predictions is not None and not predictions.empty:
                latest_actual = historical_data.tail(24)
                
                fig = go.Figure()
                
                if 'aqi' in latest_actual.columns:
                    fig.add_trace(go.Scatter(
                        x=latest_actual['timestamp'],
                        y=latest_actual['aqi'],
                        name='Historical AQI',
                        mode='lines',
                        line=dict(color='blue')
                    ))
                
                if 'predicted_aqi' in predictions.columns:
                    fig.add_trace(go.Scatter(
                        x=predictions['timestamp'],
                        y=predictions['predicted_aqi'],
                        name='Predicted AQI',
                        mode='lines',
                        line=dict(color='red', dash='dash')
                    ))
                
                fig.update_layout(
                    title=f'AQI Forecast for {selected_city}',
                    xaxis_title='Time',
                    yaxis_title='AQI',
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("📋 Prediction Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    current_aqi = historical_data['aqi'].iloc[-1] if 'aqi' in historical_data.columns else 0
                    st.metric("Current AQI", f"{current_aqi:.0f}")
                
                with col2:
                    avg_predicted = predictions['predicted_aqi'].mean() if 'predicted_aqi' in predictions.columns else 0
                    change = avg_predicted - current_aqi
                    st.metric(
                        "Avg Predicted AQI",
                        f"{avg_predicted:.0f}",
                        f"{change:+.0f}"
                    )
                
                with col3:
                    max_predicted = predictions['predicted_aqi'].max() if 'predicted_aqi' in predictions.columns else 0
                    st.metric("Peak Predicted", f"{max_predicted:.0f}")
                
                with col4:
                    trend = "Improving" if change < -10 else "Worsening" if change > 10 else "Stable"
                    st.metric("Trend", trend)
                
                if avg_predicted > 150:
                    st.error("⚠️ **Health Alert**: Predictions indicate unhealthy air quality. Vulnerable populations should limit outdoor activities.")
                elif avg_predicted > 100:
                    st.warning("⚠️ **Caution**: Moderate to unhealthy air quality predicted. Sensitive groups should take precautions.")
                else:
                    st.success("✅ Air quality is expected to remain at acceptable levels.")
                
                with st.expander("📊 View Detailed Predictions"):
                    st.dataframe(
                        predictions[['timestamp', 'predicted_aqi']].head(24),
                        use_container_width=True
                    )
            else:
                st.info("Unable to generate predictions. Please try again with more historical data.")
                
        except Exception as e:
            st.error(f"Prediction error: {str(e)}")
            st.info("Model requires sufficient historical data for accurate predictions.")
        
        st.subheader("📈 Model Performance")
        
        with st.expander("View Model Details"):
            st.markdown(f"""
            **Selected Model**: {model_type}
            
            **Training Data**:
            - Period: Last 30 days
            - Data points: {len(historical_data)}
            - City: {selected_city}
            
            **Features Used**:
            - Temporal patterns (hour, day, month)
            - Lag features (previous 1, 3, 6, 12, 24 hours)
            - Rolling statistics (6, 12, 24-hour windows)
            - Weather estimates
            
            **Prediction Horizon**: {forecast_hours} hours ahead
            """)
    
    else:
        st.error("Insufficient historical data for predictions.")
        st.info("Please ensure the data source is accessible and try again.")
        
except Exception as e:
    st.error(f"Error in prediction module: {str(e)}")
    import traceback
    with st.expander("Debug Information"):
        st.code(traceback.format_exc())
