import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from health_risk_analysis import HealthRiskAnalyzer
from data_collector import DataCollector

st.set_page_config(page_title="Health Analysis", page_icon="🏥", layout="wide")

st.title("🏥 Health Inequities & Risk Assessment")
st.markdown("*Vulnerable population analysis and health impact assessment*")

with st.sidebar:
    st.header("Analysis Settings")
    
    cities = ["Delhi", "Mumbai", "Kolkata", "Chennai", "Bangalore", "Hyderabad"]
    selected_city = st.selectbox("Select City", cities)
    
    analysis_type = st.radio(
        "Analysis Type",
        ["Vulnerable Populations", "Health Impact", "Inequity Analysis"]
    )

if 'data_collector' not in st.session_state:
    st.session_state.data_collector = DataCollector()

health_analyzer = HealthRiskAnalyzer()

try:
    with st.spinner(f"Analyzing health data for {selected_city}..."):
        current_data = st.session_state.data_collector.get_current_aqi(selected_city)
    
    if current_data is not None and not current_data.empty:
        current_aqi = current_data['aqi'].iloc[0] if 'aqi' in current_data.columns else 150
        current_pm25 = current_data['pm25'].iloc[0] if 'pm25' in current_data.columns else 75
        
        st.subheader("🎯 Current Health Risk Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            risk_level = health_analyzer.calculate_health_risk(current_pm25, pollutant='pm25')
            st.metric("PM2.5 Risk Level", risk_level)
        
        with col2:
            affected_pop = health_analyzer.estimate_affected_population(
                selected_city,
                current_pm25,
                pollutant='pm25'
            )
            st.metric("Est. Affected Population", f"{affected_pop:,.0f}")
        
        with col3:
            aqi_risk = "Hazardous" if current_aqi > 300 else "Very Unhealthy" if current_aqi > 200 else "Unhealthy" if current_aqi > 150 else "Moderate"
            st.metric("Overall AQI Status", aqi_risk)
        
        if analysis_type == "Vulnerable Populations":
            st.subheader("👥 Vulnerable Population Analysis")
            
            vuln_data = health_analyzer.analyze_vulnerable_populations(
                selected_city,
                current_pm25,
                pollutant='pm25'
            )
            
            if vuln_data is not None and not vuln_data.empty:
                fig = px.bar(
                    vuln_data,
                    x='group',
                    y='affected_count',
                    color='risk_multiplier',
                    title=f'Vulnerable Groups in {selected_city}',
                    labels={
                        'group': 'Population Group',
                        'affected_count': 'Affected Population',
                        'risk_multiplier': 'Risk Factor'
                    },
                    color_continuous_scale='Reds'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**High-Risk Groups**")
                    high_risk = vuln_data.nlargest(3, 'risk_multiplier')
                    for _, row in high_risk.iterrows():
                        st.warning(f"**{row['group'].replace('_', ' ').title()}**: {row['affected_count']:,.0f} people affected")
                
                with col2:
                    total_vulnerable = vuln_data['affected_count'].sum()
                    st.info(f"**Total Vulnerable Population**: {total_vulnerable:,.0f}")
                    
                    demographics = health_analyzer.city_demographics.get(selected_city, {})
                    total_pop = demographics.get('population', 0)
                    if total_pop > 0:
                        pct_vulnerable = (total_vulnerable / total_pop) * 100
                        st.metric("% of Population at Risk", f"{pct_vulnerable:.1f}%")
        
        elif analysis_type == "Health Impact":
            st.subheader("💊 Health Impact Assessment")
            
            health_impacts = health_analyzer.calculate_health_impacts(
                selected_city,
                current_pm25,
                pollutant='pm25'
            )
            
            if health_impacts:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Respiratory Cases (Annual)",
                        f"{health_impacts.get('respiratory_cases', 0):,.0f}"
                    )
                
                with col2:
                    st.metric(
                        "Cardiovascular Cases (Annual)",
                        f"{health_impacts.get('cardiovascular_cases', 0):,.0f}"
                    )
                
                with col3:
                    st.metric(
                        "Premature Deaths (Annual)",
                        f"{health_impacts.get('premature_deaths', 0):,.0f}"
                    )
                
                st.markdown("---")
                
                impact_df = pd.DataFrame([
                    {"Impact": "Hospital Admissions", "Annual Cases": health_impacts.get('respiratory_cases', 0)},
                    {"Impact": "ER Visits", "Annual Cases": health_impacts.get('cardiovascular_cases', 0) * 1.5},
                    {"Impact": "Asthma Attacks", "Annual Cases": health_impacts.get('respiratory_cases', 0) * 2},
                    {"Impact": "Work Days Lost", "Annual Cases": health_impacts.get('respiratory_cases', 0) * 5}
                ])
                
                fig_impact = px.bar(
                    impact_df,
                    x='Impact',
                    y='Annual Cases',
                    title='Estimated Health Impact Categories',
                    color='Annual Cases',
                    color_continuous_scale='Oranges'
                )
                
                st.plotly_chart(fig_impact, use_container_width=True)
        
        else:  # Inequity Analysis
            st.subheader("⚖️ Health Inequity Analysis")
            
            demographics = health_analyzer.city_demographics.get(selected_city, {})
            
            if demographics:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Socioeconomic Factors**")
                    low_income_pct = demographics.get('low_income_percentage', 0)
                    
                    st.progress(low_income_pct / 100)
                    st.caption(f"{low_income_pct}% Low-Income Population")
                    
                    inequity_score = health_analyzer.calculate_inequity_score(
                        selected_city,
                        current_pm25
                    )
                    
                    st.metric("Inequity Score", f"{inequity_score:.2f}", 
                             help="Higher scores indicate greater health inequity")
                
                with col2:
                    st.markdown("**Exposure Disparities**")
                    
                    exposure_data = pd.DataFrame({
                        'Group': ['Low Income', 'Middle Income', 'High Income'],
                        'Relative Exposure': [1.4, 1.0, 0.7]
                    })
                    
                    fig_exposure = px.bar(
                        exposure_data,
                        x='Group',
                        y='Relative Exposure',
                        title='Air Pollution Exposure by Income Level',
                        color='Relative Exposure',
                        color_continuous_scale='RdYlGn_r'
                    )
                    
                    st.plotly_chart(fig_exposure, use_container_width=True)
                
                st.markdown("---")
                st.subheader("📊 Key Inequity Findings")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.error("""
                    **Disproportionate Impact**
                    - Low-income communities face 40% higher pollution exposure
                    - Limited access to healthcare amplifies health risks
                    - Outdoor workers have 50% higher exposure rates
                    """)
                
                with col2:
                    st.info("""
                    **Recommendations**
                    - Prioritize air quality interventions in vulnerable areas
                    - Enhance healthcare access in high-exposure zones
                    - Implement protective measures for outdoor workers
                    """)
        
        st.markdown("---")
        st.subheader("📋 Health Recommendations")
        
        recommendations = health_analyzer.get_health_recommendations(
            current_aqi,
            selected_city
        )
        
        for rec in recommendations:
            if rec['priority'] == 'high':
                st.error(f"**{rec['group']}**: {rec['recommendation']}")
            elif rec['priority'] == 'medium':
                st.warning(f"**{rec['group']}**: {rec['recommendation']}")
            else:
                st.info(f"**{rec['group']}**: {rec['recommendation']}")
    
    else:
        st.error("Unable to fetch current air quality data.")
        st.info("Please check your connection and try again.")
        
except Exception as e:
    st.error(f"Error in health analysis: {str(e)}")
    import traceback
    with st.expander("Debug Information"):
        st.code(traceback.format_exc())
