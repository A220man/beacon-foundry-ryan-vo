import pytest
from app.services.trajectory_engine import run_trajectory_simulation
from app.models.schemas import TrajectorySimulationRequest

def test_nominal_braking_simulation():
    req = TrajectorySimulationRequest(
        burn_program="P63_BRAKING",
        initial_altitude_m=15000.0,
        initial_velocity_mps=1690.0,
        duration_s=30,
        simulate_thruster_failure=False
    )
    res = run_trajectory_simulation(req)
    assert res.anomaly_detected is False
    assert len(res.trajectory) == 30
    assert res.delta_v_total > 0
    # Final altitude should be lower than initial
    assert res.trajectory[-1].altitude_m < 15000.0
    # Fuel should decrease
    assert res.trajectory[-1].fuel_remaining_kg < 8200.0

def test_approach_phase_simulation():
    req = TrajectorySimulationRequest(
        burn_program="P64_APPROACH",
        initial_altitude_m=3000.0,
        initial_velocity_mps=200.0,
        duration_s=20
    )
    res = run_trajectory_simulation(req)
    assert res.burn_program == "P64_APPROACH"
    assert len(res.trajectory) == 20

def test_thruster_failure_injection():
    req = TrajectorySimulationRequest(
        burn_program="P63_BRAKING",
        duration_s=35,
        simulate_thruster_failure=True
    )
    res = run_trajectory_simulation(req)
    assert res.anomaly_detected is True
    # At T > 20s anomalies should trigger
    failed_steps = [s for s in res.trajectory if s.anomaly_flag]
    assert len(failed_steps) > 10
    assert "RCS_QUAD_B_ERR" in failed_steps[0].active_thrusters
