import os
import subprocess
import sys

def generate_traffic(net_file="data/map/curitiba.net.xml", route_file="data/traffic/random_peak.rou.xml", end_time=3600, period=2):
    sumo_home = os.environ.get("SUMO_HOME")
    if not sumo_home:
        print("Error: SUMO_HOME environment variable not set. Please set it to your SUMO installation path.")
        sys.exit(1)
        
    random_trips = os.path.join(sumo_home, "tools", "randomTrips.py")
    
    os.makedirs(os.path.dirname(route_file), exist_ok=True)
    
    # We will generate routes directly using -r
    cmd = [
        sys.executable, random_trips,
        "-n", net_file,
        "-r", route_file,
        "-e", str(end_time),
        "-p", str(period),
        "--validate"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"Traffic generated at {route_file}")

if __name__ == "__main__":
    generate_traffic()
