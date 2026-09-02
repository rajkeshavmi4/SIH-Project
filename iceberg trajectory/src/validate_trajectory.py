import pandas as pd

FILE = "data/processed/trajectory_features.csv"

df = pd.read_csv(FILE, parse_dates=["date"])

print("=" * 55)
print("EXTREME MOVEMENT ANALYSIS")
print("=" * 55)

for threshold in [5, 10, 20, 50, 100]:
    n = (df["distance_km"] > threshold).sum()
    p = n / len(df) * 100
    print(
        f"> {threshold:3d} km/day : "
        f"{n:7,} ({p:.3f}%)"
    )

print("\nSpeed thresholds:")

for threshold in [1, 2, 5, 10, 15]:
    n = (df["speed_kmh"] > threshold).sum()
    p = n / len(df) * 100
    print(
        f"> {threshold:2d} km/h : "
        f"{n:7,} ({p:.3f}%)"
    )

print("\nExtreme movements by coordinate source:")

print(
    df.groupby("coord_source")
      .agg(
          observations=("distance_km", "size"),
          median_km=("distance_km", "median"),
          p95_km=("distance_km", lambda x: x.quantile(.95)),
          max_km=("distance_km", "max"),
          median_speed=("speed_kmh", "median"),
          max_speed=("speed_kmh", "max")
      )
      .sort_values("max_km", ascending=False)
      .to_string()
)

print("\nTop 30 movements:")

print(
    df.nlargest(30, "distance_km")[
        [
            "track_id",
            "iceberg_id",
            "date",
            "coord_source",
            "latitude",
            "longitude",
            "dt_hours",
            "distance_km",
            "speed_kmh",
            "bearing_deg"
        ]
    ].to_string(index=False)
)