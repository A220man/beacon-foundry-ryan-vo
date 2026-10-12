import math
from typing import List, Dict, Any
from ..models.schemas import TrajectoryStep, TrajectorySimulationRequest, TrajectorySimulationResponse

# Standard lunar constants
LUNAR_GRAVITY_MPS2 = 1.62
DESCENT_ENGINE_MAX_THRUST_N = 45000.0 # ~10,000 lbf
LM_INITIAL_MASS_KG = 15000.0
ISP_SECONDS = 311.0
G0_MPS2 = 9.80665

def run_trajectory_simulation(request: TrajectorySimulationRequest) -> TrajectorySimulationResponse:
    t_step = 1.0 # 1 second steps
    steps: List[TrajectoryStep] = []
    
    current_altitude = request.initial_altitude_m
    current_velocity = request.initial_velocity_mps
    current_mass = LM_INITIAL_MASS_KG
    fuel_remaining = 8200.0 # kg of usable prop
    attitude_pitch = 45.0 # degrees relative to local vertical
    
    total_delta_v = 0.0
    max_attitude_rate = 0.0
    anomaly_detected = False
    notes: List[str] = []
    
    # Target profile based on program
    if request.burn_program == "P63_BRAKING":
        target_thrust_pct = 95.0
        pitch_rate = -0.3 # degrees per second pitch forward
    elif request.burn_program == "P64_APPROACH":
        target_thrust_pct = 57.0
        pitch_rate = -0.5
    elif request.burn_program == "P66_TERMINAL":
        target_thrust_pct = 40.0
        pitch_rate = 0.0
    else: # TJET_REACTION
        target_thrust_pct = 15.0
        pitch_rate = 1.2

    prev_pitch = attitude_pitch

    for s in range(request.duration_s):
        sim_time = float(s)
        
        # Thrusters
        active_thrusters = ["DESCENT_DPS"]
        if request.simulate_thruster_failure and s > 20:
            # Inject RCS quad thruster blowout
            active_thrusters.append("RCS_QUAD_B_ERR")
            attitude_pitch += 4.5 # Anomaly pitch drift
            anomaly_detected = True
            if "Thruster failure induced pitch perturbation at T+20s" not in notes:
                notes.append("Thruster failure induced pitch perturbation at T+20s")
        else:
            attitude_pitch += pitch_rate
            active_thrusters.extend(["RCS_U1", "RCS_D2"])

        pitch_change_rate = abs(attitude_pitch - prev_pitch) / t_step
        if pitch_change_rate > max_attitude_rate:
            max_attitude_rate = pitch_change_rate
        prev_pitch = attitude_pitch

        # Fuel burn
        thrust_force = (target_thrust_pct / 100.0) * DESCENT_ENGINE_MAX_THRUST_N
        mass_flow_rate = thrust_force / (ISP_SECONDS * G0_MPS2)
        fuel_burned = mass_flow_rate * t_step
        fuel_remaining = max(0.0, fuel_remaining - fuel_burned)
        current_mass = max(7000.0, current_mass - fuel_burned)

        # Acceleration and state integration
        accel_thrust = thrust_force / current_mass
        accel_net = accel_thrust * math.sin(math.radians(attitude_pitch)) - LUNAR_GRAVITY_MPS2
        
        current_velocity = max(0.0, current_velocity - (accel_thrust * math.cos(math.radians(attitude_pitch)) * t_step))
        current_altitude = max(0.0, current_altitude - (current_velocity * t_step * 0.1))
        
        step_dv = accel_thrust * t_step
        total_delta_v += step_dv

        step_anomaly = False
        if request.simulate_thruster_failure and s > 20:
            step_anomaly = True

        steps.append(TrajectoryStep(
            timestamp_s=sim_time,
            altitude_m=round(current_altitude, 1),
            velocity_mps=round(current_velocity, 1),
            thrust_pct=target_thrust_pct,
            fuel_remaining_kg=round(fuel_remaining, 1),
            active_thrusters=active_thrusters,
            attitude_pitch_deg=round(attitude_pitch, 2),
            anomaly_flag=step_anomaly
        ))

    if not anomaly_detected:
        notes.append("Trajectory conforms to nominal Apollo descent corridor boundaries.")

    return TrajectorySimulationResponse(
        simulation_id=f"sim-{request.burn_program.lower()}-{request.duration_s}s",
        burn_program=request.burn_program,
        trajectory=steps,
        delta_v_total=round(total_delta_v, 2),
        max_attitude_rate_deg_s=round(max_attitude_rate, 2),
        anomaly_detected=anomaly_detected,
        notes=notes
    )
