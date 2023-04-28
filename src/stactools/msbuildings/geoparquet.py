from __future__ import annotations

import jsonschema
import requests
import fsspec
import geopandas
import pyarrow.fs
import pyproj
import json
from typing import Any

storage_options = dict(account_name="bingmlbuildings", credential="")
SCHEMA = "https://raw.githubusercontent.com/opengeospatial/geoparquet/v1.0.0-beta.1/format-specs/schema.json"


def add_geo_metadata(
    table: pyarrow.Table,
    geometry_types: list[str] | None = None,
    geometry_name: str = "geometry",
    geoparquet_version: str = "1.0.0-beta.1",
    schema_url: str | None = SCHEMA,
):
    if b"geo" in table.schema.metadata:
        # Already present
        return table

    geometry_types = geometry_types or []
    bbox = list(geopandas.array.from_wkb(table[geometry_name].to_numpy()).total_bounds)

    geo_metadata = {
        "version": geoparquet_version,
        "primary_column": geometry_name,
        "columns": {
            geometry_name: {
                "encoding": "WKB",
                "crs": json.loads(pyproj.CRS("WGS 84").to_json()),
                "geometry_types": geometry_types,
                "bbox": bbox,
            }
        },
    }
    metadata = {
        **table.schema.metadata,
        b"geo": json.dumps(geo_metadata).encode(),
    }

    if schema_url:
        r = requests.get(schema_url)
        r.raise_for_status()
        d = r.json()

        jsonschema.validate(geo_metadata, d)

    metadata = {
        **table.schema.metadata,
        b"geo": json.dumps(geo_metadata).encode(),
    }
    new_table = table.replace_schema_metadata(metadata)
    return new_table


def update_many(
    protocol: str,
    prefix: str,
    geometry_types: list[str],
    geometry_name: str = "geometry",
    geoparquet_version: str = "1.0.0-beta.1",
    storage_options: dict[str, Any] | None = None,
    schema_url: str | None = SCHEMA,
) -> str:
    """
    Add geoparquet metadata to all parquet files in a directory.
    """
    storage_options = storage_options or {}
    fs = fsspec.filesystem(protocol, **storage_options)
    arrow_fs = pyarrow.fs.PyFileSystem(pyarrow.fs.FSSpecHandler(fs))

    for path in fs.find(prefix):
        table = pyarrow.parquet.read_table(path, filesystem=fs)
        new_table = add_geo_metadata(
            table,
            geometry_types=geometry_types,
            geometry_name=geometry_name,
            geoparquet_version=geoparquet_version,
            schema_url=schema_url,
        )
        # TODO: robust error handling here
        pyarrow.parquet.write_table(new_table, path, filesystem=arrow_fs)
    return prefix
