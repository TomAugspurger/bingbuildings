from __future__ import annotations

import dataclasses
import functools
import importlib.resources
import json
import logging
from datetime import datetime, timezone
from typing import Any

import dateutil.parser
import mercantile
import shapely.geometry
import stac_table
from pystac import (
    Asset,
    CatalogType,
    Collection,
    Extent,
    Item,
    Link,
    MediaType,
    Provider,
    ProviderRole,
    RelType,
    SpatialExtent,
    TemporalExtent,
)
from pystac.extensions.item_assets import ItemAssetsExtension

logger = logging.getLogger(__name__)

ASSET_TITLE = "Building Footprints"
ASSET_DESCRIPTION = "Parquet dataset with the building footprints for this region."
GEOMETRY_DESCRIPTION = "Building footprint polygons"
# TODO: generalize to other storage
ASSET_EXTRA_FIELDS = {
    "table:storage_options": {"account_name": "bingmlbuildings"},
    "table:columns": [
        {
            "name": "geometry",
            "type": "byte_array",
            "description": GEOMETRY_DESCRIPTION,
        }
    ],
}


@functools.lru_cache
def get_data() -> dict[str, Any]:
    """
    Lookup metadata from a file provided by the footprints team.

    See `scripts/make_data.py`.
    """
    result = json.load(
        importlib.resources.open_text("stactools.msbuildings", "data.json")
    )
    assert isinstance(result, dict)
    return result


def create_collection(
    description: str | None = None, extra_fields: dict[str, Any] | None = None
) -> Collection:
    """Create a STAC Collection

    This function includes logic to extract all relevant metadata from
    an asset describing the STAC collection and/or metadata coded into an
    accompanying constants.py file.

    See `Collection<https://pystac.readthedocs.io/en/latest/api.html#collection>`_.

    Returns:
        Collection: STAC Collection object
    """
    providers = [
        Provider(
            name="Microsoft",
            roles=[ProviderRole.PRODUCER, ProviderRole.PROCESSOR, ProviderRole.HOST],
            url="https://planetarycomputer.microsoft.com",
        )
    ]

    start_datetime = datetime(2014, 1, 1, tzinfo=timezone.utc)

    extent = Extent(
        SpatialExtent([[-180.0, 90.0, 180.0, -90.0]]),
        TemporalExtent([[start_datetime, None]]),
    )

    links = [
        Link(
            rel=RelType.LICENSE,
            target="https://github.com/microsoft/GlobalMLBuildingFootprints/blob/main/LICENSE",
            media_type="text/html",
            title="ODbL-1.0 License",
        )
    ]
    keywords = [
        "Bing Maps",
        "Buildings",
        "geoparquet",
        "Microsoft",
        "Footprint",
    ]

    if description is None:
        description = (
            "Machine-learning detected building footprints. The underlying "
            "imagery is from Bing Maps and includes imagery from Maxar and Airbus."
        )

    collection = Collection(
        id="ms-buildings",
        title="Microsoft Building Footprints",
        description=description,  # noqa: E502
        license="ODbL-1.0",
        providers=providers,
        extent=extent,
        catalog_type=CatalogType.RELATIVE_PUBLISHED,
    )
    collection.links = links
    collection.keywords = keywords
    collection.add_asset(
        "thumbnail",
        Asset(
            "https://ai4edatasetspublicassets.blob.core.windows.net/assets/pc_thumbnails/msbuildings-thumbnail.png",  # noqa: E501
            title="Thumbnail",
            media_type=MediaType.PNG,
        ),
    )

    ItemAssetsExtension.add_to(collection)
    collection.extra_fields["item_assets"] = {
        "data": {
            "type": stac_table.PARQUET_MEDIA_TYPE,
            "title": ASSET_TITLE,
            "roles": ["data"],
            "description": ASSET_DESCRIPTION,
            **ASSET_EXTRA_FIELDS,
        }
    }

    if extra_fields:
        collection.extra_fields.update(extra_fields)

    return collection


@dataclasses.dataclass
class PathParts:
    """
    Parse a path like

    footprints/delta/2023-04-25/ml-buildings.parquet/RegionName=Abyei/quadkey=122321003/

    into its component parts.
    """

    path: str

    def __post_init__(self) -> None:
        split = self.path.rstrip("/").split("/")
        region_part = split[-2]
        datetime_part = split[-4]
        quadkey_part = split[-1]

        self.region = region_part.split("=", 1)[-1]
        self.datetime = dateutil.parser.parse(datetime_part).astimezone(timezone.utc)
        self.quadkey = int(quadkey_part.split("=")[1])


def create_item(
    asset_href: str,
    storage_options: dict[str, Any] | None = None,
    asset_extra_fields: dict[str, Any] | None = None,
) -> Item:
    """Create a STAC Item

    For

    Args:
        asset_href (str): The HREF pointing to an asset associated with the item

    Returns:
        Item: STAC Item object
    """
    parts = PathParts(asset_href)

    data = get_data().get(parts.region, {})

    start_datetime = data.get("MinCaptureDate")
    end_datetime = data.get("MaxCaptureDate")

    has_data = bool(data)
    properties = {
        "title": "Building footprints",
        "description": "Parquet dataset with the building footprints",
        "msbuildings:region": parts.region,
        "msbuildings:quadkey": parts.quadkey,
        "msbuildings:processing-date": parts.datetime.date().isoformat(),
    }

    tile = mercantile.quadkey_to_tile(str(parts.quadkey))
    bbox = mercantile.bounds(tile)
    shape = shapely.geometry.box(*bbox)

    geometry = shapely.geometry.mapping(shape)
    bbox = list(shape.bounds)

    if has_data:
        datetime = None
        properties.update(
            {"start_datetime": start_datetime, "end_datetime": end_datetime}
        )
    else:
        datetime = parts.datetime

    template = Item(
        id="_".join(
            [parts.region, str(parts.quadkey), parts.datetime.date().isoformat()]
        ),
        properties=properties,
        geometry=geometry,
        bbox=bbox,
        datetime=datetime,
        stac_extensions=[],
    )
    item = stac_table.generate(
        asset_href,
        template,
        storage_options=storage_options,
        asset_extra_fields=asset_extra_fields,
        infer_bbox=not has_data,
        infer_geometry=False,
        proj=False,
        count_rows=not has_data,
    )
    assert isinstance(item, Item)

    if has_data:
        item.properties["table:row_count"] = data["Count"]
    else:
        item.properties.pop("proj:bbox")

    item.properties["table:columns"][0]["description"] = GEOMETRY_DESCRIPTION

    # TODO: make configurable upstream
    item.assets["data"].title = ASSET_TITLE
    item.assets["data"].description = ASSET_DESCRIPTION

    return item
