import warnings
warnings.filterwarnings("ignore")

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from functools import lru_cache
import math

class PolarMLRiskModel:
    """
    High-Performance ML Risk Model for Antarctic Navigation.
    Uses RandomForestRegressor with Spatial Memoization for zero-latency routing.
    """
    def __init__(self):
        # 15 trees + depth 5 keeps inference blazing fast
        self.model = RandomForestRegressor(n_estimators=15, max_depth=5, random_state=42, n_jobs=1)
        self._train_initial_model()

    def _generate_polar_dataset(self, n_samples=800):
        np.random.seed(42)
        lats = np.random.uniform(-82.0, -55.0, n_samples)
        lons = np.random.uniform(-180.0, 180.0, n_samples)
        months = np.random.randint(1, 13, n_samples)
        
        surface_temps = -2.0 + (lats + 55.0) * 0.25 - np.cos((months - 1) * math.pi / 6.0) * 3.5
        wind_speeds = np.random.uniform(10.0, 45.0, n_samples) + np.abs(lats + 60.0) * 0.4
        
        X = np.column_stack([lats, lons, months, surface_temps, wind_speeds])
        
        y = []
        for lat, lon, m, t, w in X:
            base_ice = np.clip((-55.0 - lat) / 25.0, 0.0, 1.0)
            seasonal_freeze = 0.25 * max(0.0, np.cos((m - 8) * math.pi / 6.0))
            temp_penalty = 0.20 if t < -1.5 else 0.05
            weddell = 0.25 * math.exp(-((lat - -72.0)**2 / 40.0 + (lon - -45.0)**2 / 600.0))
            
            target_risk = np.clip(base_ice * 0.6 + seasonal_freeze + temp_penalty + weddell, 0.0, 1.0)
            y.append(target_risk)

        return X, np.array(y)

    def _train_initial_model(self):
        X_train, y_train = self._generate_polar_dataset()
        self.model.fit(X_train, y_train)
        print(" [ML ENGINE] Polar Random Forest Regressor ready (Optimized for instant routing).")

    @lru_cache(maxsize=8192)
    def _cached_predict(self, lat_r: float, lon_r: float, month: int) -> float:
        est_temp = -2.0 + (lat_r + 55.0) * 0.25
        est_wind = 25.0 + abs(lat_r + 60.0) * 0.3
        vec = np.array([[lat_r, lon_r, month, est_temp, est_wind]])
        return float(self.model.predict(vec)[0])

    def predict_environmental_risk(self, lat: float, lon: float, month: int = 11) -> float:
        """Returns ML risk score instantly with spatial grid caching."""
        # Rounding to 1 decimal place prevents duplicate ML evaluations
        lat_r = round(float(lat), 1)
        lon_r = round(float(lon), 1)
        pred = self._cached_predict(lat_r, lon_r, int(month))
        return float(np.clip(pred, 0.0, 1.0))