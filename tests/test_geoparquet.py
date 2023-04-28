import json
import pathlib

import pyarrow.parquet
from stactools.msbuildings.geoparquet import add_geo_metadata

HERE = pathlib.Path(__file__).parent


def test_add_geo_metadata():
    table = pyarrow.parquet.read_table(HERE / "data" / "no_metadata.parquet")
    result = add_geo_metadata(table, geometry_types=[])
    geo_md = json.loads(result.schema.metadata[b"geo"])

    assert b"org.apache.spark.version" in result.schema.metadata

    assert geo_md["version"] == "1.0.0-beta.1"
    assert geo_md["primary_column"] == "geometry"

    geo = geo_md["columns"]["geometry"]
    assert geo["encoding"] == "WKB"
    assert geo["crs"]
    assert geo["bbox"]