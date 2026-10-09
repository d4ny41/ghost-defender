"""Pure maths for the Ghost Defender. numpy only.

Coordinates are in yards, speeds in yards per second, `dir` in degrees
clockwise from the +y axis (0 = +y, 90 = +x, 180 = -y, 270 = -x).
"""

import math

import numpy as np

DT = 0.1  # seconds between tracking frames (10 fps)
CONTACT_RADIUS = 1.0  # yards
LEAGUE_MAX_SPEED = 8.5  # yd/s

_EPS = 1e-9


def velocity_from_s_dir(s, dir_deg):
    """Return the velocity (vx, vy) from speed `s` and direction `dir_deg`."""
    rad = math.radians(dir_deg)
    return np.array([s * math.sin(rad), s * math.cos(rad)], dtype=float)


def solve_intercept(carrier_pos, carrier_vel, defender_pos, speed):
    """Earliest time a defender at `speed` can meet a constant-velocity carrier.

    Returns (t, intercept_point) or None if no intercept exists.
    """
    c0 = np.asarray(carrier_pos, dtype=float)
    vc = np.asarray(carrier_vel, dtype=float)
    d0 = np.asarray(defender_pos, dtype=float)

    # 1. No speed, no solution.
    if speed <= 0:
        return None

    d = c0 - d0
    a = float(vc @ vc) - speed**2
    b = 2.0 * float(d @ vc)
    c = float(d @ d)

    # 2. Defender is already on the carrier.
    if c < _EPS:
        return 0.0, c0.copy()

    # 3. Equal speeds: the quadratic degenerates to a linear equation.
    if abs(a) < _EPS:
        if b < 0:
            t = -c / b
            return t, c0 + vc * t
        return None

    # 4. General case.
    disc = b * b - 4.0 * a * c
    if disc < 0:
        return None
    sqrt_disc = math.sqrt(disc)
    roots = [(-b - sqrt_disc) / (2.0 * a), (-b + sqrt_disc) / (2.0 * a)]
    positive = [r for r in roots if r > 0]
    if not positive:
        return None
    t = min(positive)
    return t, c0 + vc * t


def ghost_positions(defender_pos, intercept_pos, t_intercept, taus):
    """Ghost positions at each `tau` (seconds since the catch), shape (n, 2).

    The ghost runs in a straight line from the defender's start to the
    intercept point, then stays there. If t_intercept is 0 it is always at
    the intercept point.
    """
    d0 = np.asarray(defender_pos, dtype=float)
    i = np.asarray(intercept_pos, dtype=float)
    taus = np.asarray(taus, dtype=float).reshape(-1)

    if t_intercept <= 0:
        return np.tile(i, (len(taus), 1))

    frac = np.minimum(taus / t_intercept, 1.0)
    return d0 + (i - d0) * frac[:, None]


def path_length(points):
    """Sum of straight-line distances between consecutive rows of (n, 2)."""
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or len(pts) < 2:
        return 0.0
    return float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum())
