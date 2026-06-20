import os
import sys
import traci
import xml.etree.ElementTree as ET

# Ensure src path is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.rl.env import SumoTrafficEnv
from stable_baselines3 import PPO
def parse_tripinfo(tripinfo_file):
    if not os.path.exists(tripinfo_file):
        print(f"Warning: {tripinfo_file} not found.")
        return None
        
    try:
        tree = ET.parse(tripinfo_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing tripinfo XML: {e}")
        return None
    
    total_waiting_time = 0.0
    trip_count = 0
    
    for trip in root.findall('tripinfo'):
        waiting_time = float(trip.get('waitingTime', 0))
        
        total_waiting_time += waiting_time
        trip_count += 1
        
    if trip_count == 0:
        return 0, 0
        
    avg_waiting_time = total_waiting_time / trip_count
    return total_waiting_time, avg_waiting_time, trip_count

def run_evaluation(scenario, traffic, use_gui):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    net_file = os.path.join(base_dir, 'data', 'map', 'curitiba.net.xml')
    route_file = os.path.join(base_dir, 'data', 'traffic', f'{traffic}.rou.xml')
    
    if not os.path.exists(route_file):
        print(f"Error: Route file not found at {route_file}")
        sys.exit(1)
        
    tripinfo_file = os.path.join(base_dir, 'simulations', f'tripinfo_{scenario}_{traffic}.xml')
    
    if scenario == "baseline":
        gui_settings_file = os.path.join(base_dir, 'simulations', 'viewsettings.xml')
        sumo_binary = "sumo-gui" if use_gui else "sumo"
        cmd = [
            sumo_binary,
            "-n", net_file,
            "-r", route_file,
            "--tripinfo-output", tripinfo_file,
            "--no-step-log", "true",
            "--no-warnings", "true"
        ]
        if use_gui and os.path.exists(gui_settings_file):
            cmd.extend(["--gui-settings-file", gui_settings_file])
        print(f"Running baseline simulation for traffic: {traffic}...")
        traci.start(cmd)
        
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            
        traci.close()
        
    elif scenario == "rl":
        model_path = os.path.join(base_dir, 'src', 'rl', 'model_ppo.zip')
        if not os.path.exists(model_path):
            print(f"Error: Model file not found at {model_path}. Please train the model first.")
            print("You can run training via: python src/rl/train.py")
            sys.exit(1)
            
        print(f"Running RL simulation for traffic: {traffic}...")
        model = PPO.load(model_path)
        env = SumoTrafficEnv(
            net_file=net_file, 
            route_file=route_file, 
            tripinfo_file=tripinfo_file,
            render_mode="human" if use_gui else "none"
        )
        
        obs, _ = env.reset()
        done = False
        while not done:
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            
        env.close()
        

    elif scenario == "green_wave":
        # Importa o controlador de Onda Verde (em src/controllers/).
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)
        from src.controllers.greenwave_controller import GreenWaveController

        sumo_binary = "sumo-gui" if use_gui else "sumo"
        cmd = [
            sumo_binary,
            "-n", net_file,
            "-r", route_file,
            "--tripinfo-output", tripinfo_file,
            "--no-step-log", "true",
            "--no-warnings", "true",
            "--waiting-time-memory", "10000",
        ]
        print(f"Running GREEN WAVE simulation for traffic: {traffic}...")
        traci.start(cmd)

        controller = GreenWaveController(verbose=True)
        controller.apply_offsets()  # aplica offsets fixos no início (t=0)

        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            controller.collect_step_metrics()

        traci.close()
    # Analyze results
    print("\n" + "="*40)
    print("--- Simulation Results ---")
    metrics = parse_tripinfo(tripinfo_file)
    if metrics:
        total_waiting_time, avg_waiting_time, trip_count = metrics
        print(f"Scenario               : {scenario.upper()}")
        print(f"Traffic Profile        : {traffic}")
        print(f"Completed Trips        : {trip_count}")
        print(f"Total Waiting Time     : {total_waiting_time:.2f} seconds")
        print(f"Average Wait Per Trip  : {avg_waiting_time:.2f} seconds")
    else:
        print("Could not calculate metrics.")
    print("="*40 + "\n")
