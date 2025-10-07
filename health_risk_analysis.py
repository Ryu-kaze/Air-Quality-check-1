import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

class HealthRiskAnalyzer:
    def __init__(self):
        # WHO health risk thresholds (annual averages in μg/m³)
        self.who_thresholds = {
            'pm25': {'safe': 5, 'moderate': 15, 'unhealthy': 25, 'hazardous': 50},
            'pm10': {'safe': 15, 'moderate': 45, 'unhealthy': 75, 'hazardous': 150},
            'no2': {'safe': 10, 'moderate': 25, 'unhealthy': 40, 'hazardous': 100}
        }
        
        # Vulnerable population factors
        self.vulnerability_factors = {
            'children_under_5': 1.8,        # 80% higher risk
            'elderly_over_65': 1.6,         # 60% higher risk
            'respiratory_conditions': 2.2,  # 120% higher risk
            'cardiovascular_conditions': 1.9, # 90% higher risk
            'pregnant_women': 1.4,          # 40% higher risk
            'outdoor_workers': 1.5          # 50% higher risk
        }
        
        # Demographic data for major Indian cities (approximate percentages)
        self.city_demographics = {
            'Delhi': {
                'children_under_5': 8.2,
                'elderly_over_65': 4.6,
                'respiratory_conditions': 12.5,
                'cardiovascular_conditions': 8.9,
                'pregnant_women': 2.1,
                'outdoor_workers': 28.5,
                'population': 32900000,
                'low_income_percentage': 35.2
            },
            'Mumbai': {
                'children_under_5': 7.8,
                'elderly_over_65': 5.2,
                'respiratory_conditions': 10.8,
                'cardiovascular_conditions': 7.6,
                'pregnant_women': 1.9,
                'outdoor_workers': 31.2,
                'population': 20700000,
                'low_income_percentage': 41.3
            },
            'Kolkata': {
                'children_under_5': 8.9,
                'elderly_over_65': 6.1,
                'respiratory_conditions': 14.2,
                'cardiovascular_conditions': 9.8,
                'pregnant_women': 2.0,
                'outdoor_workers': 25.7,
                'population': 15000000,
                'low_income_percentage': 32.8
            },
            'Chennai': {
                'children_under_5': 7.5,
                'elderly_over_65': 5.8,
                'respiratory_conditions': 9.8,
                'cardiovascular_conditions': 7.2,
                'pregnant_women': 1.8,
                'outdoor_workers': 23.4,
                'population': 11700000,
                'low_income_percentage': 29.6
            },
            'Bangalore': {
                'children_under_5': 7.2,
                'elderly_over_65': 4.9,
                'respiratory_conditions': 8.9,
                'cardiovascular_conditions': 6.8,
                'pregnant_women': 1.9,
                'outdoor_workers': 22.1,
                'population': 13200000,
                'low_income_percentage': 26.4
            },
            'Hyderabad': {
                'children_under_5': 7.8,
                'elderly_over_65': 5.1,
                'respiratory_conditions': 10.2,
                'cardiovascular_conditions': 7.5,
                'pregnant_women': 2.0,
                'outdoor_workers': 24.8,
                'population': 10500000,
                'low_income_percentage': 31.2
            }
        }
    
    def calculate_health_risk_score(self, aqi_value, city_name):
        """Calculate comprehensive health risk score"""
        if city_name not in self.city_demographics:
            city_name = 'Delhi'  # Default fallback
        
        demographics = self.city_demographics[city_name]
        
        # Base risk from AQI
        if aqi_value <= 50:
            base_risk = 0.1
        elif aqi_value <= 100:
            base_risk = 0.3
        elif aqi_value <= 150:
            base_risk = 0.6
        elif aqi_value <= 200:
            base_risk = 0.8
        elif aqi_value <= 300:
            base_risk = 0.95
        else:
            base_risk = 1.0
        
        # Calculate population-weighted risk
        total_risk = 0
        total_population_factor = 0
        
        for group, vulnerability in self.vulnerability_factors.items():
            if group in demographics:
                pop_percentage = demographics[group] / 100
                group_risk = base_risk * vulnerability * pop_percentage
                total_risk += group_risk
                total_population_factor += pop_percentage
        
        # Normalize by population factors
        if total_population_factor > 0:
            weighted_risk = total_risk / total_population_factor
        else:
            weighted_risk = base_risk
        
        # Adjust for socioeconomic factors
        low_income_factor = 1 + (demographics['low_income_percentage'] / 100 * 0.3)  # 30% additional risk
        final_risk = min(weighted_risk * low_income_factor, 1.0)
        
        return final_risk
    
    def get_vulnerable_populations_at_risk(self, aqi_value, city_name):
        """Calculate number of people at risk in vulnerable populations"""
        if city_name not in self.city_demographics:
            city_name = 'Delhi'
        
        demographics = self.city_demographics[city_name]
        total_population = demographics['population']
        
        at_risk_populations = {}
        
        # Define risk threshold based on AQI
        if aqi_value <= 100:
            risk_threshold = 0.1  # Only highly sensitive affected
        elif aqi_value <= 150:
            risk_threshold = 0.3
        else:
            risk_threshold = 0.6  # Most vulnerable populations affected
        
        for group, vulnerability in self.vulnerability_factors.items():
            if group in demographics:
                group_population = total_population * (demographics[group] / 100)
                
                # Calculate risk level for this group
                base_risk = self._get_base_risk_from_aqi(aqi_value)
                group_risk = base_risk * vulnerability
                
                # People at risk in this group
                if group_risk >= risk_threshold:
                    at_risk_count = int(group_population * group_risk)
                    at_risk_populations[group] = {
                        'total_population': int(group_population),
                        'at_risk_count': at_risk_count,
                        'risk_level': group_risk,
                        'percentage': demographics[group]
                    }
        
        return at_risk_populations
    
    def _get_base_risk_from_aqi(self, aqi_value):
        """Get base risk level from AQI value"""
        if aqi_value <= 50:
            return 0.05
        elif aqi_value <= 100:
            return 0.15
        elif aqi_value <= 150:
            return 0.35
        elif aqi_value <= 200:
            return 0.60
        elif aqi_value <= 300:
            return 0.85
        else:
            return 1.0
    
    def calculate_health_impact_metrics(self, air_quality_data, city_name):
        """Calculate comprehensive health impact metrics"""
        if air_quality_data.empty:
            return {}
        
        if city_name not in self.city_demographics:
            city_name = 'Delhi'
        
        demographics = self.city_demographics[city_name]
        
        # Calculate average pollutant levels
        avg_pm25 = air_quality_data['pm25'].mean() if 'pm25' in air_quality_data.columns else 0
        avg_pm10 = air_quality_data['pm10'].mean() if 'pm10' in air_quality_data.columns else 0
        avg_no2 = air_quality_data['no2'].mean() if 'no2' in air_quality_data.columns else 0
        avg_aqi = air_quality_data['aqi'].mean() if 'aqi' in air_quality_data.columns else 0
        
        # Calculate excess deaths attributable to air pollution (simplified model)
        # Based on epidemiological studies showing relationship between PM2.5 and mortality
        baseline_mortality_rate = 0.008  # 0.8% annual mortality rate
        pm25_risk_factor = max(0, (avg_pm25 - 10) / 10 * 0.06)  # 6% increase per 10 μg/m³ above WHO guideline
        
        excess_deaths_annual = int(demographics['population'] * baseline_mortality_rate * pm25_risk_factor)
        
        # Calculate respiratory illness cases
        respiratory_baseline = 0.15  # 15% baseline respiratory illness rate
        respiratory_risk_factor = max(0, (avg_pm25 - 10) / 10 * 0.12)  # 12% increase per 10 μg/m³
        
        excess_respiratory_cases = int(demographics['population'] * respiratory_baseline * respiratory_risk_factor)
        
        # Calculate economic impact (simplified)
        cost_per_death = 3500000  # 35 lakhs INR (approximate value of statistical life in India)
        cost_per_illness = 25000   # 25,000 INR average treatment cost
        
        economic_impact = (excess_deaths_annual * cost_per_death) + (excess_respiratory_cases * cost_per_illness)
        
        # Calculate days when air quality exceeded healthy levels
        unhealthy_days = len(air_quality_data[air_quality_data['aqi'] > 100]) if 'aqi' in air_quality_data.columns else 0
        total_days = len(air_quality_data)
        
        return {
            'city': city_name,
            'population': demographics['population'],
            'average_aqi': avg_aqi,
            'average_pm25': avg_pm25,
            'average_pm10': avg_pm10,
            'average_no2': avg_no2,
            'excess_deaths_annual': excess_deaths_annual,
            'excess_respiratory_cases': excess_respiratory_cases,
            'economic_impact_inr': economic_impact,
            'unhealthy_days': unhealthy_days,
            'total_days': total_days,
            'percentage_unhealthy_days': (unhealthy_days / total_days * 100) if total_days > 0 else 0,
            'who_pm25_exceedance': max(0, avg_pm25 - 5),  # WHO guideline is 5 μg/m³
            'who_pm10_exceedance': max(0, avg_pm10 - 15), # WHO guideline is 15 μg/m³
            'low_income_population': int(demographics['population'] * demographics['low_income_percentage'] / 100)
        }
    
    def create_vulnerability_map_data(self, cities_data):
        """Create data for vulnerability mapping"""
        map_data = []
        
        for city, data in cities_data.items():
            if city in self.city_demographics:
                demographics = self.city_demographics[city]
                
                # Calculate overall vulnerability score
                vulnerability_score = 0
                for group, factor in self.vulnerability_factors.items():
                    if group in demographics:
                        vulnerability_score += (demographics[group] / 100) * factor
                
                # Normalize vulnerability score
                vulnerability_score = min(vulnerability_score / len(self.vulnerability_factors), 1.0)
                
                # Calculate current risk
                current_aqi = data.get('aqi', 150)
                risk_score = self.calculate_health_risk_score(current_aqi, city)
                
                map_data.append({
                    'city': city,
                    'latitude': 28.6139 if city == 'Delhi' else 19.0760,  # Simplified coordinates
                    'longitude': 77.2090 if city == 'Delhi' else 72.8777,
                    'population': demographics['population'],
                    'vulnerability_score': vulnerability_score,
                    'current_risk_score': risk_score,
                    'current_aqi': current_aqi,
                    'low_income_percentage': demographics['low_income_percentage'],
                    'children_percentage': demographics['children_under_5'],
                    'elderly_percentage': demographics['elderly_over_65']
                })
        
        return pd.DataFrame(map_data)
    
    def create_health_inequity_chart(self, city_name, aqi_value):
        """Create chart showing health inequities"""
        at_risk_pops = self.get_vulnerable_populations_at_risk(aqi_value, city_name)
        
        if not at_risk_pops:
            fig = go.Figure()
            fig.add_annotation(
                text="No significant health risks identified at current air quality levels",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16)
            )
            return fig
        
        # Prepare data for visualization
        groups = []
        at_risk_counts = []
        risk_levels = []
        colors = []
        
        group_names = {
            'children_under_5': 'Children Under 5',
            'elderly_over_65': 'Elderly (65+)',
            'respiratory_conditions': 'Respiratory Conditions',
            'cardiovascular_conditions': 'Cardiovascular Conditions',
            'pregnant_women': 'Pregnant Women',
            'outdoor_workers': 'Outdoor Workers'
        }
        
        for group, data in at_risk_pops.items():
            groups.append(group_names.get(group, group))
            at_risk_counts.append(data['at_risk_count'])
            risk_levels.append(data['risk_level'])
            
            # Color based on risk level
            if data['risk_level'] < 0.3:
                colors.append('yellow')
            elif data['risk_level'] < 0.6:
                colors.append('orange')
            else:
                colors.append('red')
        
        # Create horizontal bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=groups,
            x=at_risk_counts,
            orientation='h',
            marker_color=colors,
            text=[f"{count:,} people" for count in at_risk_counts],
            textposition='inside',
            name='People at Risk'
        ))
        
        fig.update_layout(
            title=f'Vulnerable Populations at Risk - {city_name} (AQI: {aqi_value:.0f})',
            xaxis_title='Number of People at Risk',
            yaxis_title='Vulnerable Groups',
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_risk_comparison_chart(self, cities_air_quality_data):
        """Create chart comparing health risks across cities"""
        risk_data = []
        
        for city, data in cities_air_quality_data.items():
            if not data.empty and 'aqi' in data.columns:
                avg_aqi = data['aqi'].mean()
                risk_score = self.calculate_health_risk_score(avg_aqi, city)
                
                if city in self.city_demographics:
                    demographics = self.city_demographics[city]
                    risk_data.append({
                        'city': city,
                        'risk_score': risk_score,
                        'avg_aqi': avg_aqi,
                        'population': demographics['population'],
                        'low_income_percentage': demographics['low_income_percentage']
                    })
        
        if not risk_data:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for risk comparison",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16)
            )
            return fig
        
        df = pd.DataFrame(risk_data)
        
        # Create bubble chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['avg_aqi'],
            y=df['risk_score'],
            mode='markers+text',
            marker=dict(
                size=df['population'] / 500000,  # Scale bubble size
                color=df['low_income_percentage'],
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="Low Income %"),
                sizemin=10,
                sizemode='diameter'
            ),
            text=df['city'],
            textposition='top center',
            name='Cities'
        ))
        
        fig.update_layout(
            title='Health Risk vs Air Quality by City',
            xaxis_title='Average AQI',
            yaxis_title='Health Risk Score',
            height=500
        )
        
        return fig
    
    def generate_health_recommendations(self, aqi_value, city_name):
        """Generate health recommendations based on current conditions"""
        recommendations = []
        
        if aqi_value <= 50:
            recommendations.append("✅ Air quality is good. Normal outdoor activities are safe for everyone.")
            
        elif aqi_value <= 100:
            recommendations.append("⚠️ Air quality is moderate. Sensitive individuals should consider limiting prolonged outdoor activities.")
            recommendations.append("💡 Children and elderly should avoid strenuous outdoor activities during peak hours.")
            
        elif aqi_value <= 150:
            recommendations.append("🚨 Unhealthy for sensitive groups. Children, elderly, and people with respiratory/heart conditions should avoid outdoor activities.")
            recommendations.append("😷 Consider wearing N95 masks when outdoors.")
            recommendations.append("🏠 Keep windows closed and use air purifiers indoors.")
            
        elif aqi_value <= 200:
            recommendations.append("⛔ Unhealthy air quality. Everyone should avoid prolonged outdoor activities.")
            recommendations.append("😷 Wear N95 masks when going outdoors.")
            recommendations.append("🏠 Stay indoors with air purifiers running.")
            recommendations.append("⚕️ Seek medical attention if experiencing difficulty breathing.")
            
        else:
            recommendations.append("🆘 Hazardous air quality. Avoid all outdoor activities.")
            recommendations.append("😷 Wear N95/N99 masks even for brief outdoor exposure.")
            recommendations.append("🏠 Seal windows and doors. Use air purifiers continuously.")
            recommendations.append("⚕️ Seek immediate medical attention for any respiratory symptoms.")
            recommendations.append("🚗 Avoid driving with windows down.")
        
        # Add city-specific recommendations
        if city_name in self.city_demographics:
            demographics = self.city_demographics[city_name]
            
            if demographics['outdoor_workers'] > 25:  # High outdoor worker population
                recommendations.append(f"👷 Special attention needed for {city_name}'s large outdoor worker population - provide protective equipment and schedule breaks indoors.")
            
            if demographics['low_income_percentage'] > 35:  # High low-income population
                recommendations.append(f"🏘️ Community health centers in {city_name} should provide free masks and health check-ups for low-income residents.")
        
        return recommendations
