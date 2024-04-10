import requests
import time
import yaml
import asyncio

IP_REQUEST_URL = "https://api.ipify.org/?format=json"
CLOUDFLARE_REQUEST_FORMAT = "https://api.cloudflare.com/client/v4/zones/{zone}/{cmd}"

with open("/home/nic/Desktop/pi-server/config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)
api_config = config.get("cloudflare_api")


def get_public_ip() -> str:
    """
    Makes a request to api.ipify.org to determine this device's public IP address.
    :return: IP address (string)
    """
    response = requests.get(IP_REQUEST_URL)
    return response.json()["ip"]


def cloudflare_api_request(verb: str, command: str, **kwargs):

    zone_id = api_config.get("zone_id")
    url = CLOUDFLARE_REQUEST_FORMAT.format(zone=zone_id, cmd=command)
    
    response = requests.request(
        verb, url, headers={
            "X-Auth-Key": api_config.get("key"),
            "X-Auth-Email": api_config.get("email")
        },
        **kwargs
    )
    return response


def get_dns_record(name: str):
    """
    Makes a Cloudflare API request to find a type A DNS record with a given name.

    :param name: name of DNS record (string)
    :return: JSON blob of DNS record data
    """
    response = cloudflare_api_request("GET", "dns_records").json()

    if response.get("success"):
        print("Cloudflare API DNS record request was successful.")
        records = response.get("result")
        for record in records:
            if record["type"] == "A" and record["name"] == name:
                print(f"Found type A record with name {name}.")
                return record
        else:
            print(f"No type A DNS record found with name {name}.")
    else:
        print("Cloudflare API DNS record request failed")
        print(f"Errors reported: {response.get('errors')}")
    

async def update_dns_record_ip_address(name: str, proxied: bool = True) -> None:
    """
    Makes a Cloudflare API request to update the IP address of the type A DNS record with the given name to the current
    IP address of this device.

    :param name: name of DNS record (string)
    :param proxied: option to specify whether to have traffic proxied through Cloudflare.
    """
    print("Finding DNS record...")
    record = get_dns_record(name)
    
    if record is None:
        print("DNS record not found; aborting.")
        return
    
    print("Getting public IP address...")
    public_ip = get_public_ip()

    if public_ip is None:
        print("Could not obtain IP address; aborting.")
        return

    if public_ip == record.get("content"):
        print(f"IP address for {name} is already up-to-date; aborting.")
        return
    
    old_ip = record.get("content")
    record_id = record.get("id")

    response = cloudflare_api_request(
        "PUT",
        f"dns_records/{record_id}",
        json={
            "type": "A",
            "name": name,
            "content": public_ip,
            "proxied": proxied
        }
    )

    if response.status_code == 200:
        print(f"Successfully updated DNS record for {name} from {old_ip} to {public_ip}.")
    else:
        print(f"Error while updating DNS record: response status code {response.status_code}.")


async def enter_development_mode():
    # Purge cache
    print("Purging cache...")
    response = cloudflare_api_request("DELETE", "purge_cache", json={"purge_everything": True})
    if response.status_code == 200:
        print("Successfully purged Cloudflare cache.")
    else:
        print(f"Error while purging Cloudflare cache: response status code {response.status_code}")
    
    # Activate development mode
    print("Activating development mode...")
    response = cloudflare_api_request("PATCH", "settings/development_mode", json={"value": "on"})
    if response.status_code == 200:
        print("Server is running in development mode (for the next 3 hrs). Cloudflare's cache will be bypassed.")
    else:
        print(f"Error while activating development mode: response status code {response.status_code}")


if __name__ == "__main__":
    print("Testing API requests:")

    print("Getting public ip...")
    
    t0 = time.perf_counter()
    ip = get_public_ip()
    t1 = time.perf_counter()

    response_time = int((t1 - t0) * 1000)
    print(f"Response: {ip} ({response_time} ms)")

    hostname = "pi.nicyelland.com"
    print(f"Getting DNS record for {hostname}")
    
    t0 = time.perf_counter()
    dns_record = get_dns_record(hostname)
    t1 = time.perf_counter()
    
    response_time = int((t1 - t0) * 1000)
    print(f"Response: {dns_record} ({response_time} ms)")

    print("Updating IP address...")

    t0 = time.perf_counter()
    asyncio.run(update_dns_record_ip_address(hostname))
    t1 = time.perf_counter()

    response_time = int((t1 - t0) * 1000)
    print(f"({response_time} ms)")

    print("Entering development mode...")

    t0 = time.perf_counter()
    asyncio.run(enter_development_mode())
    t1 = time.perf_counter()

    response_time = int((t1 - t0) * 1000)
    print(f"({response_time} ms)")
