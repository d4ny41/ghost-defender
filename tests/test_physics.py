import numpy as np
from pytest import approx

from physics import (
    arrival_gap,
    ghost_positions,
    ghost_to_target,
    path_length,
    reach_time,
    solve_intercept,
    velocity_from_s_dir,
)

TOL = 1e-3


def test_example_1_stationary_carrier():
    t, i = solve_intercept((10, 0), (0, 0), (0, 0), 5)
    assert t == approx(2.0, abs=TOL)
    assert i == approx([10, 0], abs=TOL)


def test_example_2_crossing_route():
    t, i = solve_intercept((10, 0), (0, 5), (0, 0), 10)
    assert t == approx(1.1547, abs=TOL)
    assert i == approx([10, 5.7735], abs=TOL)


def test_example_3_faster_carrier_running_away():
    assert solve_intercept((10, 0), (8, 0), (0, 0), 6) is None


def test_example_4_equal_speeds_carrier_towards_defender():
    t, i = solve_intercept((10, 0), (-5, 0), (0, 0), 5)
    assert t == approx(1.0, abs=TOL)
    assert i == approx([5, 0], abs=TOL)


def test_example_5_velocity():
    assert velocity_from_s_dir(5, 90) == approx([5, 0], abs=TOL)
    assert velocity_from_s_dir(5, 180) == approx([0, -5], abs=TOL)


def test_example_6_ghost_path():
    pos = ghost_positions((0, 0), (10, 0), 2.0, [1.0, 2.0, 2.4])
    assert pos.shape == (3, 2)
    assert pos[0] == approx([5, 0], abs=TOL)
    assert pos[1] == approx([10, 0], abs=TOL)
    assert pos[2] == approx([10, 0], abs=TOL)


def test_example_7_path_length():
    assert path_length(np.array([[0, 0], [3, 4], [3, 10]])) == approx(11.0, abs=TOL)


def test_zero_speed_moving_carrier_returns_none():
    assert solve_intercept((10, 0), (0, 5), (0, 0), 0) is None


# --- v2 worked examples (CLAUDE.md "Worked examples" 3-7) ---------------------


def test_v2_example_3_ghost_to_target():
    pos = ghost_to_target((0, 0), (10, 0), 5, [0, 1, 2, 3])
    assert pos.shape == (4, 2)
    assert pos[0] == approx([0, 0], abs=TOL)
    assert pos[1] == approx([5, 0], abs=TOL)
    assert pos[2] == approx([10, 0], abs=TOL)
    assert pos[3] == approx([10, 0], abs=TOL)


def test_v2_example_4_arrival_gap():
    assert arrival_gap((0, 0), (10, 0), 4, 2) == approx(2.0, abs=TOL)
    assert arrival_gap((0, 0), (10, 0), 6, 2) == approx(0.0, abs=TOL)


def test_v2_example_5_reach_time():
    assert reach_time((0, 0), (6, 8), 5) == approx(2.0, abs=TOL)


def test_v2_example_6_defender_already_at_catch_point():
    pos = ghost_to_target((5, 5), (5, 5), 7, [0, 1])
    assert pos.shape == (2, 2)
    assert pos[0] == approx([5, 5], abs=TOL)
    assert pos[1] == approx([5, 5], abs=TOL)
    assert arrival_gap((5, 5), (5, 5), 7, 1) == approx(0.0, abs=TOL)
    assert reach_time((5, 5), (5, 5), 7) == approx(0.0, abs=TOL)


def test_v2_example_7_wasted_yards():
    catch = np.array([6.0, 8.0])
    ghost_gap = arrival_gap((0, 0), catch, 5, 2)
    real_gap = float(np.linalg.norm(catch - np.array([3.0, 4.0])))
    assert ghost_gap == approx(0.0, abs=TOL)
    assert real_gap == approx(5.0, abs=TOL)
    assert real_gap - ghost_gap == approx(5.0, abs=TOL)
