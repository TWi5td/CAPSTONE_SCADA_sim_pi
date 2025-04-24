import json

with open('/home/SCADA/scada_project/scada_config/config.json', 'r') as f:
    config = json.load(f)
print("Protocol:", config["protocol"])
print("Data Points:", config["data_points"])
