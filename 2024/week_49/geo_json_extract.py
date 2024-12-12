import json
import os

print(f'Current wd: {os.getcwd()}')

# Define the states you want to keep
new_england_states = {"Maine", "New Hampshire", "Vermont", "Massachusetts", "Rhode Island", "Connecticut"}

# Input and output file paths
input_file = "./figure_friday/2024/week_49/data/gz_2010_us_040_00_500k.json"
output_file = "./figure_friday/2024/week_49/data/new_england_geojson.json"

# Load the input GeoJSON
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Filter the features
filtered_features = []
for feature in data["features"]:
    if feature["properties"].get("NAME") in new_england_states:
        filtered_features.append(feature)

# Create a new GeoJSON FeatureCollection
filtered_data = {
    "type": "FeatureCollection",
    "features": filtered_features
}

# Write the filtered data to a new file
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(filtered_data, f, indent=2)

print(f"Filtered GeoJSON saved to {output_file}")
