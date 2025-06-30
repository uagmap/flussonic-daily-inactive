#Script to collect inactive cameras from flussonic watcher V2
#For V2, outdated docs can be found on WayBack machine: https://web.archive.org/web/20240714105230/https://flussonic.github.io/watcher-docs/api.html

import requests
import json
import os
from datetime import datetime

#authenticate and get session key
auth_response = requests.post(
    "http://my.url.here/vsaas/api/v2/auth/login",
    headers={"Content-Type": "application/json"},
    json={"login": "uagmap", "password": "xxxx"}
)

#configuration
SESSION_KEY = auth_response.json()['session']
BASE_URL = "http://my.url.here/vsaas/api/v2/cameras"
OUTPUT_DIR = "data_collection"

#create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

#fetch all cameras with pagination
all_cameras = []
limit = 100  #fetch 100 ata time (may be changed)
offset = 0

#loop will run, fetching 100 cameras at a time and increasing offset
#until runs out of cameras to fetch
while True:
    #pagination parameters
    params = {
        "limit": limit,     #how many at a time
        "offset": offset    #shift from the start?
    }
    
    headers = { #from docs
        "x-vsaas-session": SESSION_KEY,
        "X-Page-Limit": str(limit),
        "X-Page-Offset": str(offset)
    }
    
    response = requests.get(
        BASE_URL,
        headers=headers,
        params=params
    )
    
    cameras = response.json()

    #stop when we get an empty response
    #catches APIs that return empty lists at the end
    if not cameras:  
        break
    
    all_cameras.extend(cameras)
    print(f"Fetched {len(cameras)} cameras (Total: {len(all_cameras)})")
    
    #stop if we got fewer cameras than requested
    #catches APIs that don't return empty lists, but return partial pages
    if len(cameras) < limit:
        break
        
    offset += limit #increase offset by limit each iteration

#process results and total statistics
online_count = sum(1 for camera in all_cameras if camera.get('stream_status').get('alive')) #for each matching camera increment by 1
offline_cameras = [camera for camera in all_cameras if not camera.get('stream_status', {}).get('alive')]
print("\nFinal Results:")
print("-" * 60)
print(f"Total cameras fetched: {len(all_cameras)}")
print(f"Online cameras: {online_count}")
print(f"Offline cameras: {len(all_cameras) - online_count}")
print("-" * 60)

print(f"List of offline cameras: ")
print("-" * 60)


#need to save snapshot with timestamp
timestamp = datetime.now().strftime("%d-%m-%Y") #format date output
filename = f"{OUTPUT_DIR}/inactive_cameras_{timestamp}.json"


#prepare data
data = {
    "timestamp": datetime.now().isoformat(),
    "total_cameras": len(all_cameras),
    "online_count": online_count,
    "offline_count": len(offline_cameras),
    "offline_cameras": []
}

for camera in offline_cameras:
    stream_status = camera.get('stream_status', {})
    data["offline_cameras"].append({
        "name": stream_status.get('name', 'N/A'),
        "alive": stream_status.get('alive', 'N/A'),
        "source_error": stream_status.get('source_error', 'None'),
    })


#write to json
with open(filename, 'w') as f:
     json.dump(data, f, indent=2)

print(f"Saved snapshot of {len(offline_cameras)} offline cameras to {filename}")
print("=" * 60)


#print summary
print(f"\nOffline Cameras ({len(offline_cameras)}):")

'''
for camera in offline_cameras:
    stream_status = camera.get('stream_status', {})
    print(f"- {stream_status.get('name', 'N/A')} (Error: {stream_status.get('source_error', 'None')})")
'''
