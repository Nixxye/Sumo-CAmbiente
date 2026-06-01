import osmnx as ox
import os

# Coordinates obtained previously:
# BBox: -25.4782072, -49.3059994, -25.4305491, -49.2490417
# South, West, North, East -> min_lat, min_lon, max_lat, max_lon

# But osmnx expects north, south, east, west for bbox
north = -25.4305491
south = -25.4782072
east = -49.2490417
west = -49.3059994

print("Downloading map using OSMnx...")
# Download network as graph
G = ox.graph_from_bbox(north, south, east, west, network_type='drive')

# Save to graphml or osm? OSMnx doesn't directly save to .osm out of the box in the latest versions.
# Actually, the user asked to extract using osmnx OR SUMO polyconvert/netconvert (preferably netconvert with osm args)
# If osmnx is used, it saves to graphml and we might need to convert graphml to net.xml, OR we can just use overpass api directly properly.

# Let's fix the overpass api script instead.
