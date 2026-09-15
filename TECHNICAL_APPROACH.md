# IndraSetu Technical Approach, Workflow, ML Architecture, and Dataset Guide

This document explains the current repository as inspected on 2026-09-12. It covers the runtime application, user workflow, machine learning pipelines, dataset structure, generated artifacts, scripts, and implementation boundaries.

## 1. Executive Summary

IndraSetu is an Antarctic maritime decision support prototype. It combines:

- Satellite sea-ice concentration observations.
- A ConvLSTM sea-ice forecast model.
- Historical iceberg trajectory data and GRU-based iceberg drift forecasting.
- Live or fallback MetOcean conditions.
- Dynamic hazards injected during an underway voyage.
- A risk engine that normalizes hazards into a common 0 to 1 risk score.
- A route engine that uses A* search to produce safest, balanced, and fuel-efficient routes.
- A browser dashboard that visualizes the operating environment and simulates rerouting.

The product is designed for route planning and mission review. It is not a certified navigation system, not a replacement for official charts, and not a substitute for human voyage command decisions.

## 2. Repository Map

The repository is organized around one runtime app and two ML workspaces.

| Path | Role |
| --- | --- |
| `run.py` | Starts the FastAPI/Uvicorn runtime on `127.0.0.1:8000`. |
| `requirements.txt` | Python dependencies for API, ML, geospatial processing, testing, and plotting. |
| `evaluate_model.py` | Evaluates the synthetic Random Forest risk fallback model. |
| `ARCHITECTURE.md` | Existing high-level architecture document. This file expands it with dataset and script-level detail. |
| `.gitattributes` | Configures Git LFS for zip archives. |
| `frontend/index.html` | Single-page Leaflet dashboard, styling, map logic, route rendering, evaluation modal, simulation, and rerouting UI. |
| `backend/` | FastAPI composition root and runtime services. |
| `Sea ice prediction/` | Sea-ice raw data, processed arrays, ConvLSTM model code, checkpoints, risk-grid scripts, route optimizer, and generated outputs. |
| `iceberg trajectory/` | Iceberg raw CSV database, processed trajectory features, GRU code, checkpoints, predictions, risk grid, and helper scripts. |
| `tests/` | API and service tests for route evaluation, rerouting, hazards, and sea-ice forecast endpoint. |
| `iceberg trajectory.zip` | Archive of the iceberg trajectory workspace. |
| `Sea ice prediction (2).zip` | Archive of the sea-ice workspace. |
| `.venv/`, `__pycache__/`, `.pytest_cache/` | Local environment and generated caches. These are not source artifacts. |
| `Program Files/` | Empty directory in the workspace at inspection time. |

Approximate project file inventory, excluding `.git`, `.venv`, `__pycache__`, and `.pytest_cache`:

| File type | Count | Meaning |
| --- | ---: | --- |
| `.nc` | 5,442 | Raw NSIDC sea-ice NetCDF files. |
| `.csv` | 666 | Iceberg raw tracks, processed trajectory files, risk outputs, route outputs, and evaluation summaries. |
| `.py` | 42 | Backend, tests, ML scripts, and helpers. |
| `.npy` | 25 | Processed tensors and sequence datasets. |
| `.png` | 5 | Sea-ice and route visualizations. |
| `.pt` | 5 | PyTorch checkpoints. |
| `.npz` | 4 | Compressed navigation/risk grid artifacts. |
| `.txt` / `.TXT` | 3 | Requirements, iceberg database README, and a prior output log. |
| `.zip` | 2 | Archived dataset/workspace bundles. |

## 3. Runtime Architecture

At runtime the system is a single FastAPI backend serving a single HTML dashboard.

```text
Operator
  -> frontend/index.html
  -> FastAPI backend/main.py
  -> RouteEngine
  -> RiskEngine
  -> SeaIceService / SeaIceMLService / IcebergService / IcebergMLService / LiveEnvironmentService
  -> Local arrays, checkpoints, CSV predictions, Open-Meteo fallback path
```

The runtime is intentionally local and lightweight:

- `run.py` starts Uvicorn.
- `backend/main.py` creates all services once at import/startup time.
- The frontend is served at `/`.
- Frontend requests JSON from `/api/...` endpoints.
- The backend keeps dynamic hazards and forecast state in memory.
- Processed datasets and checkpoints are read from local disk.

## 4. Backend Runtime Files

| File | Technical responsibility |
| --- | --- |
| `backend/main.py` | FastAPI application, CORS, request schemas, endpoint wiring, and HTML dashboard serving. |
| `backend/sea_ice_service.py` | Loads real processed satellite arrays when present and exposes point concentration, heatmap points, and demo GeoJSON ice zones. Falls back to a deterministic polar ice model if data is missing. |
| `backend/sea_ice_ml.py` | Loads `SeaIceConvLSTM` and `best_model.pt`, prepares a masked 7-day sequence, resizes to 128 x 128, runs forecast inference, and provides nearest-cell sea-ice risk lookup. |
| `backend/iceberg_service.py` | Loads GRU prediction CSV output, selects latest target-date predictions, calculates iceberg speed/bearing, and returns proximity risk against forecast iceberg positions. |
| `backend/iceberg_ml_service.py` | Loads trajectory features and `iceberg_gru_72h_best.pt`, predicts featured iceberg trajectories for map display, and applies observed-motion continuity correction if the model underpredicts recent movement. |
| `backend/live_data_service.py` | Fetches live Open-Meteo weather data with a 1.5 second timeout, converts wind/visibility/pressure into maritime fields, derives wave height, caches by rounded coordinate for 5 minutes, and falls back to deterministic polar MetOcean synthesis. Also stores dynamic hazards in memory. |
| `backend/risk_engine.py` | Combines sea-ice, iceberg, weather, dynamic hazard, and vessel class into one composite risk score. |
| `backend/route_engine.py` | Runs A* route search on a rounded Antarctic coordinate lattice, computes profile metrics, checks cyclone signatures, supports en-route rerouting, and builds route evaluation reports. |
| `backend/ml_risk_model.py` | Trains a small synthetic Random Forest regressor at startup for fallback point-risk inference if the sea-ice ML service is unavailable. |

## 5. API Contract

| Endpoint | Method | Request | Response purpose |
| --- | --- | --- | --- |
| `/` | GET | None | Serves `frontend/index.html`. |
| `/api/environment/layers` | GET | None | Returns sea-ice GeoJSON zones, featured GRU iceberg trajectories, active dynamic hazards, and a data notice. |
| `/api/sea-ice/heatmap` | GET | `date`, `stride` query params | Returns satellite sea-ice heatmap points `[lat, lon, concentration]`, observation date, concentration stats, and estimated ice extent. |
| `/api/live/environmental-data` | GET | `lat`, `lon` query params | Returns MetOcean data plus risk breakdown for a coordinate. |
| `/api/live/hazard/trigger` | POST | `lat`, `lon`, `hazard_type`, `radius_nm`, `severity`, `description` | Adds a dynamic hazard and returns it. |
| `/api/sea-ice/forecast` | POST | `forecast_date` | Runs or retrieves sea-ice forecast and returns min/max/mean at 128 x 128 resolution. |
| `/api/routes/calculate` | POST | start, destination, departure date, vessel type | Returns safest, balanced, and fuel-efficient route alternatives. |
| `/api/routes/reroute` | POST | current position, destination, vessel type, active profile, traveled waypoints | Recalculates remaining route from current vessel position. |
| `/api/routes/evaluate` | POST | route waypoints, vessel type, profile name, optional departure date | Returns voyage performance index, fuel, cost, emissions, hull stress, average risks, and segment breakdown. |

## 6. User Workflow

### 6.1 Start The System

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the app:

```bash
python run.py
```

3. Open:

```text
http://127.0.0.1:8000
```

### 6.2 Dashboard Initialization

When the page loads, `frontend/index.html`:

- Creates a Leaflet map centered on Antarctic waters.
- Adds Esri dark map tiles.
- Creates Leaflet layer groups for routes, environment layers, dynamic hazards, and sea-ice heatmap.
- Calls `/api/environment/layers`.
- Calls `/api/sea-ice/heatmap`.
- Registers browser online/offline listeners.
- Keeps cached environment, heatmap, and route data in `localStorage` with `polar_cache_...` keys.

### 6.3 Inspect The Operating Environment

The operator can:

- Toggle the Gaussian sea-ice heatmap.
- Switch between thermal and polar heatmap palettes.
- View sea-ice zones.
- View featured iceberg trajectories.
- View active hazard circles.
- Click any Antarctic map coordinate to call `/api/live/environmental-data`.

The click popup shows:

- Sea-ice concentration risk.
- Iceberg danger.
- Wind/wave risk.
- Coordinate label.

### 6.4 Generate Routes

The operator selects:

- Origin port: Punta Arenas, Ushuaia, Lyttelton, or Cape Town.
- Destination base: Palmer, McMurdo, Zhongshan, or Neumayer III.
- Departure date.
- Vessel class: `Polar Class 1`, `Polar Class 4`, or `Ice 1C`.

Then `runOptimization()` posts to `/api/routes/calculate`. The backend runs three A* searches:

- Safest.
- Balanced.
- Fuel Efficient.

The dashboard renders the routes as colored Leaflet polylines and fills route cards with:

- Overall risk score.
- Distance in nautical miles.
- Estimated time in days.
- Estimated fuel in metric tons.
- Profile explanation.

### 6.5 Evaluate A Route

The operator opens the full route evaluation report. The frontend posts active waypoints to `/api/routes/evaluate`. The response fills a modal with:

- Voyage Performance Index.
- Fuel and estimated cost.
- CO2 footprint.
- Hull stress index.
- Tactical briefing.
- Segment-level risk table.

### 6.6 Simulate An Underway Voyage

The operator starts voyage simulation after routes exist. The frontend:

- Shows the underway HUD.
- Places a vessel marker at the first waypoint.
- Advances one waypoint every 2.5 seconds.
- Updates current position, ETA approximation, compass heading, wind, waves, sea ice, and forward risk.
- Starts a 60 second reroute watchdog.

### 6.7 Dynamic Hazard And Rerouting

The operator can inject a dynamic hazard during simulation. The frontend posts to `/api/live/hazard/trigger`, reloads environment layers, and asks for reroute evaluation.

The watchdog or manual reroute button posts to `/api/routes/reroute`. If current cell risk is above 45%, the UI displays a hazard alert and stores the proposed reroute. When the operator accepts the detour, the remaining route polyline is replaced with `full_voyage_waypoints`.

## 7. Risk Fusion Approach

The runtime risk model uses component scores on a 0 to 1 scale.

### 7.1 Sea-Ice Risk

Sea-ice risk comes from:

- `SeaIceMLService.get_risk_at()` when the ConvLSTM service is available.
- `PolarMLRiskModel.predict_environmental_risk()` if no sea-ice ML service is attached.
- `SeaIceService.get_ice_concentration()` for observation and heatmap behavior.

The ML service treats no-data or land-mask cells as maximum risk for routing.

### 7.2 Iceberg Risk

`IcebergService.get_iceberg_risk_at()` measures distance to predicted iceberg positions from `test_predictions.csv`.

```text
risk radius = 2.5 deg * 111 km ~= 277.5 km
iceberg risk = max(0, 1 - distance_km / risk_radius_km)
```

The gridded offline iceberg risk script uses Gaussian influence around predicted positions:

```text
local risk = exp(-0.5 * (distance / radius)^2)
```

with a 24 hour radius of 30 km in the current script.

### 7.3 Weather Risk

`LiveEnvironmentService` returns wind, wave, visibility, temperature, pressure, and direction. Weather risk is calculated in `RiskEngine.get_weather_risk()`:

```text
wind penalty = min(1, wind_knots / 50)
wave penalty = min(1, wave_height_m / 8)
visibility penalty = max(0, 1 - visibility_km / 15)
storm belt = exp(-((lat - -60)^2) / 18)
weather risk = clamp(storm_belt * 0.4
                   + 0.3 * wind penalty
                   + 0.2 * wave penalty
                   + 0.1 * visibility penalty,
                   lower=0.1,
                   upper=1.0)
```

Open-Meteo is used as the live source where reachable. Wave height is currently derived from wind speed, not fetched from a marine wave endpoint.

### 7.4 Dynamic Hazard Risk

Dynamic hazards are circular. Distance is approximated in degrees and converted to nautical miles:

```text
adjusted dlon = wrapped_lon_delta * cos(lat)
distance_nm = sqrt(dlat^2 + adjusted_dlon^2) * 60
hazard risk = severity * (1 - distance_nm / radius_nm)
```

Only the maximum active hazard contribution is used at a point.

### 7.5 Vessel Factor

`RiskEngine.calculate_cell_risk()` adjusts raw risk by vessel capability:

| Vessel string contains | Factor |
| --- | ---: |
| `Class 1` | 0.45 |
| `Class 4` | 0.75 |
| `Standard` | 1.35 |
| Other values | 1.00 |

The frontend currently sends `Ice 1C` for one option. That string receives the default factor of `1.00` because the backend does not have an explicit `Ice 1C` branch.

### 7.6 Composite Risk Formula

Runtime risk fusion:

```text
raw risk = (0.40 * sea_ice_risk
          + 0.25 * iceberg_risk
          + 0.15 * weather_risk
          + 0.20 * dynamic_hazard_risk) * vessel_factor

total risk = clamp(raw risk, 0, 1)
```

The API returns:

- `total_risk`
- `sea_ice_risk`
- `iceberg_risk`
- `weather_risk`
- `dynamic_hazard_risk`

Note that `iceberg_risk` in the response is `max(static_iceberg_risk, dynamic_hazard_risk)` for display, while `dynamic_hazard_risk` is also reported separately.

## 8. Runtime Route Engine

`backend/route_engine.py` performs live API routing on a coarse Antarctic coordinate lattice.

### 8.1 A* Search Grid

| Setting | Value |
| --- | ---: |
| Latitude step | 1.5 deg |
| Longitude step | 3.0 deg |
| Latitude bounds | -82 to -50 |
| Longitude handling | Wrapped to -180 to 180 |
| Neighbor directions | 8-connected grid |
| Max visited nodes | 2,500 |
| Destination acceptance | Within 120 nautical miles of rounded destination |
| Distance function | Haversine, Earth radius 3440.065 nautical miles |

### 8.2 Edge Cost

For each candidate neighbor:

```text
edge cost = segment_distance_nm
          * (1 + route_profile_risk_weight * total_risk^2 * 8)
```

The squared risk term heavily penalizes high-risk cells.

### 8.3 Route Profiles

| Runtime profile | Risk weight | Design intent |
| --- | ---: | --- |
| Safest | 15.0 | Strongly avoids ice, iceberg, weather, and dynamic hazard exposure. |
| Balanced | 3.5 | Trades extra distance for lower risk. |
| Fuel Efficient | 0.2 | Stays closer to short route, accepting higher exposure. |

### 8.4 Route Metrics

Distance-weighted risk:

```text
average risk = sum(segment_risk * segment_distance) / total_distance
```

Speed and fuel:

```text
base speed = 12 kt for Class 1, 14 kt for Class 4, 15 kt for Standard/other
effective speed = base_speed * (1 - 0.45 * average_risk)
estimated hours = distance_nm / max(effective_speed, 4)
fuel rate = 1.0 * (1 + 0.6 * average_risk)
fuel metric tons = estimated_hours * fuel_rate
```

### 8.5 Route Evaluation Metrics

`evaluate_route()` calculates:

```text
fuel cost USD = fuel_mt * 650
CO2 emissions mt = fuel_mt * 3.114
hull stress index = 1 + 2.5 * average_sea_ice_risk
high-risk corridor ratio = high_risk_distance / total_distance * 100
VPI = clamp(100 - 0.45 * average_risk * 100 - 0.003 * total_distance_nm,
            lower=10,
            upper=99)
```

Segment risk tiers:

| Total segment risk | Tier |
| ---: | --- |
| `> 0.50` | `HIGH HAZARD` |
| `> 0.25` | `MODERATE EXPOSURE` |
| otherwise | `LOW RISK` |

## 9. Frontend Technical Approach

`frontend/index.html` is a single-file app. It contains:

- HTML layout.
- CSS theme and responsive behavior.
- Leaflet map setup.
- Heatmap rendering through `leaflet-heat`.
- API calls through `fetch`.
- Offline resilience through `localStorage`.
- Route rendering and route profile selection.
- Voyage simulation timer.
- Dynamic hazard injection.
- Automatic and manual rerouting calls.
- Route evaluation modal.

Important frontend functions:

| Function | Role |
| --- | --- |
| `initMap()` | Creates map, tile layers, environment layers, heatmap, and map-click inspector. |
| `loadSeaIceHeatmap()` | Fetches `/api/sea-ice/heatmap`, caches data, and calls renderer. |
| `renderSeaIceHeatmap()` | Converts `[lat, lon, concentration]` points to a Leaflet heat layer. |
| `loadEnvironment()` | Fetches `/api/environment/layers` or uses cached environment data. |
| `renderEnvLayers()` | Renders sea-ice polygons, iceberg markers/trajectories, and dynamic hazard circles. |
| `runOptimization()` | Posts route request and stores current route alternatives. |
| `renderRoutes()` | Draws route polylines and fills result cards. |
| `highlightRoute()` | Makes a route active visually and logically. |
| `openRouteEvaluation()` | Posts active route to evaluation endpoint and fills modal metrics. |
| `startVoyageSimulation()` | Begins waypoint stepping and the reroute watchdog. |
| `performPeriodicRerouteCheck()` | Posts current position to reroute endpoint and raises alert if risk is high. |
| `simulateDynamicHazard()` | Injects a hazard ahead of the vessel and refreshes layers. |
| `acceptDynamicReroute()` | Applies proposed detour to the active route polyline. |

## 10. Sea-Ice Dataset

### 10.1 Raw Data

Raw sea-ice data lives under:

```text
Sea ice prediction/data/raw/NSIDC-0079_4-20260827_172653/
```

Inventory:

| Category | Count |
| --- | ---: |
| Total NetCDF files | 5,442 |
| Southern hemisphere files matching `*S25km*.nc` | 2,722 |
| Northern hemisphere files matching `*N25km*.nc` | 2,720 |

The preprocessing script uses only files matching `*S25km*.nc`.

Example first southern file:

```text
NSIDC0079_SEAICE_PS_S25km_20180813_v4.0.nc
```

Example latest southern files include:

```text
NSIDC0079_SEAICE_PS_S25km_20251101_v4.0.nc
NSIDC0079_SEAICE_PS_S25km_202511_v4.0.nc
```

The inspected NetCDF schema:

| Field | Value |
| --- | --- |
| Dimensions | `time: 1`, `y: 332`, `x: 316` |
| Coordinates | `time`, `y`, `x` |
| Main variable | `F17_ICECON` |
| Main variable shape | `(1, 332, 316)` |
| Main variable dtype | `float64` in the raw NetCDF sample |
| CRS variable | `crs` |

`preprocess.py` converts the projected x/y grid from EPSG:3412 to latitude/longitude using `pyproj.Transformer`.

### 10.2 Processed Sea-Ice Arrays

Processed sea-ice arrays live under:

```text
Sea ice prediction/data/processed/
```

| File | Shape | Dtype | Meaning |
| --- | ---: | --- | --- |
| `sic.npy` | `(2636, 332, 316)` | `float32` | Full sea-ice concentration tensor. |
| `dates.npy` | `(2636,)` | `datetime64[ns]` | Observation dates for `sic.npy`. |
| `train_sic.npy` | `(1845, 332, 316)` | `float32` | Chronological training split. |
| `train_dates.npy` | `(1845,)` | `datetime64[ns]` | Training dates: 2018-08-13 to 2023-09-02. |
| `val_sic.npy` | `(395, 332, 316)` | `float32` | Validation split. |
| `val_dates.npy` | `(395,)` | `datetime64[ns]` | Validation dates: 2023-09-03 to 2024-10-01. |
| `test_sic.npy` | `(396, 332, 316)` | `float32` | Test split. |
| `test_dates.npy` | `(396,)` | `datetime64[ns]` | Test dates: 2024-10-02 to 2025-11-01. |
| `lat.npy` | `(332, 316)` | `float32` | Latitude grid, about -89.84 to -39.36. |
| `lon.npy` | `(332, 316)` | `float32` | Longitude grid, about -179.82 to 179.82. |
| `x.npy` | `(316,)` | `float64` | Projected x-axis values. |
| `y.npy` | `(332,)` | `float64` | Projected y-axis values. |

The full processed date range is 2018-08-13 to 2025-11-01. There is one non-daily gap in the processed sequence:

```text
2019-04-15 to 2019-04-18: 3 days
```

Sequence builders skip windows with non-consecutive days.

### 10.3 Sea-Ice Preprocessing

`Sea ice prediction/src/preprocess.py`:

1. Recursively finds raw files matching `*S25km*.nc`.
2. Opens each file with xarray.
3. Selects the first data variable whose name contains `ICECON`, ignoring `crs`.
4. Reads `time=0`.
5. Casts to `float32`.
6. Sets values outside 0 to 1 as `NaN`.
7. Stores x and y coordinate vectors from the first valid dataset.
8. Sorts all records by date.
9. Removes duplicate dates.
10. Stacks maps into `sic.npy`.
11. Saves date, x/y, and transformed lat/lon arrays.

### 10.4 Sea-Ice Train/Validation/Test Split

`Sea ice prediction/src/split.py` applies a chronological split:

| Split | Fraction | Count |
| --- | ---: | ---: |
| Train | 70% | 1,845 frames |
| Validation | 15% | 395 frames |
| Test | 15% | 396 frames |

This prevents future observations from leaking into training.

## 11. Sea-Ice ML Architecture

### 11.1 Dataset Class

`Sea ice prediction/src/dataset.py` defines `SeaIceDataset`.

Input construction:

- Load `sic.npy` and date array with NumPy.
- Find valid indices where the next 7 gaps are exactly 1 day.
- For each item, load an 8-frame window.
- The first 7 frames are input.
- The 8th frame is the target.
- Build a validity mask from finite pixels.
- Replace `NaN`, `+inf`, and `-inf` with 0 for tensor math.
- Resize values and masks to 128 x 128.
- Return `(x, y, mask)`.

Shapes returned:

```text
x:    (7, 1, 128, 128)
y:    (1, 128, 128)
mask: (1, 128, 128)
```

### 11.2 ConvLSTM Model

`Sea ice prediction/src/model.py` defines:

- `ConvLSTMCell`
- `SeaIceConvLSTM`

The current model is a residual next-frame predictor:

```text
input:      (batch, 7, 1, 128, 128)
layer 1:    ConvLSTMCell, input channels 1, hidden channels 16
layer 2:    ConvLSTMCell, input channels 16, hidden channels 16
head:       1 x 1 Conv2d from 16 channels to 1 channel
output:     clamp(last_input_frame + predicted_delta, 0, 1)
parameters: 28,369
```

Each ConvLSTM cell concatenates current input and hidden state, then applies a 3 x 3 convolution to produce input, forget, output, and candidate gates.

### 11.3 Sea-Ice Training

`Sea ice prediction/src/train.py`:

| Setting | Value |
| --- | ---: |
| Sequence length | 7 days |
| Epoch limit | 20 |
| Batch size | 2 |
| Optimizer | AdamW |
| Learning rate | 0.001 |
| Weight decay | 0.00001 |
| Hidden channels | 16 |
| Loss | Validity-masked MSE |
| Mixed precision | Enabled on CUDA |
| Checkpoint criterion | Lowest validation loss |

Masked MSE:

```text
loss = sum((prediction - target)^2 * mask) / max(sum(mask), 1)
```

Checkpoints found:

| File | Validation loss |
| --- | ---: |
| `Sea ice prediction/checkpoints/best_model.pt` | 0.0006938815 |
| `Sea ice prediction/checkpoints/best_model_before_nanfix.pt` | 0.0006912054 |
| `Sea ice prediction/checkpoints/best_model_before_residual.pt` | 0.0007102016 |

The runtime uses `best_model.pt`.

### 11.4 Sea-Ice Evaluation And Visualization

`Sea ice prediction/src/evaluate.py`:

- Loads test dataset.
- Loads `best_model.pt`.
- Runs model inference.
- Computes pixel MAE and RMSE under the validity mask.
- Computes a persistence baseline using the previous observed frame.
- Reports percentage change versus persistence.

`Sea ice prediction/src/baseline.py`:

- Computes persistence-only MAE and RMSE on consecutive test observations.

`Sea ice prediction/src/visualise_prediction.py`:

- Prompts for a date.
- Builds the 7-day input window.
- Runs model prediction.
- Plots observed SIC, predicted SIC, and absolute error.
- Saves a PNG under `Sea ice prediction/outputs/`.

Generated visualization files:

- `sea_ice_prediction.png`
- `sea_ice_prediction_2024-11-13.png`
- `sea_ice_prediction_2025-10-04.png`

## 12. Sea-Ice Risk And Offline Navigation Scripts

These scripts are a batch/offline pipeline separate from the live FastAPI route engine.

### 12.1 `seaice_to_risk.py`

Purpose:

- Load test sea-ice data, dates, lat/lon, and ConvLSTM checkpoint.
- Prompt for a forecast start date.
- Build the 7-day input sequence.
- Predict next-day sea-ice concentration.
- Resize the geographic grid to 128 x 128.
- Treat predicted concentration as continuous sea-ice risk.
- Classify risk:

| Risk value | Class |
| ---: | ---: |
| `< 0.15` | 0 |
| `0.15 to < 0.40` | 1 |
| `0.40 to < 0.70` | 2 |
| `>= 0.70` | 3 |

Generated artifact inspected:

```text
Sea ice prediction/outputs/seaice/seaice_navigation_risk.npz
```

Keys and stats:

| Key | Shape | Notes |
| --- | ---: | --- |
| `sic` | `(128, 128)` | Min 0.000547, max 0.992943, mean 0.241504. |
| `risk` | `(128, 128)` | Same as SIC. |
| `risk_class` | `(128, 128)` | Integer class 0 to 3. |
| `latitude` | `(128, 128)` | Resized grid. |
| `longitude` | `(128, 128)` | Resized grid. |
| `forecast_date` | scalar | `2025-10-12T00:00:00.000000000`. |
| `input_start` | scalar | `2025-10-05T00:00:00.000000000`. |
| `input_end` | scalar | `2025-10-11T00:00:00.000000000`. |

Also generated:

```text
Sea ice prediction/outputs/seaice/seaice_navigation_risk.csv
```

with 16,384 rows and columns `latitude`, `longitude`, `sic`, `risk`, `risk_class`.

### 12.2 `iceberg_to_risk.py`

Purpose:

- Load GRU iceberg prediction CSV from `iceberg trajectory/outputs/iceberg/test_predictions.csv`.
- Filter to a requested target date.
- Resize the sea-ice lat/lon grid to 128 x 128.
- Create an iceberg risk field around predicted iceberg positions.
- Save `.npz` and flattened `.csv` outputs.

Configuration:

| Horizon | Radius km | Weight |
| ---: | ---: | ---: |
| 24 h | 30 | 1.00 |
| 48 h | 40 | 0.75 |
| 72 h | 50 | 0.50 |

The current implementation uses the one-step `predicted_lat` and `predicted_lon` columns from `test_predictions.csv`, so the active risk grid is effectively 24 hour risk.

Generated artifact inspected:

```text
iceberg trajectory/outputs/iceberg/iceberg_navigation_risk.npz
```

Keys and stats:

| Key | Shape | Notes |
| --- | ---: | --- |
| `risk` | `(128, 128)` | Min 0, max 0.945976, mean 0.000349. |
| `risk_class` | `(128, 128)` | Integer class 0 to 3. |
| `iceberg_count` | `(128, 128)` | Count of iceberg influence per cell. |
| `latitude` | `(128, 128)` | Resized grid. |
| `longitude` | `(128, 128)` | Resized grid. |
| `forecast_date` | scalar | `2026-04-19`. |

### 12.3 `build_composite_risk.py`

Purpose:

- Load sea-ice and iceberg risk grids.
- Validate shape and coordinate alignment.
- Combine them into a composite risk grid.

Formula:

```text
composite_risk = 0.60 * seaice_risk + 0.40 * iceberg_risk
```

Generated artifact inspected:

```text
Sea ice prediction/outputs/navigation/composite_navigation_risk.npz
```

Stats:

| Key | Shape | Notes |
| --- | ---: | --- |
| `risk` | `(128, 128)` | Min 0.000328, max 0.994134, mean 0.180467. |
| `seaice_risk` | `(128, 128)` | Mean 0.241504. |
| `iceberg_risk` | `(128, 128)` | Mean 0.088911 in this composite artifact. |
| `risk_class` | `(128, 128)` | Integer class 0 to 3. |
| `latitude` / `longitude` | `(128, 128)` | Shared route grid. |

Also generated:

```text
Sea ice prediction/outputs/navigation/composite_navigation_risk.csv
```

with 16,384 rows and columns `latitude`, `longitude`, `seaice_risk`, `iceberg_risk`, `composite_risk`, `risk_class`.

### 12.4 `build_navigation_mask.py`

Purpose:

- Load `test_sic.npy`, lat/lon, and composite risk.
- Identify cells with no observations across the test period.
- Resize valid/land masks to 128 x 128.
- Save navigability mask.

Generated artifact:

```text
Sea ice prediction/outputs/navigation/navigation_mask.npz
```

Inspected stats:

| Metric | Value |
| --- | ---: |
| Navigable cells | 12,950 |
| Blocked cells | 3,434 |
| Navigable percentage | 79.04% |
| Land/invalid percentage | 20.96% |

### 12.5 `route_optimizer.py`

Purpose:

- Load composite risk and navigation mask.
- Prompt for start/destination coordinates.
- Map requested coordinates to nearest navigable cells.
- Compute baseline, safe, balanced, and fuel routes with A*.
- Save route CSVs, a summary CSV, and route plot.

Offline route profile settings:

| Mode | Risk weight | Blocked risk |
| --- | ---: | ---: |
| `safe` | 12.0 | 0.75 |
| `balanced` | 6.0 | 0.85 |
| `fuel` | 2.0 | 0.90 |

Offline movement cost:

```text
movement_cost = distance_km * (1 + risk_weight * cell_risk)
```

Saved route evaluation artifact:

| Route | Distance km | Mean risk | Max risk | Risk >= 0.50 | Risk >= 0.75 | Cells |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `baseline` | 8412.52 | 0.360828 | 0.983225 | 37.72% | 14.91% | 114 |
| `balanced` | 12555.12 | 0.100520 | 0.815781 | 12.36% | 2.25% | 178 |
| `fuel` | 10125.66 | 0.187676 | 0.895164 | 25.52% | 6.21% | 145 |

Saved route CSV files:

- `route_baseline.csv`
- `route_balanced.csv`
- `route_fuel.csv`
- `route_safe.csv`
- `recommended_route.csv`

At inspection time, `route_safe.csv` and `recommended_route.csv` each contained only one row. Treat those two artifacts as incomplete or from a failed/partial run until regenerated.

## 13. Iceberg Dataset

### 13.1 Raw Database

Raw iceberg CSV files live under:

```text
iceberg trajectory/data/raw/
```

The database README identifies it as the BYU MERS Consolidated Antarctic Iceberg Database. Each CSV represents one named iceberg. File names are iceberg IDs.

Inspected inventory:

| Metric | Value |
| --- | ---: |
| Raw CSV files | 647 |
| Raw rows | 516,691 |
| Unique raw schemas | 27 |

All raw columns observed:

```text
ascat_1, ascat_2, ascat_3,
date,
ers_1, ers_2, ers_3,
nic_1, nic_2, nic_3,
nscat_1, nscat_2, nscat_3,
oscat_1, oscat_2, oscat_3,
qscat_1, qscat_2, qscat_3,
sass_1, sass_2, sass_3,
seawinds_1, seawinds_2, seawinds_3,
size_1, size_2
```

README data rules:

- `sensor_1` is latitude.
- `sensor_2` is longitude.
- `sensor_3` is an observation/interpolation flag where available.
- `date` is year plus Julian day, formatted like `YYYYDDD`.
- `size_1` and `size_2` are iceberg major/minor axes in nautical miles.
- Values `0,0` indicate no data in sensor coordinate columns.
- Some files contain only the sensors available for that iceberg.

Largest raw schema groups:

| Schema group | File count | Columns |
| --- | ---: | --- |
| 1 | 193 | `date`, `qscat_1`, `qscat_2`, `qscat_3` |
| 2 | 132 | `ascat_1`, `ascat_2`, `ascat_3`, `date`, `nic_1`, `nic_2`, `nic_3`, `size_1`, `size_2` |
| 3 | 95 | `date`, `nic_1`, `nic_2`, `nic_3`, `size_1`, `size_2` |
| 4 | 29 | `date`, `nic_1`, `nic_2`, `nic_3`, `qscat_1`, `qscat_2`, `qscat_3`, `size_1`, `size_2` |
| 5 | 28 | `date`, `nic_1`, `nic_2`, `nic_3`, `qscat_1`, `qscat_2`, `qscat_3`, `seawinds_1`, `seawinds_2`, `seawinds_3`, `size_1`, `size_2` |

### 13.2 Raw-To-Master Trajectory Extraction

`iceberg trajectory/src/build_trajectory_dataset.py`:

1. Iterates all raw CSV files.
2. Selects a coordinate source using priority order:

```text
sass -> qscat -> ascat -> ers -> oscat -> nscat -> seawinds -> nic
```

3. Parses `date` using `%Y%j`.
4. Filters dates to 1970-01-01 through 2050-12-31.
5. Converts selected lat/lon columns to numeric.
6. Drops missing date/coordinate rows.
7. Keeps latitudes in -90 to 90 and longitudes in -180 to 180.
8. Drops duplicate dates.
9. Requires at least 7 observations.
10. Writes `data/processed/master_trajectories.csv`.

Processed master stats:

| Metric | Value |
| --- | ---: |
| Rows | 516,480 |
| Unique icebergs | 609 |
| Date range | 1976-02-01 to 2026-04-30 |
| Latitude range | -79.1 to 0.0 |
| Longitude range | -179.9998 to 179.9994 |

Coordinate source row counts:

| Source | Rows |
| --- | ---: |
| `qscat` | 300,227 |
| `ascat` | 194,623 |
| `ers` | 14,324 |
| `nic` | 5,432 |
| `sass` | 1,166 |
| `seawinds` | 708 |

Because the raw README uses `0,0` as no-data, downstream cleaning is important. The master file still has latitude maximum 0.0, which indicates some no-data coordinates survive this first extraction stage.

### 13.3 Processed Iceberg Trajectory Files

Processed iceberg files live under:

```text
iceberg trajectory/data/processed/
```

| File | Shape | Purpose |
| --- | ---: | --- |
| `master_trajectories.csv` | `(516480, 5)` | Initial extracted per-date iceberg positions with `iceberg_id`, `date`, `latitude`, `longitude`, `coord_source`. |
| `clean_trajectories.csv` | `(368526, 6)` | Cleaned and segmented tracks with `track_id`. |
| `trajectory_features.csv` | `(366577, 14)` | Movement features used by GRU sequence builder. |
| `track_summary.csv` | `(632, 9)` | Exploratory summary generated by `inspect_icebergs.py`. |

`trajectory_features.csv` columns:

```text
track_id, iceberg_id, date, latitude, longitude, coord_source,
dt_hours, prev_lat, prev_lon, distance_km, speed_kmh,
bearing_deg, delta_lat, delta_lon
```

Feature dataset stats:

| Metric | Value |
| --- | ---: |
| Rows | 366,577 |
| Tracks | 1,940 |
| Icebergs | 603 |
| Date range | 1976-12-27 to 2026-04-30 |
| Mean daily distance | 3.77 km |
| Median daily distance | 0.00 km |
| 95th percentile distance | 17.40 km |
| 99th percentile distance | 32.78 km |
| Maximum observed step | 456.93 km |
| Mean speed | 0.1567 km/h |
| 95th percentile speed | 0.7245 km/h |
| Maximum speed | 19.04 km/h |

Large movement counts:

| Threshold | Count | Percent |
| --- | ---: | ---: |
| `distance_km > 5` | 92,513 | 25.237% |
| `distance_km > 10` | 47,390 | 12.928% |
| `distance_km > 20` | 13,482 | 3.678% |
| `distance_km > 50` | 1,020 | 0.278% |
| `distance_km > 100` | 133 | 0.036% |

Speed outlier counts:

| Threshold | Count | Percent |
| --- | ---: | ---: |
| `speed_kmh > 1` | 8,646 | 2.359% |
| `speed_kmh > 2` | 1,128 | 0.308% |
| `speed_kmh > 5` | 85 | 0.023% |
| `speed_kmh > 10` | 26 | 0.007% |
| `speed_kmh > 15` | 7 | 0.002% |

### 13.4 Iceberg Sequence Dataset

`iceberg trajectory/src/build_iceberg_sequences.py` expects:

```text
iceberg trajectory/data/processed/trajectory_features.csv
```

It creates supervised sequence arrays in:

```text
iceberg trajectory/data/processed/iceberg_ml/
```

Input features:

| Feature | Meaning |
| --- | --- |
| `latitude` | Current latitude. |
| `longitude` | Current longitude. |
| `delta_lat` | Latitude difference from previous observation. |
| `delta_lon` | Wrapped longitude difference from previous observation. |
| `speed_kmh` | Movement speed in km/h. |

Sequence and target design:

```text
input X: 7 consecutive observations x 5 features
targets: north/east displacement in km at 1, 2, and 3 day horizons
```

The split is by iceberg identity, not random sequence. This reduces leakage where the same iceberg appears in both training and testing.

Split artifact stats:

| File | Shape | Meaning |
| --- | ---: | --- |
| `X_train.npy` | `(242752, 7, 5)` | Train inputs. |
| `Y_1d_train.npy` | `(242752, 2)` | Train 1-day north/east displacement. |
| `Y_2d_train.npy` | `(242752, 2)` | Train 2-day north/east displacement. |
| `Y_3d_train.npy` | `(242752, 2)` | Train 3-day north/east displacement. |
| `X_val.npy` | `(38865, 7, 5)` | Validation inputs. |
| `Y_1d_val.npy` | `(38865, 2)` | Validation 1-day targets. |
| `Y_2d_val.npy` | `(38865, 2)` | Validation 2-day targets. |
| `Y_3d_val.npy` | `(38865, 2)` | Validation 3-day targets. |
| `X_test.npy` | `(59940, 7, 5)` | Test inputs. |
| `Y_1d_test.npy` | `(59940, 2)` | Test 1-day targets. |
| `Y_2d_test.npy` | `(59940, 2)` | Test 2-day targets. |
| `Y_3d_test.npy` | `(59940, 2)` | Test 3-day targets. |

Metadata split stats:

| Split | Metadata shape | Icebergs | Tracks | Date span |
| --- | ---: | ---: | ---: | --- |
| Train | `(242752, 4)` | 405 | 1,196 | 1978-07-30 to 2026-04-20 |
| Validation | `(38865, 4)` | 86 | 202 | 1978-07-30 to 2026-04-20 |
| Test | `(59940, 4)` | 88 | 270 | 1978-07-30 to 2026-04-28 |

## 14. Iceberg ML Architecture

### 14.1 GRU Model

`iceberg trajectory/src/iceberg_model.py` defines `IcebergGRU`.

Architecture:

```text
input:       (batch, 7, 5)
GRU:         input_size=5, hidden_size=128, layers=2, batch_first=True, dropout=0.15
head:        Linear(128 -> 64), ReLU, Linear(64 -> 6)
output:      reshape to (batch, 3, 2)
parameters:  159,558
```

The output represents 3 horizons x 2 displacement components:

```text
[[north_km_24h, east_km_24h],
 [north_km_48h, east_km_48h],
 [north_km_72h, east_km_72h]]
```

### 14.2 One-Day GRU Training

`iceberg trajectory/src/train_iceberg_gru.py`:

- Loads `X_train`, `X_val`, `Y_1d_train`, and `Y_1d_val`.
- Normalizes inputs using train mean/std.
- Uses AdamW, Smooth L1 loss, ReduceLROnPlateau, gradient clipping, and early stopping.
- Saves `iceberg trajectory/checkpoints/iceberg_gru_best.pt`.

Checkpoint:

| File | Validation loss |
| --- | ---: |
| `iceberg_gru_best.pt` | 0.0069675342 |

### 14.3 Multi-Horizon GRU Training

`iceberg trajectory/src/train_iceberg_gru_multihorizon.py`:

- Loads `X_train`, `X_val`.
- Stacks `Y_1d`, `Y_2d`, and `Y_3d` into `(batch, 3, 2)`.
- Uses train mean/std normalization.
- Trains `IcebergGRU`.
- Saves `iceberg trajectory/checkpoints/iceberg_gru_72h_best.pt`.

Training configuration:

| Setting | Value |
| --- | ---: |
| Seed | 42 |
| Batch size | 256 |
| Epoch limit | 40 |
| Learning rate | 0.001 |
| Weight decay | 0.0001 |
| Loss | Smooth L1 |
| Scheduler | ReduceLROnPlateau, factor 0.5, patience 3 |
| Early stopping patience | 7 |
| Gradient clipping | Norm 1.0 |

Checkpoint:

| File | Validation loss |
| --- | ---: |
| `iceberg_gru_72h_best.pt` | 4.1939748270 |

The larger multi-horizon loss is expected because targets are kilometer-scale displacements for multiple horizons.

### 14.4 Runtime Iceberg Model Use

There are two iceberg services in runtime:

| Service | Asset | Used for |
| --- | --- | --- |
| `IcebergMLService` | `trajectory_features.csv` plus `iceberg_gru_72h_best.pt` | `/api/environment/layers` featured iceberg trajectories on the map. |
| `IcebergService` | `outputs/iceberg/test_predictions.csv` | Risk engine iceberg proximity risk. |

`IcebergMLService` predicts the following featured iceberg IDs when available:

```text
a76c, d15c, b09g, a81, d33c, a83
```

It uses the last 7 observations for each iceberg, normalizes them with checkpoint mean/std, predicts 24/48/72 hour displacements, and converts displacement back to lat/lon. If the model's 24 hour displacement is less than half of recent observed motion for a moving iceberg, it uses recent observed motion as a continuity correction.

`IcebergService` uses the latest target date in `test_predictions.csv`. At inspection time:

| Metric | Value |
| --- | ---: |
| Prediction rows | 49,683 |
| Unique icebergs in prediction CSV | 158 |
| Unique tracks in prediction CSV | 250 |
| Target date span | 1978-09-17 to 2026-04-19 |
| Latest target date | 2026-04-19 |
| Unique icebergs on latest target date | 4 |

Latest target-date icebergs in the current prediction CSV:

| Iceberg | Current lat | Current lon | Predicted lat | Predicted lon | GRU error km |
| --- | ---: | ---: | ---: | ---: | ---: |
| `a84` | -73.7232 | -106.1894 | -73.67248 | -106.26162 | 2.799607 |
| `b09g` | -68.2242 | 41.5694 | -68.22328 | 41.56385 | 0.250561 |
| `c39` | -69.2045 | 75.0942 | -69.20468 | 75.08926 | 0.196247 |
| `d15c` | -67.0623 | 80.1015 | -67.06234 | 80.097084 | 0.863893 |

### 14.5 Iceberg Evaluation Artifacts

`iceberg trajectory/outputs/iceberg/evaluation_summary.csv`:

| Metric | Value |
| --- | ---: |
| Test sequences | 49,683 |
| Persistence MAE | 3.816315 km |
| Persistence RMSE | 8.173801 km |
| Persistence median | 0.000000 km |
| GRU MAE | 3.360700 km |
| GRU RMSE | 6.658406 km |
| GRU median | 0.759938 km |
| MAE improvement | 11.938623% |
| ADE field | 3.360700 km |
| FDE field | 0.759938 km |

`iceberg trajectory/outputs/iceberg/72h_evaluation.csv`:

| Horizon | Persistence MAE km | GRU MAE km | Improvement |
| ---: | ---: | ---: | ---: |
| 24 h | 233.59146 | 200.08655 | 14.343381% |
| 48 h | 422.25345 | 354.63913 | 16.012733% |
| 72 h | 591.87775 | 501.65590 | 15.243321% |

Important caution: the current `evaluate_iceberg_72h.py` adds kilometer displacement values directly to latitude/longitude values before applying haversine distance. That inflates/invalidates the absolute kilometer metrics. The improvement percentage may still show directional behavior, but the script should be corrected before using these numbers as formal model performance.

Also, the current source of `evaluate_iceberg_gru.py` appears to have an indentation/return issue in its `haversine()` function. The existing `evaluation_summary.csv` was likely generated by an earlier or corrected version. Rerunning the current source should be checked before reporting results.

## 15. Script Inventory

### 15.1 Root Scripts

| File | Purpose |
| --- | --- |
| `run.py` | Starts local API/dashboard runtime. |
| `evaluate_model.py` | Creates `PolarMLRiskModel`, generates synthetic test data, and reports regression/classification metrics for fallback environmental risk. |

### 15.2 Backend Scripts

These are runtime modules, not standalone CLIs:

| File | Purpose |
| --- | --- |
| `main.py` | API app and service wiring. |
| `sea_ice_service.py` | Observation lookup, heatmap, and fallback ice model. |
| `sea_ice_ml.py` | ConvLSTM inference service. |
| `iceberg_service.py` | CSV-backed iceberg forecast positions and proximity risk. |
| `iceberg_ml_service.py` | GRU-backed featured iceberg trajectories. |
| `live_data_service.py` | Live/fallback MetOcean and dynamic hazards. |
| `risk_engine.py` | Risk fusion. |
| `route_engine.py` | A* routes, reroutes, evaluation. |
| `ml_risk_model.py` | Synthetic Random Forest fallback risk model. |

### 15.3 Sea-Ice Workspace Scripts

| File | Purpose |
| --- | --- |
| `Sea ice prediction/src/preprocess.py` | Convert raw southern NSIDC NetCDF files into stacked SIC/date/grid arrays. |
| `Sea ice prediction/src/split.py` | Chronological train/val/test split. |
| `Sea ice prediction/src/dataset.py` | PyTorch dataset for masked 7-day sequence learning. |
| `Sea ice prediction/src/model.py` | ConvLSTM model definition. |
| `Sea ice prediction/src/train.py` | Train ConvLSTM with masked MSE. |
| `Sea ice prediction/src/evaluate.py` | Evaluate ConvLSTM against persistence baseline. |
| `Sea ice prediction/src/baseline.py` | Evaluate persistence baseline only. |
| `Sea ice prediction/src/visualise_prediction.py` | Interactive date-based forecast visualization. |
| `Sea ice prediction/src/seaice_to_risk.py` | Convert ConvLSTM forecast into sea-ice risk grid. |
| `Sea ice prediction/src/iceberg_to_risk.py` | Convert iceberg prediction CSV into iceberg risk grid. |
| `Sea ice prediction/src/build_composite_risk.py` | Combine sea-ice and iceberg grids into composite navigation risk. |
| `Sea ice prediction/src/build_navigation_mask.py` | Build land/invalid/navigable mask. |
| `Sea ice prediction/src/route_optimizer.py` | Offline gridded route optimizer and route plot generator. |
| `Sea ice prediction/src/inspect_data.py` | Inspect one raw NetCDF file's schema. |
| `Sea ice prediction/src/inspect_seaice_grid.py` | Inspect processed sea-ice arrays and grid files. |
| `Sea ice prediction/src/checkdates.py` | Inspect processed sea-ice date gaps. |
| `Sea ice prediction/src/check_iceberg_dates.py` | Inspect recent and old iceberg raw CSV date coverage. |

### 15.4 Iceberg Workspace Scripts

| File | Purpose |
| --- | --- |
| `iceberg trajectory/analyze_schemas.py` | Summarize raw iceberg CSV schemas and coordinate column ranges. |
| `iceberg trajectory/inspect_coords.py` | Manually inspect coordinate-like fields in sample raw files. |
| `iceberg trajectory/out.txt` | Prior text output/log from an iceberg inspection run. |
| `iceberg trajectory/src/build_trajectory_dataset.py` | Extract raw iceberg coordinates into `master_trajectories.csv`. |
| `iceberg trajectory/src/build_iceberg_sequences.py` | Build 7-observation GRU input sequences and multi-horizon displacement targets. |
| `iceberg trajectory/src/iceberg_model.py` | GRU architecture definition. |
| `iceberg trajectory/src/train_iceberg_gru.py` | Train one-day GRU displacement model. |
| `iceberg trajectory/src/train_iceberg_gru_multihorizon.py` | Train 24/48/72 hour GRU displacement model. |
| `iceberg trajectory/src/evaluate_iceberg_gru.py` | Evaluate one-day GRU and write prediction/evaluation CSVs. Needs source check before rerun. |
| `iceberg trajectory/src/evaluate_iceberg_72h.py` | Evaluate multi-horizon GRU. Needs displacement-to-coordinate correction before formal metric use. |
| `iceberg trajectory/src/inspect_icebergs.py` | Exploratory raw database summary and `track_summary.csv` writer. |
| `iceberg trajectory/src/checkdate.py` | Finds raw files with parsed dates outside expected year range. |
| `iceberg trajectory/src/validate_trajectory.py` | Prints movement outlier and source-level trajectory statistics. |

### 15.5 Tests

| File | Coverage intent |
| --- | --- |
| `tests/test_sea_ice_api.py` | Checks `/api/sea-ice/forecast` response fields. |
| `tests/test_dynamic_rerouting.py` | Checks MetOcean service fields, dynamic hazards, route evaluation, reroute endpoint, live environmental endpoint, and hazard endpoint. |

The current `test_dynamic_rerouting.py` expects `IcebergService.get_all_icebergs()[0]["trajectory"]` to contain four points. Current `backend/iceberg_service.py` builds a two-point current-to-forecast trajectory from `test_predictions.csv`. The test or service should be aligned before relying on a clean test run.

## 16. Data And Model Lifecycle

### 16.1 Sea-Ice Lifecycle

```text
Raw NSIDC S25km NetCDF
  -> preprocess.py
  -> sic.npy, dates.npy, lat.npy, lon.npy
  -> split.py
  -> train_sic/val_sic/test_sic arrays
  -> dataset.py
  -> train.py
  -> best_model.pt
  -> evaluate.py / visualise_prediction.py
  -> seaice_to_risk.py
  -> seaice_navigation_risk.npz/csv
```

### 16.2 Iceberg Lifecycle

```text
Raw BYU MERS per-iceberg CSVs
  -> build_trajectory_dataset.py
  -> master_trajectories.csv
  -> cleaning / track segmentation / feature engineering artifact
  -> clean_trajectories.csv and trajectory_features.csv
  -> build_iceberg_sequences.py
  -> X/Y/metadata train-val-test arrays
  -> train_iceberg_gru_multihorizon.py
  -> iceberg_gru_72h_best.pt
  -> evaluate scripts / prediction CSVs
  -> iceberg_to_risk.py
  -> iceberg_navigation_risk.npz/csv
```

The repository currently contains `clean_trajectories.csv` and `trajectory_features.csv`, but the exact script that created those two artifacts is not present as a standalone source file. `build_iceberg_sequences.py` depends on `trajectory_features.csv`, so full reproducibility of the iceberg preprocessing pipeline requires restoring or documenting that cleaning/feature-engineering step.

### 16.3 Composite Offline Navigation Lifecycle

```text
seaice_navigation_risk.npz
iceberg_navigation_risk.npz
  -> build_composite_risk.py
  -> composite_navigation_risk.npz/csv
  -> build_navigation_mask.py
  -> navigation_mask.npz
  -> route_optimizer.py
  -> route CSVs, evaluation CSV, route PNG
```

### 16.4 Runtime Lifecycle

```text
run.py
  -> backend/main.py
  -> load SeaIceService
  -> load SeaIceMLService
  -> load IcebergService
  -> load IcebergMLService
  -> load LiveEnvironmentService
  -> create RiskEngine and RouteEngine
  -> serve dashboard and API
```

## 17. How To Run The Main Pieces

### 17.1 Runtime App

```bash
python run.py
```

### 17.2 Tests

```bash
pytest
```

Before treating the suite as a release gate, align the iceberg trajectory expectation in `tests/test_dynamic_rerouting.py` with the current `IcebergService` output or update the service to expose 24/48/72 hour points.

### 17.3 Sea-Ice Pipeline

Run from the `Sea ice prediction` directory for scripts using relative `data/...` paths:

```bash
cd "Sea ice prediction"
python src/preprocess.py
python src/split.py
python src/train.py
python src/evaluate.py
python src/visualise_prediction.py
python src/seaice_to_risk.py
```

Then from the repository root or appropriate script directory:

```bash
python "Sea ice prediction/src/iceberg_to_risk.py" 2026-04-19
python "Sea ice prediction/src/build_composite_risk.py"
python "Sea ice prediction/src/build_navigation_mask.py"
python "Sea ice prediction/src/route_optimizer.py"
```

`route_optimizer.py` prompts for route coordinates.

### 17.4 Iceberg Pipeline

Run from the `iceberg trajectory` directory for scripts using relative paths:

```bash
cd "iceberg trajectory"
python src/build_trajectory_dataset.py
python src/build_iceberg_sequences.py
python src/train_iceberg_gru_multihorizon.py
python src/evaluate_iceberg_72h.py
```

Current caveat: `build_iceberg_sequences.py` expects `data/processed/trajectory_features.csv`, but the exact source script for producing that feature file from `master_trajectories.csv` is not present in the current source tree.

## 18. Current Boundaries And Caveats

These are important implementation facts for future development and judging demos:

- Dynamic hazards are stored in memory only. They disappear when the backend process restarts and are not shared across multiple backend instances.
- There is no authentication, authorization, audit log, rate limiting, or persistent database.
- Live MetOcean uses Open-Meteo weather fields; wave height is derived from wind speed in code.
- Sea-ice forecast inference uses the nearest available observation date if an exact requested date is unavailable.
- The live route engine uses a coarse 1.5 deg x 3.0 deg lattice, not a ship-channel grid or chart-constrained route network.
- Runtime routing does not use bathymetry, land polygons, protected areas, official chart restrictions, port approaches, or icebreaker convoy rules.
- `Ice 1C` is shown in the frontend but does not have a dedicated vessel factor branch in the backend.
- `IcebergMLService` is used for map display, while `IcebergService` is used for iceberg proximity risk. These are related but separate runtime paths.
- `IcebergService` currently exposes one-step current-to-forecast trajectories from `test_predictions.csv`, while one test expects four absolute trajectory points.
- `test_predictions.csv` has 49,683 rows, while current `metadata_test.csv` has 59,940 rows. Those artifacts likely came from different pipeline runs or script versions.
- `evaluate_iceberg_gru.py` current source should be checked before rerun because the `haversine()` return appears misplaced.
- `evaluate_iceberg_72h.py` should convert north/east kilometer displacement back to coordinates before haversine evaluation.
- `track_summary.csv` is exploratory and includes unfiltered parsed-date behavior from `inspect_icebergs.py`; use `master_trajectories.csv`, `clean_trajectories.csv`, and `trajectory_features.csv` for ML-facing documentation.
- `route_safe.csv` and `recommended_route.csv` are one-row artifacts at inspection time and should be regenerated before being presented as valid saved routes.
- The repository contains generated `.pyc` files and local caches. They are execution artifacts, not part of the technical design.

## 19. What Is Working Today

The current working system can:

- Serve a Leaflet Antarctic mission dashboard.
- Load processed sea-ice observation arrays where present.
- Render real satellite sea-ice heatmap points.
- Run ConvLSTM sea-ice forecast inference from `best_model.pt`.
- Use fallback deterministic sea-ice behavior if data/model assets are missing.
- Load GRU iceberg trajectory model and show featured iceberg paths.
- Load prediction CSVs for iceberg proximity risk.
- Fetch live weather from Open-Meteo when reachable.
- Fall back to deterministic MetOcean synthesis when offline or restricted.
- Inject and render dynamic hazards.
- Fuse sea ice, iceberg, weather, dynamic hazard, and vessel class into composite risk.
- Calculate three live route profiles with A*.
- Evaluate route metrics and segment risk.
- Simulate an underway voyage in the frontend.
- Periodically request reroutes during simulation.

## 20. Recommended Next Technical Improvements

1. Restore or write the missing iceberg cleaning/feature-engineering script that produces `clean_trajectories.csv` and `trajectory_features.csv`.
2. Fix the current `evaluate_iceberg_gru.py` haversine return issue and regenerate `evaluation_summary.csv`.
3. Fix `evaluate_iceberg_72h.py` coordinate reconstruction and regenerate 24/48/72 hour metrics.
4. Align `IcebergService` and `test_dynamic_rerouting.py` on whether iceberg trajectories should be two-point one-step forecasts or four-point 0/24/48/72 hour forecasts.
5. Add a backend vessel factor branch for `Ice 1C` or change the frontend option to match supported backend classes.
6. Persist dynamic hazards in a database or shared cache.
7. Add a proper marine weather/wave source instead of deriving wave height from wind.
8. Add route constraints for land, bathymetry, charts, port approaches, protected areas, and voyage regulations.
9. Version datasets, checkpoints, generated risk grids, and evaluation artifacts with run metadata.
10. Add frontend tests or Playwright checks for map rendering, route cards, evaluation modal, offline cache, and reroute alert behavior.

