import json
from pathlib import Path
from avro.schema import parse


def load_all_schemas():
    """Load all Avro schemas from .avsc files in this directory."""
    schema_dir = Path(__file__).parent
    schemas = {}

    schema_files = [
        "alerts_raw.avsc",
        "telegram_raw.avsc",
        "osint_batch.avsc",
        "weather_raw.avsc",
        "features_online.avsc",
        "predictions.avsc"
    ]

    for filename in schema_files:
        schema_path = schema_dir / filename
        with open(schema_path, 'r') as f:
            schema_dict = json.load(f)
        parsed_schema = parse(json.dumps(schema_dict))
        schema_name = schema_dict['name']
        schemas[schema_name] = parsed_schema

    return schemas


def get_schema(schema_name):
    """Get a specific schema by name."""
    schemas = load_all_schemas()
    return schemas.get(schema_name)
