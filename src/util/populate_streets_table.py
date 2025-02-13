from pathlib import Path
import json
from typing import List, Dict
import logging
from src.database.database import db
from src.models.street import Street

logger = logging.getLogger(__name__)

class StreetDataLoader:
    def __init__(self, filepath: Path):
        self.filepath = Path(filepath)

    def load_streets_from_json(self) -> List[Dict]:
        """Load and parse street data from JSON file."""
        if not self.filepath.exists():
            raise FileNotFoundError(f"File not found: {self.filepath}")

        features = []
        try:
            with self.filepath.open('r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if isinstance(data, dict):
                            features.append(data)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse line: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise

        return features

    def populate_streets(self) -> None:
        """Populate streets table with data."""
        # Create tables first
        logger.info("Creating database tables...")
        db.create_all()

        logger.info("Loading street data...")
        streets_data = self.load_streets_from_json()

        logger.info(f"Found {len(streets_data)} streets to import")

        with db.session() as session:
            for street_data in streets_data:
                properties = street_data['properties']
                geometry = json.dumps(street_data['geometry'])

                street = Street(
                    street_name=properties['street'],
                    postal_code=properties['postcode'],
                    city=properties['city'],
                    district=properties['district'],
                    state=properties['region'],
                    geometry=geometry
                )
                session.add(street)

            logger.info("Committing data to database...")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        loader = StreetDataLoader(Path("lesser-poland-street-names.geojson"))
        loader.populate_streets()
        logger.info("Successfully populated streets table")
    except Exception as e:
        logger.error(f"Failed to populate streets table: {e}")
        raise

if __name__ == '__main__':
    main()
