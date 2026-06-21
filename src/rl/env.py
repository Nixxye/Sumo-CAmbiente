import gymnasium as gym
from gymnasium import spaces
import numpy as np
import traci
import os
import sys

class SumoTrafficEnv(gym.Env):
    metadata = {"render_modes": ["human", "none"], "render_fps": 30}

    def __init__(self, sumocfg_path=None, net_file=None, route_file=None, tripinfo_file=None, render_mode="none"):
        super(SumoTrafficEnv, self).__init__()
        
        self.sumocfg_path = sumocfg_path
        self.net_file = net_file
        self.route_file = route_file
        self.tripinfo_file = tripinfo_file
        self.render_mode = render_mode
        self.tls_id = None
        self.tls_phases = []
        self.step_length = 5 # seconds per action
        self.conn_label = f"sim_{id(self)}"
        
        # Start traci temporarily to get info
        cmd = ["sumo", "--no-step-log", "true", "--no-warnings", "true"]
        if self.sumocfg_path:
            cmd.extend(["-c", self.sumocfg_path])
        elif self.net_file and self.route_file:
            cmd.extend(["-n", self.net_file, "-r", self.route_file])
        else:
            raise ValueError("Either sumocfg_path or (net_file and route_file) must be provided.")
            
        traci.start(cmd, label="init_conn")
        conn = traci.getConnection("init_conn")
        
        tls_list = conn.trafficlight.getIDList()
        if len(tls_list) == 0:
            conn.close()
            raise ValueError("No traffic lights found in the network.")
        
        # Pick the first traffic light that has more than 1 phase
        for tls in tls_list:
            logics = conn.trafficlight.getAllProgramLogics(tls)
            if len(logics) > 0 and len(logics[0].phases) > 1:
                self.tls_id = tls
                self.tls_phases = logics[0].phases
                break
                
        if self.tls_id is None:
            self.tls_id = tls_list[0]
            self.tls_phases = conn.trafficlight.getAllProgramLogics(self.tls_id)[0].phases
            
        self.controlled_lanes = list(set(conn.trafficlight.getControlledLanes(self.tls_id)))
        conn.close()
        
        self.action_space = spaces.Discrete(len(self.tls_phases))
        self.observation_space = spaces.Box(
            low=0, 
            high=np.inf, 
            shape=(len(self.controlled_lanes),), 
            dtype=np.float32
        )
        
        self.sumo_cmd = None
        self.conn = None

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        if self.conn is not None:
            try:
                self.conn.close()
            except:
                pass
            
        sumo_binary = "sumo-gui" if self.render_mode == "human" else "sumo"
        self.sumo_cmd = [
            sumo_binary, 
            "--no-step-log", "true",
            "--no-warnings", "true",
            "--waiting-time-memory", "10000",
            "--device.emissions.probability", "1"
        ]
        
        if self.sumocfg_path:
            self.sumo_cmd.extend(["-c", self.sumocfg_path])
        else:
            self.sumo_cmd.extend(["-n", self.net_file, "-r", self.route_file])
            
        if self.tripinfo_file:
            self.sumo_cmd.extend(["--tripinfo-output", self.tripinfo_file])
            edgedata_file = self.tripinfo_file.replace("tripinfo_", "edgedata_")
            self.sumo_cmd.extend(["--edgedata-output", edgedata_file])
            
        gui_settings_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', 'simulations', 'viewsettings.xml')
        if self.render_mode == "human" and os.path.exists(gui_settings_file):
            self.sumo_cmd.extend(["--gui-settings-file", gui_settings_file])
            
        traci.start(self.sumo_cmd, label=self.conn_label)
        self.conn = traci.getConnection(self.conn_label)
        
        self.step_num = 0
        return self._get_obs(), {}

    def step(self, action):
        self.conn.trafficlight.setPhase(self.tls_id, action)
        
        for _ in range(self.step_length):
            self.conn.simulationStep()
            self.step_num += 1
            
        obs = self._get_obs()
        reward = self._get_reward()
        
        terminated = self.conn.simulation.getMinExpectedNumber() <= 0
        truncated = self.step_num >= 3600
        
        return obs, reward, terminated, truncated, {}

    def _get_obs(self):
        obs = []
        for lane in self.controlled_lanes:
            obs.append(self.conn.lane.getLastStepHaltingNumber(lane))
        return np.array(obs, dtype=np.float32)

    def _get_reward(self):
        total_waiting_time = 0
        for lane in self.controlled_lanes:
            total_waiting_time += self.conn.lane.getWaitingTime(lane)
        return -total_waiting_time

    def close(self):
        if self.conn is not None:
            try:
                self.conn.close()
            except:
                pass
            self.conn = None
