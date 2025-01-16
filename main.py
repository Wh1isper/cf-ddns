import os
import socket
import time

import httpx
from loguru import logger

# Cloudflare API base URL
CLOUDFLARE_API_BASE = "https://api.cloudflare.com/client/v4"

# API credentials from environment variables
CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "")
ZONE_ID = os.environ.get("ZONE_ID", "")
DOMAIN = os.environ.get("DOMAIN", "")


def get_cloudflare_records():
    """
    Retrieve existing DNS records for the specified domain from Cloudflare.

    Returns:
    list: A list of DNS records
    """
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    # Get all DNS records for the specified zone (domain)
    url = f"{CLOUDFLARE_API_BASE}/zones/{ZONE_ID}/dns_records?type=AAAA"

    response = httpx.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()

    if not data["success"]:
        logger.error(f"Failed to retrieve DNS records: {data.get('errors', 'Unknown error')}")
        return []

    logger.debug(f"Successfully retrieved DNS records: {data['result']}")
    # Filter records for the exact domain
    records = [record for record in data["result"] if record.get("name") == DOMAIN]

    return records


def delete_cloudflare_record(record_id):
    """
    Delete a specific DNS record from Cloudflare.

    Args:
    record_id (str): The ID of the DNS record to delete

    Returns:
    bool: True if deletion was successful, False otherwise
    """
    try:
        headers = {
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json",
        }

        url = f"{CLOUDFLARE_API_BASE}/zones/{ZONE_ID}/dns_records/{record_id}"

        response = httpx.delete(url, headers=headers)
        response.raise_for_status()

        data = response.json()

        if not data["success"]:
            logger.error(f"Failed to delete DNS record: {data.get('errors', 'Unknown error')}")
            return False

        return True

    except httpx.RequestException as e:
        logger.error(f"Error deleting Cloudflare DNS record: {e}")
        return False


def create_cloudflare_record(v6_address):
    """
    Create a new AAAA (IPv6) DNS record in Cloudflare.

    Args:
    v6_address (str): The IPv6 address to add as a DNS record

    Returns:
    bool: True if record creation was successful, False otherwise
    """
    try:
        headers = {
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json",
        }

        # Prepare the DNS record payload
        name = "@" if len(DOMAIN.split(".")) == 2 else DOMAIN.split(".", 1)[0]
        payload = {
            "type": "AAAA",
            "name": name,  # Root domain
            "content": v6_address,
            "ttl": 1,  # Automatic TTL
            "proxied": False,
        }

        url = f"{CLOUDFLARE_API_BASE}/zones/{ZONE_ID}/dns_records"

        response = httpx.post(url, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()

        if not data["success"]:
            logger.error(f"Failed to create DNS record: {data.get('errors', 'Unknown error')}")
            return False

        return True

    except httpx.RequestException as e:
        logger.error(f"Error creating Cloudflare DNS record: {e}")
        return False


def isNetOK(testserver):
    s = socket.socket()
    s.settimeout(3)
    try:
        status = s.connect_ex(testserver)
        if status == 0:
            s.close()
            return True
        else:
            return False
    except Exception:
        return False


def isNetChainOK(testserver=("www.baidu.com", 80)):
    isOK = isNetOK(testserver)
    return isOK


def ddns_refresh(v6_address):
    logger.info(f"Refreshing DDNS with address: {v6_address}")
    records = get_cloudflare_records()
    noneedupdate = False

    for record in records:
        if record["content"] == v6_address:
            logger.debug(f"Record {v6_address} already exists")
            noneedupdate = True
            continue
        logger.info(f"Removing record {record['id']}")
        delete_cloudflare_record(record["id"])

    if noneedupdate:
        return False

    logger.info("Adding new record")
    create_cloudflare_record(v6_address)
    return True


def get_v6_address_from_web():
    try:
        r = httpx.get("https://api-ipv6.ip.sb")
        r.raise_for_status()
    except Exception as e:
        logger.exception(e)
        return None
    return r.content.decode("utf-8").strip()


if __name__ == "__main__":
    while not isNetChainOK():
        time.sleep(10)
        logger.info("No network connection, waiting...")

    while True:
        try:
            net_v6_address = get_v6_address_from_web()
            if not net_v6_address:
                exit(1)
            if ddns_refresh(net_v6_address):
                logger.info("DDNS refresh success")
        except Exception as e:
            logger.exception(e)

        time.sleep(60)
