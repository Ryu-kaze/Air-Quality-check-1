import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_collector import DataCollector

st.set_page_config(page_title="Geographic View", page_icon="🗺️", layout="wide")

st.title("🗺️ Geographic Analysis & Hotspot Mapping")
st.markdown("*Spatial distribution and pollution hotspot identification*")

with st.sidebar:
    st.header("Map Settings")
    
    view_type = st.radio(
        "View Type",
        ["Multi-City Overview", "City Hotspots", "Regional Analysis"]
    )
    
    pollutant_display = st.selectbox(
        "Pollutant to Display",
        ["AQI", "PM2.5", "PM10", "NO2"]
    )

if 'data_collector' not in st.session_state:
    st.session_state.data_collector = DataCollector()

try:
    if view_type == "Multi-City Overview":
        st.subheader("🌍 Multi-City Air Quality Map")
        
        cities = ["Delhi", "Mumbai", "Kolkata", "Chennai", "Bangalore", "Hyderabad"]
        
        city_coords = {
            "Delhi": {"lat": 28.6139, "lon": 77.2090},
            "Mumbai": {"lat": 19.0760, "lon": 72.8777},
            "Kolkata": {"lat": 22.5726, "lon": 88.3639},
            "Chennai": {"lat": 13.0827, "lon": 80.2707},
            "Bangalore": {"lat": 12.9716, "lon": 77.5946},
            "Hyderabad": {"lat": 17.3850, "lon": 78.4867}
        }
        
        map_data = []
        
        with st.spinner("Fetching data for all cities..."):
            for city in cities:
                data = st.session_state.data_collector.get_current_aqi(city)
                if data is not None and not data.empty:
                    coords = city_coords.get(city, {"lat": 0, "lon": 0})
                    
                    pollutant_col = pollutant_display.lower().replace(".", "")
                    value = data[pollutant_col].iloc[0] if pollutant_col in data.columns else 0
                    
                    map_data.append({
                        'city': city,
                        'lat': coords['lat'],
                        'lon': coords['lon'],
                        'value': value,
                        'pollutant': pollutant_display
                    })
        
        if map_data:
            df_map = pd.DataFrame(map_data)
            
            fig = px.scatter_mapbox(
                df_map,
                lat='lat',
                lon='lon',
                size='value',
                color='value',
                hover_name='city',
                hover_data={'value': ':.1f', 'lat': False, 'lon': False},
                color_continuous_scale='RdYlGn_r',
                size_max=50,
                zoom=4,
                center={"lat": 20.5937, "lon": 78.9629}
            )
            
            fig.update_layout(
                mapbox_style="open-street-map",
                height=600,
                title=f'{pollutant_display} Levels Across Major Cities'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                worst_city = df_map.loc[df_map['value'].idxmax()]
                st.error(f"**Highest {pollutant_display}**: {worst_city['city']} ({worst_city['value']:.1f})")
            
            with col2:
                best_city = df_map.loc[df_map['value'].idxmin()]
                st.success(f"**Lowest {pollutant_display}**: {best_city['city']} ({best_city['value']:.1f})")
            
            with col3:
                avg_value = df_map['value'].mean()
                st.info(f"**Average {pollutant_display}**: {avg_value:.1f}")
            
            st.subheader("📊 City Comparison")
            
            fig_bar = px.bar(
                df_map,
                x='city',
                y='value',
                color='value',
                title=f'{pollutant_display} Comparison Across Cities',
                labels={'value': pollutant_display, 'city': 'City'},
                color_continuous_scale='RdYlGn_r'
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("Unable to fetch data for city comparison.")
    
    elif view_type == "City Hotspots":
        st.subheader("🔥 Pollution Hotspot Analysis")
        
        selected_city = st.selectbox(
            "Select City",
            ["Delhi", "Mumbai", "Kolkata", "Chennai", "Bangalore", "Hyderabad"]
        )
        
        st.info(f"Analyzing pollution hotspots in {selected_city}...")
        
        hotspot_data = st.session_state.data_collector.get_location_data(selected_city)
        
        if hotspot_data is not None and not hotspot_data.empty:
            pollutant_col = pollutant_display.lower().replace(".", "")
            
            if all(col in hotspot_data.columns for col in ['latitude', 'longitude', pollutant_col]):
                fig = px.density_mapbox(
                    hotspot_data,
                    lat='latitude',
                    lon='longitude',
                    z=pollutant_col,
                    radius=20,
                    center={"lat": hotspot_data['latitude'].mean(), 
                           "lon": hotspot_data['longitude'].mean()},
                    zoom=10,
                    mapbox_style="open-street-map",
                    color_continuous_scale='RdYlGn_r',
                    title=f'{pollutant_display} Hotspots in {selected_city}'
                )
                
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("**Hotspot Identification**")
                top_locations = hotspot_data.nlargest(5, pollutant_col)
                
                for idx, row in top_locations.iterrows():
                    location_name = row.get('location', f"Location {idx}")
                    value = row[pollutant_col]
                    st.warning(f"📍 **{location_name}**: {pollutant_display} = {value:.1f}")
            else:
                st.info(f"Detailed location data not available for {selected_city}")
        else:
            st.info(f"Hotspot data not available for {selected_city}. Showing general city data instead.")
    
    else:  # Regional Analysis
        st.subheader("🌏 Regional Air Quality Analysis")
        
        region = st.selectbox(
            "Select Region",
            ["North India", "South India", "West India", "East India"]
        )
        
        region_cities = {
            "North India": ["Delhi", "Chandigarh", "Jaipur"],
            "South India": ["Chennai", "Bangalore", "Hyderabad"],
            "West India": ["Mumbai", "Pune", "Ahmedabad"],
            "East India": ["Kolkata", "Patna", "Bhubaneswar"]
        }
        
        cities_in_region = region_cities.get(region, [])
        
        st.info(f"Analyzing {len(cities_in_region)} cities in {region}")
        
        regional_data = []
        
        for city in cities_in_region:
            data = st.session_state.data_collector.get_current_aqi(city)
            if data is not None and not data.empty:
                pollutant_col = pollutant_display.lower().replace(".", "")
                value = data[pollutant_col].iloc[0] if pollutant_col in data.columns else 0
                
                regional_data.append({
                    'city': city,
                    'value': value
                })
        
        if regional_data:
            df_region = pd.DataFrame(regional_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_pie = px.pie(
                    df_region,
                    values='value',
                    names='city',
                    title=f'{pollutant_display} Distribution in {region}'
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                fig_bar = px.bar(
                    df_region,
                    x='city',
                    y='value',
                    color='value',
                    title=f'{pollutant_display} Levels',
                    color_continuous_scale='RdYlGn_r'
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            
            avg_regional = df_region['value'].mean()
            st.metric(f"Regional Average {pollutant_display}", f"{avg_regional:.1f}")
        else:
            st.warning(f"Unable to fetch data for {region}")

except Exception as e:
    st.error(f"Error in geographic analysis: {str(e)}")
    import traceback
    with st.expander("Debug Information"):
        st.code(traceback.format_exc())
