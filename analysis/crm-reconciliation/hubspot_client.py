"""HubSpot REST v3 client using a Private App token.
Create one under HubSpot Settings > Integrations > Private Apps
with 'crm.objects.contacts.read' scope, and put it in .env as
HUBSPOT_PRIVATE_APP_TOKEN."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()
BASE_URL = "https://api.hubapi.com"


def search_contacts(segment: str, properties: list[str]) -> list[dict]:
    token = os.environ["HUBSPOT_PRIVATE_APP_TOKEN"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {
        "filterGroups": [{"filters": [
            {"propertyName": "trade_signal_segment", "operator": "EQ", "value": segment}
        ]}],
        "properties": properties,
        "limit": 100,
    }
    results, after = [], None
    while True:
        if after:
            body["after"] = after
        resp = requests.post(f"{BASE_URL}/crm/v3/objects/contacts/search", json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        results.extend(r["properties"] | {"id": r["id"]} for r in data["results"])
        after = data.get("paging", {}).get("next", {}).get("after")
        if not after:
            break
    return results
