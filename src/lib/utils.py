import urllib.parse

from src.db.models import Onsen


def generate_google_maps_link(onsen: Onsen) -> str:
    """Generate a Google Maps link for an onsen."""
    if onsen.latitude is not None and onsen.longitude is not None:
        return f"https://maps.google.com/?q={onsen.latitude},{onsen.longitude}"
    elif onsen.address:
        # URL encode the address for Google Maps
        encoded_address = urllib.parse.quote(onsen.address)
        return f"https://maps.google.com/?q={encoded_address}"
    else:
        return "N/A"
