"""
core/sensing_model.py
---------------------
Probabilistic sensing model for WSN coverage.

Detection probability follows an exponential falloff beyond the reliable
sensing radius Rs. Inside Rs, detection is certain (P=1.0). Beyond Rs,
probability decays as:
    P(d) = exp(-lambda * (d - Rs))

This is the model used throughout all fitness evaluations and coverage maps.
No I/O, no HTTP, no business logic — pure math only.
"""

import numpy as np


def detection_probability(d: float, Rs: float, lam: float = 0.5) -> float:
    """
    Compute the detection probability for a single sensor at distance d.

    Args:
        d:   Distance from sensor to target point (meters).
        Rs:  Reliable sensing radius. Within this range, P=1.0.
        lam: Falloff coefficient (lambda). Higher = steeper decay. Default 0.5.

    Returns:
        Detection probability in [0.0, 1.0].
    """
    if d <= Rs:
        return 1.0
    return float(np.exp(-lam * (d - Rs)))


def detection_probability_vectorized(
    distances: np.ndarray, Rs: float, lam: float = 0.5
) -> np.ndarray:
    """
    Vectorized version of detection_probability for use with NumPy arrays.

    Args:
        distances: Array of distances (any shape).
        Rs:        Reliable sensing radius.
        lam:       Falloff coefficient.

    Returns:
        Array of detection probabilities, same shape as distances.
    """
    probs = np.where(distances <= Rs, 1.0, np.exp(-lam * (distances - Rs)))
    return probs.astype(np.float64)


def coverage_map(
    positions: np.ndarray,
    area_W: float,
    area_H: float,
    Rs: float,
    lam: float = 0.5,
    cell_size: float = 1.0,
    restricted_mask: np.ndarray | None = None,
) -> np.ndarray:
    """
    Compute the per-cell detection probability map for the full deployment area.

    The result represents: for each grid cell, what is the probability that
    AT LEAST ONE sensor detects an event there?
    P_cell = 1 - prod(1 - P_i(d_i)) over all sensors i.

    Args:
        positions:       Array of shape (N, 2) — sensor (x, y) positions.
        area_W:          Width of the deployment area (meters).
        area_H:          Height of the deployment area (meters).
        Rs:              Reliable sensing radius.
        lam:             Falloff coefficient.
        cell_size:       Grid resolution (meters per cell). Default 1.0.
        restricted_mask: Optional boolean array of shape (rows, cols).
                         True = cell is restricted (excluded from coverage).

    Returns:
        coverage: Float array of shape (rows, cols) with values in [0.0, 1.0].
                  restricted cells are set to 0.0.
    """
    cols = int(np.ceil(area_W / cell_size))
    rows = int(np.ceil(area_H / cell_size))

    # Grid cell center coordinates
    xs = (np.arange(cols) + 0.5) * cell_size  # shape: (cols,)
    ys = (np.arange(rows) + 0.5) * cell_size  # shape: (rows,)
    grid_x, grid_y = np.meshgrid(xs, ys)       # shape: (rows, cols)

    # Start with probability that NO sensor detects an event (product of misses)
    prob_miss = np.ones((rows, cols), dtype=np.float64)

    for sx, sy in positions:
        # Distance from this sensor to every grid cell
        dist = np.sqrt((grid_x - sx) ** 2 + (grid_y - sy) ** 2)
        p_detect = detection_probability_vectorized(dist, Rs, lam)
        prob_miss *= (1.0 - p_detect)

    cov = 1.0 - prob_miss

    # Zero out restricted areas
    if restricted_mask is not None:
        cov[restricted_mask] = 0.0

    return cov
