import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_aqi_gauge(aqi_value):
    """Create an AQI gauge chart"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = aqi_value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Air Quality Index"},
        delta = {'reference': 100},
        gauge = {
            'axis': {'range': [None, 500]},
            'bar': {'color': get_aqi_color(aqi_value)},
            'steps': [
                {'range': [0, 50], 'color': "lightgreen"},
                {'range': [50, 100], 'color': "yellow"},
                {'range': [100, 150], 'color': "orange"},
                {'range': [150, 200], 'color': "red"},
                {'range': [200, 300], 'color': "purple"},
                {'range': [300, 500], 'color': "darkred"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': aqi_value
            }
        }
    ))
    
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def get_aqi_color(aqi_value):
    """Get color based on AQI value"""
    if aqi_value <= 50:
        return "green"
    elif aqi_value <= 100:
        return "yellow"
    elif aqi_value <= 150:
        return "orange"
    elif aqi_value <= 200:
        return "red"
    elif aqi_value <= 300:
        return "purple"
    else:
        return "maroon"

def get_aqi_category(aqi_value):
    """Get AQI category based on value"""
    if aqi_value <= 50:
        return "Good"
    elif aqi_value <= 100:
        return "Moderate"
    elif aqi_value <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi_value <= 200:
        return "Unhealthy"
    elif aqi_value <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"

def get_health_message(aqi_value):
    """Get health message based on AQI value"""
    if aqi_value <= 50:
        return "Air quality is satisfactory and poses little to no health risk."
    elif aqi_value <= 100:
        return "Air quality is acceptable. Sensitive individuals may experience minor symptoms."
    elif aqi_value <= 150:
        return "Sensitive groups may experience health effects. General public is less likely to be affected."
    elif aqi_value <= 200:
        return "Everyone may begin to experience health effects. Sensitive groups may experience more serious effects."
    elif aqi_value <= 300:
        return "Health warnings of emergency conditions. Everyone may experience more serious health effects."
    else:
        return "Emergency conditions. Everyone is likely to be affected. Avoid outdoor activities."

def create_time_series_chart(df, pollutant='aqi', title_suffix=''):
    """Create time series chart for pollutant data"""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    fig = go.Figure()
    
    # Add main line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df[pollutant],
        mode='lines+markers',
        name=f'{pollutant.upper()}',
        line=dict(color='blue', width=2),
        marker=dict(size=4)
    ))
    
    # Add AQI category background colors if plotting AQI
    if pollutant == 'aqi':
        fig.add_hrect(y0=0, y1=50, fillcolor="green", opacity=0.1, annotation_text="Good", annotation_position="left")
        fig.add_hrect(y0=50, y1=100, fillcolor="yellow", opacity=0.1, annotation_text="Moderate", annotation_position="left")
        fig.add_hrect(y0=100, y1=150, fillcolor="orange", opacity=0.1, annotation_text="Unhealthy for Sensitive", annotation_position="left")
        fig.add_hrect(y0=150, y1=200, fillcolor="red", opacity=0.1, annotation_text="Unhealthy", annotation_position="left")
        fig.add_hrect(y0=200, y1=300, fillcolor="purple", opacity=0.1, annotation_text="Very Unhealthy", annotation_position="left")
        fig.add_hrect(y0=300, y1=500, fillcolor="maroon", opacity=0.1, annotation_text="Hazardous", annotation_position="left")
    
    fig.update_layout(
        title=f'{pollutant.upper()} Trend Over Time {title_suffix}',
        xaxis_title='Time',
        yaxis_title=f'{pollutant.upper()} Value',
        hovermode='x unified',
        showlegend=True
    )
    
    return fig

def create_pollutant_comparison_chart(df):
    """Create comparison chart for multiple pollutants"""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    fig = go.Figure()
    
    pollutants = ['pm25', 'pm10', 'no2', 'so2', 'o3']
    colors = ['red', 'orange', 'blue', 'green', 'purple']
    
    for pollutant, color in zip(pollutants, colors):
        if pollutant in df.columns:
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df[pollutant],
                mode='lines',
                name=pollutant.upper(),
                line=dict(color=color)
            ))
    
    fig.update_layout(
        title='Pollutant Concentrations Over Time',
        xaxis_title='Time',
        yaxis_title='Concentration (μg/m³)',
        hovermode='x unified'
    )
    
    return fig

def create_daily_pattern_chart(df, pollutant='aqi'):
    """Create chart showing daily pattern"""
    if df.empty or 'timestamp' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Extract hour from timestamp
    df_copy = df.copy()
    df_copy['hour'] = pd.to_datetime(df_copy['timestamp']).dt.hour
    
    # Calculate average by hour
    hourly_avg = df_copy.groupby('hour')[pollutant].mean().reset_index()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hourly_avg['hour'],
        y=hourly_avg[pollutant],
        mode='lines+markers',
        name=f'Average {pollutant.upper()}',
        line=dict(color='blue', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=f'Daily Pattern - Average {pollutant.upper()} by Hour',
        xaxis_title='Hour of Day',
        yaxis_title=f'Average {pollutant.upper()}',
        xaxis=dict(tickmode='linear', tick0=0, dtick=2)
    )
    
    return fig

def create_prediction_chart(historical_data, predictions):
    """Create chart showing predictions vs historical data"""
    fig = go.Figure()
    
    # Historical data
    if not historical_data.empty:
        fig.add_trace(go.Scatter(
            x=historical_data['timestamp'],
            y=historical_data['aqi'],
            mode='lines',
            name='Historical AQI',
            line=dict(color='blue')
        ))
    
    # Predictions
    if 'hourly_predictions' in predictions:
        # ARIMA hourly predictions
        future_times = pd.date_range(
            start=historical_data['timestamp'].iloc[-1] + timedelta(hours=1),
            periods=len(predictions['hourly_predictions']),
            freq='H'
        )
        
        pred_values = [p['predicted_aqi'] for p in predictions['hourly_predictions']]
        upper_bounds = [p['upper_bound'] for p in predictions['hourly_predictions']]
        lower_bounds = [p['lower_bound'] for p in predictions['hourly_predictions']]
        
        # Prediction line
        fig.add_trace(go.Scatter(
            x=future_times,
            y=pred_values,
            mode='lines+markers',
            name='Predicted AQI',
            line=dict(color='red', dash='dash')
        ))
        
        # Confidence interval
        fig.add_trace(go.Scatter(
            x=future_times,
            y=upper_bounds,
            mode='lines',
            line=dict(width=0),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=future_times,
            y=lower_bounds,
            mode='lines',
            fill='tonexty',
            fillcolor='rgba(255,0,0,0.1)',
            line=dict(width=0),
            name='Confidence Interval'
        ))
    
    elif 'predicted_aqi' in predictions:
        # Random Forest point prediction
        future_time = historical_data['timestamp'].iloc[-1] + timedelta(days=1)
        
        fig.add_trace(go.Scatter(
            x=[future_time],
            y=[predictions['predicted_aqi']],
            mode='markers',
            name='Next Day Prediction',
            marker=dict(color='red', size=12, symbol='diamond')
        ))
        
        # Prediction interval if available
        if 'prediction_interval' in predictions:
            fig.add_trace(go.Scatter(
                x=[future_time, future_time],
                y=predictions['prediction_interval'],
                mode='lines',
                name='Prediction Interval',
                line=dict(color='red', dash='dot')
            ))
    
    fig.update_layout(
        title='Air Quality Predictions',
        xaxis_title='Time',
        yaxis_title='AQI',
        hovermode='x unified'
    )
    
    return fig

def create_correlation_heatmap(df):
    """Create correlation heatmap for pollutants"""
    pollutant_cols = ['pm25', 'pm10', 'no2', 'so2', 'o3', 'co', 'aqi']
    available_cols = [col for col in pollutant_cols if col in df.columns]
    
    if len(available_cols) < 2:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data for correlation analysis",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    corr_matrix = df[available_cols].corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmid=0,
        text=np.round(corr_matrix.values, 2),
        texttemplate="%{text}",
        textfont={"size": 10},
        colorbar=dict(title="Correlation")
    ))
    
    fig.update_layout(
        title='Pollutant Correlation Matrix',
        xaxis_title='Pollutants',
        yaxis_title='Pollutants'
    )
    
    return fig

def create_feature_importance_chart(feature_importance):
    """Create feature importance chart"""
    if not feature_importance:
        fig = go.Figure()
        fig.add_annotation(
            text="No feature importance data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Get top 15 features
    top_features = dict(list(feature_importance.items())[:15])
    
    fig = go.Figure(go.Bar(
        x=list(top_features.values()),
        y=list(top_features.keys()),
        orientation='h',
        marker=dict(color='skyblue')
    ))
    
    fig.update_layout(
        title='Top Feature Importance (Random Forest)',
        xaxis_title='Importance Score',
        yaxis_title='Features',
        height=500
    )
    
    return fig
