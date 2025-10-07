import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import joblib
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import warnings
warnings.filterwarnings('ignore')

class AirQualityPredictor:
    def __init__(self):
        self.rf_model = None
        self.arima_model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.is_trained = False
        
    def prepare_features(self, df):
        """Prepare features for machine learning models"""
        if df.empty:
            return pd.DataFrame()
            
        # Create a copy to avoid modifying original data
        data = df.copy()
        
        # Ensure timestamp is datetime
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data = data.sort_values('timestamp')
        
        # Create time-based features
        data['hour'] = data['timestamp'].dt.hour
        data['day_of_week'] = data['timestamp'].dt.dayofweek
        data['month'] = data['timestamp'].dt.month
        data['day_of_year'] = data['timestamp'].dt.dayofyear
        
        # Create lag features (previous values)
        lag_periods = [1, 3, 6, 12, 24]  # 1, 3, 6, 12, 24 hours ago
        for period in lag_periods:
            for col in ['pm25', 'pm10', 'no2', 'aqi']:
                if col in data.columns:
                    data[f'{col}_lag_{period}'] = data[col].shift(period)
        
        # Create rolling statistics
        window_sizes = [6, 12, 24]  # 6, 12, 24 hour windows
        for window in window_sizes:
            for col in ['pm25', 'pm10', 'no2', 'aqi']:
                if col in data.columns:
                    data[f'{col}_rolling_mean_{window}'] = data[col].rolling(window=window).mean()
                    data[f'{col}_rolling_std_{window}'] = data[col].rolling(window=window).std()
        
        # Weather-related features (simplified - in real implementation would use weather API)
        # For now, create synthetic weather patterns
        data['temp_estimate'] = 25 + 10 * np.sin(2 * np.pi * data['hour'] / 24) + 5 * np.sin(2 * np.pi * data['day_of_year'] / 365)
        data['humidity_estimate'] = 60 + 20 * np.sin(2 * np.pi * (data['hour'] + 6) / 24)
        data['wind_speed_estimate'] = 5 + 3 * np.random.random(len(data))
        
        # Drop rows with NaN values (from lag and rolling operations)
        data = data.dropna()
        
        return data
    
    def train_random_forest(self, df, target_column='aqi'):
        """Train Random Forest model for next-day prediction"""
        try:
            if df.empty:
                raise ValueError("No training data available")
            
            # Prepare features
            processed_data = self.prepare_features(df)
            
            if processed_data.empty:
                raise ValueError("No data available after feature preparation")
            
            # Define feature columns (exclude non-feature columns)
            exclude_cols = ['timestamp', 'location', 'city', 'country', 'latitude', 'longitude']
            self.feature_columns = [col for col in processed_data.columns 
                                  if col not in exclude_cols and col != target_column]
            
            if not self.feature_columns:
                raise ValueError("No feature columns available for training")
            
            # Prepare X and y
            X = processed_data[self.feature_columns].fillna(0)
            y = processed_data[target_column]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train Random Forest
            self.rf_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            
            self.rf_model.fit(X_train_scaled, y_train)
            
            # Make predictions and calculate metrics
            y_pred = self.rf_model.predict(X_test_scaled)
            
            metrics = {
                'mae': mean_absolute_error(y_test, y_pred),
                'mse': mean_squared_error(y_test, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                'r2': r2_score(y_test, y_pred)
            }
            
            self.is_trained = True
            return metrics
            
        except Exception as e:
            raise Exception(f"Error training Random Forest model: {str(e)}")
    
    def train_arima(self, df, target_column='aqi'):
        """Train ARIMA model for time series forecasting"""
        try:
            if df.empty:
                raise ValueError("No training data available")
            
            # Prepare time series data
            data = df.copy()
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data = data.sort_values('timestamp')
            
            # Resample to hourly data and forward fill
            data.set_index('timestamp', inplace=True)
            ts_data = data[target_column].resample('H').mean().fillna(method='ffill')
            
            if len(ts_data) < 48:  # Need at least 2 days of data
                raise ValueError("Insufficient data for ARIMA training (need at least 48 hours)")
            
            # Fit ARIMA model (using auto-selected parameters for simplicity)
            # In production, would use auto_arima or grid search
            self.arima_model = ARIMA(ts_data, order=(2, 1, 2))
            fitted_model = self.arima_model.fit()
            
            # Calculate metrics on training data
            predictions = fitted_model.fittedvalues
            actuals = ts_data[1:]  # Skip first value (differenced)
            
            if len(predictions) != len(actuals):
                # Align predictions with actuals
                min_len = min(len(predictions), len(actuals))
                predictions = predictions[:min_len]
                actuals = actuals[:min_len]
            
            metrics = {
                'mae': mean_absolute_error(actuals, predictions),
                'mse': mean_squared_error(actuals, predictions),
                'rmse': np.sqrt(mean_squared_error(actuals, predictions)),
                'aic': fitted_model.aic,
                'bic': fitted_model.bic
            }
            
            self.arima_fitted = fitted_model
            return metrics
            
        except Exception as e:
            raise Exception(f"Error training ARIMA model: {str(e)}")
    
    def predict_next_day_rf(self, current_data):
        """Make next-day prediction using Random Forest"""
        try:
            if not self.is_trained or self.rf_model is None:
                raise ValueError("Random Forest model not trained")
            
            if current_data.empty:
                raise ValueError("No current data for prediction")
            
            # Prepare features for the latest data point
            processed_data = self.prepare_features(current_data)
            
            if processed_data.empty:
                raise ValueError("No data available after feature preparation")
            
            # Get the latest row
            latest_data = processed_data.iloc[-1:][self.feature_columns].fillna(0)
            
            # Scale features
            latest_scaled = self.scaler.transform(latest_data)
            
            # Make prediction
            prediction = self.rf_model.predict(latest_scaled)[0]
            
            # Get feature importance
            if self.feature_columns is not None:
                feature_importance = dict(zip(
                    self.feature_columns,
                    self.rf_model.feature_importances_
                ))
                
                # Sort by importance
                sorted_items = sorted(
                    feature_importance.items(),
                    key=lambda x: float(x[1]) if isinstance(x[1], (int, float)) else 0,
                    reverse=True
                )
                feature_importance = dict(sorted_items)
            else:
                feature_importance = {}
            
            return {
                'predicted_aqi': max(0, prediction),  # Ensure non-negative
                'feature_importance': feature_importance,
                'prediction_interval': [max(0, prediction - 25), prediction + 25]  # Simple confidence interval
            }
            
        except Exception as e:
            raise Exception(f"Error making Random Forest prediction: {str(e)}")
    
    def predict_next_day_arima(self, steps=24):
        """Make next-day prediction using ARIMA"""
        try:
            if not hasattr(self, 'arima_fitted') or self.arima_fitted is None:
                raise ValueError("ARIMA model not trained")
            
            # Forecast next 24 hours
            forecast_result = self.arima_fitted.forecast(steps=steps)
            
            if hasattr(forecast_result, 'predicted_mean'):
                predictions = forecast_result.predicted_mean
                conf_int = forecast_result.conf_int() if hasattr(forecast_result, 'conf_int') else None
            else:
                predictions = forecast_result
                conf_int = None
            
            # Calculate average for next day
            next_day_avg = predictions.mean()
            
            # Create hourly predictions
            hourly_predictions = []
            for i, pred in enumerate(predictions):
                hourly_predictions.append({
                    'hour': i + 1,
                    'predicted_aqi': max(0, pred),
                    'lower_bound': max(0, conf_int.iloc[i, 0]) if conf_int is not None else max(0, pred - 20),
                    'upper_bound': conf_int.iloc[i, 1] if conf_int is not None else pred + 20
                })
            
            return {
                'next_day_average': max(0, next_day_avg),
                'hourly_predictions': hourly_predictions,
                'model_summary': {
                    'aic': self.arima_fitted.aic,
                    'bic': self.arima_fitted.bic,
                    'log_likelihood': self.arima_fitted.llf
                }
            }
            
        except Exception as e:
            raise Exception(f"Error making ARIMA prediction: {str(e)}")
    
    def get_model_performance(self):
        """Get model performance metrics"""
        if not self.is_trained:
            return {"error": "Models not trained yet"}
        
        performance = {}
        
        if self.rf_model is not None:
            performance['random_forest'] = {
                'model_type': 'Random Forest',
                'n_estimators': self.rf_model.n_estimators,
                'max_depth': self.rf_model.max_depth,
                'n_features': len(self.feature_columns) if self.feature_columns else 0
            }
        
        if hasattr(self, 'arima_fitted') and self.arima_fitted is not None:
            performance['arima'] = {
                'model_type': 'ARIMA',
                'order': self.arima_fitted.model.order,
                'aic': self.arima_fitted.aic,
                'bic': self.arima_fitted.bic
            }
        
        return performance
    
    def save_models(self, filepath_prefix="air_quality_models"):
        """Save trained models"""
        try:
            if self.rf_model is not None:
                joblib.dump(self.rf_model, f"{filepath_prefix}_rf.pkl")
                joblib.dump(self.scaler, f"{filepath_prefix}_scaler.pkl")
            
            if hasattr(self, 'arima_fitted') and self.arima_fitted is not None:
                self.arima_fitted.save(f"{filepath_prefix}_arima.pkl")
            
            return True
        except Exception as e:
            print(f"Error saving models: {e}")
            return False
    
    def load_models(self, filepath_prefix="air_quality_models"):
        """Load pre-trained models"""
        try:
            # Load Random Forest
            try:
                self.rf_model = joblib.load(f"{filepath_prefix}_rf.pkl")
                self.scaler = joblib.load(f"{filepath_prefix}_scaler.pkl")
                self.is_trained = True
            except:
                pass
            
            # Load ARIMA
            try:
                from statsmodels.tsa.arima.model import ARIMAResults
                self.arima_fitted = ARIMAResults.load(f"{filepath_prefix}_arima.pkl")
            except:
                pass
            
            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            return False
