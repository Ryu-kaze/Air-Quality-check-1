import psycopg2
import pandas as pd
import os
from datetime import datetime, timedelta
import json
from typing import Optional, Dict, List, Any

class DatabaseHelper:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable not set")
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)
    
    def save_air_quality_measurement(self, data: pd.DataFrame, data_source: str = 'API'):
        """Save air quality measurements to database"""
        if data.empty:
            return 0
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        inserted_count = 0
        
        try:
            for _, row in data.iterrows():
                cursor.execute("""
                    INSERT INTO air_quality_measurements 
                    (city, timestamp, location, latitude, longitude, aqi, pm25, pm10, no2, so2, o3, co, data_source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (city, timestamp, location) DO UPDATE SET
                        aqi = EXCLUDED.aqi,
                        pm25 = EXCLUDED.pm25,
                        pm10 = EXCLUDED.pm10,
                        no2 = EXCLUDED.no2,
                        so2 = EXCLUDED.so2,
                        o3 = EXCLUDED.o3,
                        co = EXCLUDED.co,
                        data_source = EXCLUDED.data_source
                """, (
                    row.get('city', ''),
                    row.get('timestamp', datetime.now()),
                    row.get('location', ''),
                    float(row.get('latitude', 0)) if pd.notna(row.get('latitude')) else None,
                    float(row.get('longitude', 0)) if pd.notna(row.get('longitude')) else None,
                    float(row.get('aqi', 0)) if pd.notna(row.get('aqi')) else None,
                    float(row.get('pm25', 0)) if pd.notna(row.get('pm25')) else None,
                    float(row.get('pm10', 0)) if pd.notna(row.get('pm10')) else None,
                    float(row.get('no2', 0)) if pd.notna(row.get('no2')) else None,
                    float(row.get('so2', 0)) if pd.notna(row.get('so2')) else None,
                    float(row.get('o3', 0)) if pd.notna(row.get('o3')) else None,
                    float(row.get('co', 0)) if pd.notna(row.get('co')) else None,
                    data_source
                ))
                inserted_count += 1
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
        
        return inserted_count
    
    def get_historical_measurements(self, city: str, days: int = 30) -> pd.DataFrame:
        """Retrieve historical measurements from database"""
        conn = self.get_connection()
        
        try:
            query = """
                SELECT city, timestamp, location, latitude, longitude, 
                       aqi, pm25, pm10, no2, so2, o3, co, data_source
                FROM air_quality_measurements
                WHERE city = %s AND timestamp >= %s
                ORDER BY timestamp DESC
            """
            
            start_date = datetime.now() - timedelta(days=days)
            df = pd.read_sql_query(query, conn, params=(city, start_date))
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
        finally:
            conn.close()
    
    def save_prediction(self, city: str, predicted_for_date: datetime, model_type: str, 
                       predicted_aqi: float, confidence_score: float = 0.0,
                       prediction_interval_low: float = 0.0, prediction_interval_high: float = 0.0,
                       model_metrics: Dict = None):
        """Save air quality prediction to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO air_quality_predictions 
                (city, prediction_timestamp, predicted_for_date, model_type, predicted_aqi, 
                 prediction_interval_low, prediction_interval_high, confidence_score, model_metrics)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                city,
                datetime.now(),
                predicted_for_date,
                model_type,
                predicted_aqi,
                prediction_interval_low,
                prediction_interval_high,
                confidence_score,
                json.dumps(model_metrics) if model_metrics else None
            ))
            
            conn.commit()
            prediction_id = cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
        
        return prediction_id
    
    def get_recent_predictions(self, city: str, days: int = 7) -> pd.DataFrame:
        """Get recent predictions for a city"""
        conn = self.get_connection()
        
        try:
            query = """
                SELECT city, prediction_timestamp, predicted_for_date, model_type, 
                       predicted_aqi, prediction_interval_low, prediction_interval_high, 
                       confidence_score, model_metrics
                FROM air_quality_predictions
                WHERE city = %s AND prediction_timestamp >= %s
                ORDER BY prediction_timestamp DESC
            """
            
            start_date = datetime.now() - timedelta(days=days)
            df = pd.read_sql_query(query, conn, params=(city, start_date))
            
            return df
        finally:
            conn.close()
    
    def create_alert(self, city: str, alert_type: str, severity: str, aqi_value: float,
                    threshold_exceeded: float, vulnerable_groups: Dict, people_affected: int,
                    health_recommendations: str):
        """Create an air quality alert"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO air_quality_alerts 
                (city, alert_type, severity, aqi_value, threshold_exceeded, 
                 vulnerable_groups, people_affected, health_recommendations, triggered_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                city,
                alert_type,
                severity,
                aqi_value,
                threshold_exceeded,
                json.dumps(vulnerable_groups),
                people_affected,
                health_recommendations,
                datetime.now()
            ))
            
            alert_id = cursor.fetchone()[0]
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
        
        return alert_id
    
    def get_active_alerts(self, city: Optional[str] = None, hours: int = 24) -> pd.DataFrame:
        """Get active alerts for the last N hours"""
        conn = self.get_connection()
        
        try:
            if city:
                query = """
                    SELECT id, city, alert_type, severity, aqi_value, threshold_exceeded,
                           vulnerable_groups, people_affected, health_recommendations, 
                           triggered_at, acknowledged
                    FROM air_quality_alerts
                    WHERE city = %s AND triggered_at >= %s AND acknowledged = FALSE
                    ORDER BY triggered_at DESC
                """
                params = (city, datetime.now() - timedelta(hours=hours))
            else:
                query = """
                    SELECT id, city, alert_type, severity, aqi_value, threshold_exceeded,
                           vulnerable_groups, people_affected, health_recommendations, 
                           triggered_at, acknowledged
                    FROM air_quality_alerts
                    WHERE triggered_at >= %s AND acknowledged = FALSE
                    ORDER BY triggered_at DESC
                """
                params = (datetime.now() - timedelta(hours=hours),)
            
            df = pd.read_sql_query(query, conn, params=params)
            return df
        finally:
            conn.close()
    
    def acknowledge_alert(self, alert_id: int):
        """Mark an alert as acknowledged"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE air_quality_alerts
                SET acknowledged = TRUE
                WHERE id = %s
            """, (alert_id,))
            
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    
    def save_health_impact_report(self, city: str, report_date: datetime, 
                                  health_metrics: Dict, recommendations: str):
        """Save health impact report"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO health_impact_reports 
                (city, report_date, average_aqi, health_risk_score, total_people_at_risk,
                 excess_deaths_annual, excess_illness_cases, economic_impact_inr,
                 vulnerable_populations, recommendations)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (city, report_date) DO UPDATE SET
                    average_aqi = EXCLUDED.average_aqi,
                    health_risk_score = EXCLUDED.health_risk_score,
                    total_people_at_risk = EXCLUDED.total_people_at_risk,
                    excess_deaths_annual = EXCLUDED.excess_deaths_annual,
                    excess_illness_cases = EXCLUDED.excess_illness_cases,
                    economic_impact_inr = EXCLUDED.economic_impact_inr,
                    vulnerable_populations = EXCLUDED.vulnerable_populations,
                    recommendations = EXCLUDED.recommendations
                RETURNING id
            """, (
                city,
                report_date,
                health_metrics.get('average_aqi', 0),
                health_metrics.get('health_risk_score', 0),
                health_metrics.get('total_people_at_risk', 0),
                health_metrics.get('excess_deaths_annual', 0),
                health_metrics.get('excess_respiratory_cases', 0),
                health_metrics.get('economic_impact_inr', 0),
                json.dumps(health_metrics.get('vulnerable_populations', {})),
                recommendations
            ))
            
            report_id = cursor.fetchone()[0]
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
        
        return report_id
    
    def get_health_reports(self, city: Optional[str] = None, days: int = 30) -> pd.DataFrame:
        """Get health impact reports"""
        conn = self.get_connection()
        
        try:
            if city:
                query = """
                    SELECT city, report_date, average_aqi, health_risk_score, 
                           total_people_at_risk, excess_deaths_annual, excess_illness_cases,
                           economic_impact_inr, vulnerable_populations, recommendations
                    FROM health_impact_reports
                    WHERE city = %s AND report_date >= %s
                    ORDER BY report_date DESC
                """
                params = (city, datetime.now().date() - timedelta(days=days))
            else:
                query = """
                    SELECT city, report_date, average_aqi, health_risk_score, 
                           total_people_at_risk, excess_deaths_annual, excess_illness_cases,
                           economic_impact_inr, vulnerable_populations, recommendations
                    FROM health_impact_reports
                    WHERE report_date >= %s
                    ORDER BY report_date DESC
                """
                params = (datetime.now().date() - timedelta(days=days),)
            
            df = pd.read_sql_query(query, conn, params=params)
            return df
        finally:
            conn.close()
    
    def get_data_quality_stats(self, city: str, days: int = 7) -> Dict:
        """Get data quality statistics for a city"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT DATE(timestamp)) as days_with_data,
                    AVG(aqi) as avg_aqi,
                    MAX(aqi) as max_aqi,
                    MIN(aqi) as min_aqi,
                    COUNT(CASE WHEN aqi IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as aqi_completeness,
                    COUNT(CASE WHEN pm25 IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as pm25_completeness,
                    COUNT(DISTINCT data_source) as data_sources
                FROM air_quality_measurements
                WHERE city = %s AND timestamp >= %s
            """, (city, start_date))
            
            row = cursor.fetchone()
            
            stats = {
                'total_records': row[0] if row[0] else 0,
                'days_with_data': row[1] if row[1] else 0,
                'avg_aqi': float(row[2]) if row[2] else 0,
                'max_aqi': float(row[3]) if row[3] else 0,
                'min_aqi': float(row[4]) if row[4] else 0,
                'aqi_completeness': float(row[5]) if row[5] else 0,
                'pm25_completeness': float(row[6]) if row[6] else 0,
                'data_sources': row[7] if row[7] else 0
            }
            
            return stats
        finally:
            cursor.close()
            conn.close()
