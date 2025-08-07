import requests
from bs4 import BeautifulSoup
from loguru import logger
from sqlalchemy.orm import Session
from src.db.models import Onsen
from src.const import CONST


def import_onsen_data(db: Session):
    """
    Example function to fetch online data and store in the DB.
    For demonstration, this is a stub that does something minimal.
    """

    url = CONST.ONSEN_URL
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Failed to fetch onsen data from {url}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # Pseudocode: you would parse the HTML, extract fields, and then create Onsen entries
    for item in soup.select("div.onsen-item"):
        ban_number = item.get("data-ban", "000")
        name = item.select_one(".onsen-name").text.strip()

        # Use a dictionary or read from HTML to get the other fields
        address = item.select_one(".onsen-address").text.strip()
        # ... likewise for business form, phone, etc.

        # Check if it already exists in the DB
        existing = db.query(Onsen).filter(Onsen.ban_number == ban_number).first()
        if existing:
            logger.info(f"Onsen with ban_number={ban_number} already in DB, updating.")
            # Update fields if needed
            existing.name = name
            existing.address = address
        else:
            logger.info(f"Adding new onsen: {name}")
            new_onsen = Onsen(
                ban_number=ban_number,
                name=name,
                address=address,
                # ...
            )
            db.add(new_onsen)
    db.commit()


def main():
    """
    Example script entrypoint.
    Use this if you want to run data import from the command line:
    `poetry run python -m onsen_manager.data_import`
    """
    from src.db.conn import get_db

    with get_db(url=CONST.DATABASE_URL) as db:
        import_onsen_data(db)


if __name__ == "__main__":
    main()
