import argparse
import sys
from src.evaluation.evaluate import run_evaluation

def main():
    parser = argparse.ArgumentParser(description="SUMO Traffic Light Controller Evaluation and Integration")
    parser.add_argument(
        "--scenario", 
        choices=["baseline", "rl"], 
        required=True, 
        help="Choose the scenario to run: 'baseline' (default SUMO logic) or 'rl' (trained Machine Learning agent)."
    )
    parser.add_argument(
        "--traffic", 
        type=str, 
        required=True, 
        help="The prefix of the traffic file to run (e.g., 'random_peak' will run 'data/traffic/random_peak.rou.xml')."
    )
    parser.add_argument(
        "--gui", 
        action="store_true", 
        help="Flag to enable SUMO GUI visualization."
    )
    
    args = parser.parse_args()
    
    try:
        run_evaluation(scenario=args.scenario, traffic=args.traffic, use_gui=args.gui)
    except Exception as e:
        print(f"Error executing evaluation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
