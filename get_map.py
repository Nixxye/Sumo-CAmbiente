import urllib.request
import urllib.parse
import json
import time
import os

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

def get_coords(query):
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"Error getting coords for {query}: {e}")
    return None, None

def get_bbox():
    points = [
        "Avenida Presidente Kennedy, Curitiba",
        "Rua XV de Novembro, Curitiba",
        "Rua Marechal Floriano Peixoto, Curitiba",
        "Rua Martim Afonso, Curitiba",
        "Rua Mariano Torres, Curitiba",
        "Rua General Mário Tourinho, Curitiba"
    ]
    lats = []
    lons = []
    for p in points:
        lat, lon = get_coords(p)
        print(f"{p}: {lat}, {lon}")
        if lat and lon:
            lats.append(lat)
            lons.append(lon)
        time.sleep(1)

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    return min_lat, max_lat, min_lon, max_lon

min_lat, max_lat, min_lon, max_lon = get_bbox()
print(f"BBox: {min_lat},{min_lon},{max_lat},{max_lon}")

print("Downloading OSM data...")
overpass_url = "http://overpass-api.de/api/interpreter"
query = f"""
[out:xml][timeout:180];
(
  node({min_lat},{min_lon},{max_lat},{max_lon});
  <;
  >;
);
out meta;
"""
req = urllib.request.Request(overpass_url, data=urllib.parse.urlencode({'data': query}).encode())
try:
    with urllib.request.urlopen(req) as response:
        content = response.read()
        os.makedirs('data/map', exist_ok=True)
        with open('data/map/curitiba.osm', 'wb') as f:
            f.write(content)
        print("Done saving curitiba.osm!")
except Exception as e:
    print(f"Error downloading map: {e}")
