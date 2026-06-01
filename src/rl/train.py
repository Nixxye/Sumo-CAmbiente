import os
import sys

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from src.rl.env import SumoTrafficEnv

def main():
    sumocfg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'simulations', 'baseline.sumocfg'))
    print(f"Using sumocfg at: {sumocfg_path}")
    
    env = SumoTrafficEnv(sumocfg_path=sumocfg_path, render_mode="none")
    
    # Verify the environment
    check_env(env)
    
    print("Environment verified. Starting training...")
    
    # Use PPO for training
    model = PPO("MlpPolicy", env, verbose=1, n_steps=256, batch_size=64)
    
    # Train for a few timesteps (proof of concept)
    model.learn(total_timesteps=1000)
    
    # Save the model
    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'model_ppo.zip'))
    model.save(model_path)
    print(f"Model saved to {model_path}")
    
    env.close()

if __name__ == "__main__":
    main()
