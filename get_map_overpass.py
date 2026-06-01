import requests
import os

north = -25.4305491
south = -25.4782072
east = -49.2490417
west = -49.3059994

bbox = f"{south},{west},{north},{east}"
query = f"""
[out:xml][timeout:180];
(
  way({bbox})["highway"];
  node(w);
);
out meta;
"""

print(f"Downloading from Overpass for bbox: {bbox}")
url = "https://overpass-api.de/api/interpreter"
headers = {
    "User-Agent": "CAmbienteBot/1.0",
    "Accept": "*/*"
}
response = requests.post(url, data={"data": query}, headers=headers)

if response.status_code == 200:
    os.makedirs('data/map', exist_ok=True)
    with open('data/map/curitiba.osm', 'wb') as f:
        f.write(response.content)
    print("Map saved to data/map/curitiba.osm")
else:
    print(f"Error {response.status_code}: {response.text}")
