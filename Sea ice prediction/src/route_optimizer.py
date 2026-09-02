from pathlib import Path
import heapq
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent.parent

RISK_FILE = (
    ROOT
    / "outputs"
    / "navigation"
    / "composite_navigation_risk.npz"
)

MASK_FILE = (
    ROOT
    / "outputs"
    / "navigation"
    / "navigation_mask.npz"
)

OUTPUT_DIR = (
    ROOT
    / "outputs"
    / "navigation"
)

EARTH_RADIUS_KM = 6371.0088

MODES = {
    "safe": {
        "risk_weight": 12.0,
        "blocked_risk": 0.75
    },
    "balanced": {
        "risk_weight": 6.0,
        "blocked_risk": 0.85
    },
    "fuel": {
        "risk_weight": 2.0,
        "blocked_risk": 0.90
    }
}

NEIGHBOURS = [
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1)
]


def haversine(lat1, lon1, lat2, lon2):

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)

    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return (
        2
        * EARTH_RADIUS_KM
        * math.asin(math.sqrt(a))
    )


def distance_between(
    lat_grid,
    lon_grid,
    a,
    b
):

    r1, c1 = a
    r2, c2 = b

    return haversine(
        lat_grid[r1, c1],
        lon_grid[r1, c1],
        lat_grid[r2, c2],
        lon_grid[r2, c2]
    )


def nearest_cell(
    lat_grid,
    lon_grid,
    latitude,
    longitude
):

    dlat = lat_grid - latitude

    dlon = (
        (lon_grid - longitude + 180.0)
        % 360.0
    ) - 180.0

    score = (
        dlat ** 2
        +
        (
            dlon
            * np.cos(
                np.radians(latitude)
            )
        ) ** 2
    )

    return np.unravel_index(
        np.argmin(score),
        score.shape
    )


def nearest_navigable_cell(
    lat_grid,
    lon_grid,
    navigable,
    latitude,
    longitude
):

    dlat = lat_grid - latitude

    dlon = (
        (lon_grid - longitude + 180.0)
        % 360.0
    ) - 180.0

    score = (
        dlat ** 2
        +
        (
            dlon
            * np.cos(
                np.radians(latitude)
            )
        ) ** 2
    )

    score = np.where(
        navigable,
        score,
        np.inf
    )

    if not np.isfinite(score).any():

        raise RuntimeError(
            "No navigable cells available."
        )

    return np.unravel_index(
        np.argmin(score),
        score.shape
    )


def astar(
    risk,
    navigable,
    lat_grid,
    lon_grid,
    start,
    goal,
    risk_weight,
    blocked_risk
):

    blocked = (
        ~navigable
        |
        (risk >= blocked_risk)
    )

    blocked[start] = False
    blocked[goal] = False

    def heuristic(node):

        return distance_between(
            lat_grid,
            lon_grid,
            node,
            goal
        )

    open_set = []

    heapq.heappush(
        open_set,
        (
            heuristic(start),
            0.0,
            start
        )
    )

    came_from = {}

    g_score = {
        start: 0.0
    }

    while open_set:

        _, current_cost, current = (
            heapq.heappop(open_set)
        )

        if current == goal:

            path = [current]

            while current in came_from:

                current = came_from[current]

                path.append(current)

            path.reverse()

            return path

        if (
            current_cost
            >
            g_score.get(
                current,
                float("inf")
            )
        ):

            continue

        r, c = current

        for dr, dc in NEIGHBOURS:

            nr = r + dr
            nc = c + dc

            if (
                nr < 0
                or nr >= risk.shape[0]
                or nc < 0
                or nc >= risk.shape[1]
            ):
                continue

            if blocked[nr, nc]:
                continue

            neighbour = (nr, nc)

            distance = distance_between(
                lat_grid,
                lon_grid,
                current,
                neighbour
            )

            cell_risk = float(
                risk[nr, nc]
            )

            movement_cost = (
                distance
                * (
                    1.0
                    +
                    risk_weight * cell_risk
                )
            )

            new_cost = (
                current_cost
                + movement_cost
            )

            if new_cost < g_score.get(
                neighbour,
                float("inf")
            ):

                g_score[neighbour] = new_cost

                came_from[neighbour] = current

                f_score = (
                    new_cost
                    +
                    heuristic(neighbour)
                )

                heapq.heappush(
                    open_set,
                    (
                        f_score,
                        new_cost,
                        neighbour
                    )
                )

    return None


def route_metrics(
    path,
    risk,
    navigable,
    lat_grid,
    lon_grid
):

    distances = []

    risks = []

    invalid_cells = 0

    for i, cell in enumerate(path):

        r, c = cell

        risks.append(
            float(risk[r, c])
        )

        if not navigable[r, c]:
            invalid_cells += 1

        if i > 0:

            distances.append(
                distance_between(
                    lat_grid,
                    lon_grid,
                    path[i - 1],
                    cell
                )
            )

    risks = np.asarray(risks)

    distances = np.asarray(distances)

    return {
        "distance_km":
            float(distances.sum()),

        "mean_risk":
            float(risks.mean()),

        "max_risk":
            float(risks.max()),

        "risk_ge_050_pct":
            float(
                np.mean(risks >= 0.50) * 100
            ),

        "risk_ge_075_pct":
            float(
                np.mean(risks >= 0.75) * 100
            ),

        "invalid_cells":
            int(invalid_cells),

        "route_cells":
            int(len(path))
    }


def save_route(
    path,
    risk,
    lat_grid,
    lon_grid,
    filename
):

    rows = []

    for step, (r, c) in enumerate(path):

        rows.append({
            "step": step,
            "latitude": float(
                lat_grid[r, c]
            ),
            "longitude": float(
                lon_grid[r, c]
            ),
            "risk": float(
                risk[r, c]
            )
        })

    df = pd.DataFrame(rows)

    output = (
        OUTPUT_DIR
        / filename
    )

    df.to_csv(
        output,
        index=False
    )


def plot_route(
    risk,
    navigable,
    lat_grid,
    lon_grid,
    path,
    start,
    goal,
    title,
    filename
):

    fig, ax = plt.subplots(
        figsize=(12, 9)
    )

    masked_risk = np.ma.masked_where(
        ~navigable,
        risk
    )

    mesh = ax.pcolormesh(
        lon_grid,
        lat_grid,
        masked_risk,
        shading="auto"
    )

    plt.colorbar(
        mesh,
        ax=ax,
        label="Composite Navigation Risk"
    )

    route_lat = [
        lat_grid[r, c]
        for r, c in path
    ]

    route_lon = [
        lon_grid[r, c]
        for r, c in path
    ]

    ax.plot(
        route_lon,
        route_lat,
        linewidth=3,
        label="Recommended Route"
    )

    ax.scatter(
        lon_grid[start],
        lat_grid[start],
        s=130,
        marker="o",
        edgecolors="black",
        linewidths=1.2,
        label="Start",
        zorder=5
    )

    ax.scatter(
        lon_grid[goal],
        lat_grid[goal],
        s=150,
        marker="X",
        edgecolors="black",
        linewidths=1.2,
        label="Destination",
        zorder=5
    )

    ax.set_xlabel(
        "Longitude (°)"
    )

    ax.set_ylabel(
        "Latitude (°)"
    )

    ax.set_title(title)

    ax.grid(
        alpha=0.2
    )

    ax.legend()

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / filename,
        dpi=220,
        bbox_inches="tight"
    )

    plt.show()


# ============================================================
# MAIN
# ============================================================

print("=" * 65)
print("POLARROUTE AI")
print("RISK-AWARE ANTARCTIC NAVIGATION")
print("=" * 65)


risk_data = np.load(
    RISK_FILE
)

mask_data = np.load(
    MASK_FILE
)


risk = risk_data[
    "risk"
].astype(
    np.float32
)

lat_grid = mask_data[
    "latitude"
].astype(
    np.float32
)

lon_grid = mask_data[
    "longitude"
].astype(
    np.float32
)

navigable = mask_data[
    "navigable"
].astype(
    bool
)


if risk.shape != navigable.shape:

    raise ValueError(
        "Risk and navigation grids "
        "do not match."
    )


print(
    f"\nGrid             : {risk.shape}"
)

print(
    f"Navigable cells  : "
    f"{navigable.sum():,}"
)

print(
    f"Blocked cells    : "
    f"{(~navigable).sum():,}"
)


# ============================================================
# INPUT
# ============================================================

print("\n" + "=" * 65)
print("ROUTE INPUT")
print("=" * 65)

print(
    "\nSuggested geographic bounds:"
)

print(
    f"Latitude  : "
    f"{lat_grid.min():.2f} → "
    f"{lat_grid.max():.2f}"
)

print(
    f"Longitude : "
    f"{lon_grid.min():.2f} → "
    f"{lon_grid.max():.2f}"
)


start_lat = float(
    input(
        "\nStart latitude: "
    )
)

start_lon = float(
    input(
        "Start longitude: "
    )
)

goal_lat = float(
    input(
        "Destination latitude: "
    )
)

goal_lon = float(
    input(
        "Destination longitude: "
    )
)


# ============================================================
# MAP TO SAFE CELLS
# ============================================================

requested_start = nearest_cell(
    lat_grid,
    lon_grid,
    start_lat,
    start_lon
)

requested_goal = nearest_cell(
    lat_grid,
    lon_grid,
    goal_lat,
    goal_lon
)

start = nearest_navigable_cell(
    lat_grid,
    lon_grid,
    navigable,
    start_lat,
    start_lon
)

goal = nearest_navigable_cell(
    lat_grid,
    lon_grid,
    navigable,
    goal_lat,
    goal_lon
)


print("\nCoordinate mapping")

print(
    f"Requested start : "
    f"{start_lat:.4f}, "
    f"{start_lon:.4f}"
)

print(
    f"Mapped start    : "
    f"{lat_grid[start]:.4f}, "
    f"{lon_grid[start]:.4f}"
)

print(
    f"Requested goal  : "
    f"{goal_lat:.4f}, "
    f"{goal_lon:.4f}"
)

print(
    f"Mapped goal     : "
    f"{lat_grid[goal]:.4f}, "
    f"{lon_grid[goal]:.4f}"
)


# ============================================================
# ROUTES
# ============================================================

routes = {}

results = {}


print("\nCalculating baseline route...")

baseline = astar(
    risk=np.zeros_like(risk),
    navigable=navigable,
    lat_grid=lat_grid,
    lon_grid=lon_grid,
    start=start,
    goal=goal,
    risk_weight=0.0,
    blocked_risk=2.0
)

if baseline is not None:

    routes["baseline"] = baseline

    results["baseline"] = route_metrics(
        baseline,
        risk,
        navigable,
        lat_grid,
        lon_grid
    )


for mode, config in MODES.items():

    print(
        f"Calculating {mode} route..."
    )

    path = astar(
        risk=risk,
        navigable=navigable,
        lat_grid=lat_grid,
        lon_grid=lon_grid,
        start=start,
        goal=goal,
        risk_weight=config[
            "risk_weight"
        ],
        blocked_risk=config[
            "blocked_risk"
        ]
    )

    if path is None:

        print(
            f"No {mode} route found."
        )

        continue

    routes[mode] = path

    results[mode] = route_metrics(
        path,
        risk,
        navigable,
        lat_grid,
        lon_grid
    )


# ============================================================
# RESULTS
# ============================================================

print("\n" + "=" * 65)
print("ROUTE COMPARISON")
print("=" * 65)

for name, result in results.items():

    print(
        f"\n{name.upper()}"
    )

    print(
        f"Distance       : "
        f"{result['distance_km']:.2f} km"
    )

    print(
        f"Mean risk      : "
        f"{result['mean_risk']:.4f}"
    )

    print(
        f"Maximum risk   : "
        f"{result['max_risk']:.4f}"
    )

    print(
        f"Risk >= 0.50   : "
        f"{result['risk_ge_050_pct']:.2f}%"
    )

    print(
        f"Risk >= 0.75   : "
        f"{result['risk_ge_075_pct']:.2f}%"
    )

    print(
        f"Invalid cells  : "
        f"{result['invalid_cells']}"
    )

    print(
        f"Route cells    : "
        f"{result['route_cells']}"
    )


# ============================================================
# COMPARISON
# ============================================================

if (
    "baseline" in results
    and "balanced" in results
):

    base = results["baseline"]

    balanced = results["balanced"]

    distance_change = (
        (
            balanced["distance_km"]
            /
            base["distance_km"]
        )
        - 1
    ) * 100

    risk_change = (
        (
            balanced["mean_risk"]
            /
            base["mean_risk"]
        )
        - 1
    ) * 100

    print(
        "\n" + "=" * 65
    )

    print(
        "BALANCED ROUTE VS BASELINE"
    )

    print(
        "=" * 65
    )

    print(
        f"Distance change : "
        f"{distance_change:+.2f}%"
    )

    print(
        f"Mean risk change: "
        f"{risk_change:+.2f}%"
    )


# ============================================================
# SAVE
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


for name, path in routes.items():

    save_route(
        path,
        risk,
        lat_grid,
        lon_grid,
        f"route_{name}.csv"
    )


summary = []

for name, result in results.items():

    row = {
        "route": name
    }

    row.update(result)

    summary.append(row)


pd.DataFrame(
    summary
).to_csv(
    OUTPUT_DIR
    / "route_evaluation.csv",
    index=False
)


# ============================================================
# PLOT BALANCED ROUTE
# ============================================================

if "balanced" in routes:

    plot_route(
        risk,
        navigable,
        lat_grid,
        lon_grid,
        routes["balanced"],
        start,
        goal,
        "POLARROUTE AI | Balanced Risk-Aware Route",
        "recommended_route.png"
    )

elif "safe" in routes:

    plot_route(
        risk,
        navigable,
        lat_grid,
        lon_grid,
        routes["safe"],
        start,
        goal,
        "POLARROUTE AI | Safe Route",
        "recommended_route.png"
    )

elif "baseline" in routes:

    plot_route(
        risk,
        navigable,
        lat_grid,
        lon_grid,
        routes["baseline"],
        start,
        goal,
        "POLARROUTE AI | Baseline Route",
        "recommended_route.png"
    )


print(
    "\n" + "=" * 65
)

print(
    "FILES SAVED"
)

print(
    "=" * 65
)

print(
    OUTPUT_DIR
    / "route_evaluation.csv"
)

print(
    OUTPUT_DIR
    / "recommended_route.png"
)

print(
    OUTPUT_DIR
    / "route_baseline.csv"
)

print(
    OUTPUT_DIR
    / "route_balanced.csv"
)

print(
    OUTPUT_DIR
    / "route_safe.csv"
)

print(
    OUTPUT_DIR
    / "route_fuel.csv"
)