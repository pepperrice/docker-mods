import requests
import time
import xml.etree.ElementTree as ET
import argparse

def read_conf_file(config_path):
    # read XML
    tree = ET.parse(config_path)
    root = tree.getroot()

    # get api key and port
    api_key = root.find('ApiKey').text
    port = root.find('Port').text
    return api_key, port 

def delete_unimported_downloads(api_key, url):
    headers = {
        "X-Api-Key": api_key
    }

    try:
        response = requests.get(f"{url}/queue?page=1&pageSize=200&includeUnknownSeriesItems=true&includeSeries=true&includeEpisode=true", headers=headers)
    except requests.exceptions.RequestException as e:
        print(e)
        return

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

parser = argparse.ArgumentParser(description='Remove stuck items from Sonarr/Radarr.')
parser.add_argument('--config', type=str, help='Path to Sonarr/Radarr conf')
parser.add_argument('--interval', type=int, default=1800, help='Waiting interval')
parser.add_argument("-o", "--oneshot", action="store_true", help='Run once')
parser.add_argument("-u", "--url", type=str, help='URL to Sonarr/Radarr "http//:sonarr:8989", required if --config is not set')
parser.add_argument("-a", "--apikey", type=str, help='The API key, required if --config is not set')
args = parser.parse_args()

if not any([args.url, args.apikey, args.config]):
    raise Exception("--config, --apikey and --url not Set")

if args.url:
    url = f"{args.url}/api/v3"

if args.apikey:
    api_key = args.apikey

time.sleep(60)

while True:
    if args.config:
        api_key,port = read_conf_file(args.config)
        url = f"http://localhost:{port}/api/v3"

    delete_unimported_downloads(api_key, url)
    
    # run once if oneshot
    if args.oneshot:
        print("oneshot set only run once")
        break
    
    # wait
    time.sleep(args.interval)