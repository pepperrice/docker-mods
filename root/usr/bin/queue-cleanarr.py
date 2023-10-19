import requests
import time
import xml.etree.ElementTree as ET
import argparse

def get_api_key(config_path):
    # read XML
    tree = ET.parse(config_path)
    root = tree.getroot()

    # get api key and port
    api_key = root.find('ApiKey').text
    port = root.find('Port').text
    return api_key, port 

def delete_unimported_downloads(api_key, port):
    # URL to arr
    url = f"http://localhost:{port}:/api/v3"

    headers = {
        "X-Api-Key": api_key
    }

    response = requests.get(f"{url}/queue?page=1&pageSize=200&includeUnknownSeriesItems=true&includeSeries=true&includeEpisode=true", headers=headers)

    # check responsecode 
    if response.status_code == 200:
        data = response.json()

        for item in data['records']:
            # Usenet and Warning, delete from Download Client
            if item['trackedDownloadStatus'] == 'warning'and item['protocol'] == "usenet":
                print(f"Remove download: {item['title']}")
                requests.delete(f"{url}/queue/{item['id']}?removeFromClient=true&blocklist=false&skipRedownload=true", headers=headers)
            # Torrent Warning, keep in client to avoid HaR
            elif item['trackedDownloadStatus'] == 'warning' and item['protocol'] == "torrent":
                print(f"Remove download: {item['title']}")
                requests.delete(f"{url}/queue/{item['id']}?removeFromClient=false&blocklist=false&skipRedownload=true", headers=headers)
    
    else:
        print(f"Error getting API: {response.status_code}")


def main(config_path, interval):
    while True:
        api_key,port = get_api_key(config_path)
        delete_unimported_downloads(api_key, port)

        # wait
        time.sleep(interval)
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Remove stuck items from Sonarr/Radarr.')
    parser.add_argument('--config', type=str, required=True, help='Path to Sonarr/Radarr conf')
    parser.add_argument('--interval', type=int, required=True, help='Waiting interval')
    
    args = parser.parse_args()

    main(args.config, args.interval)