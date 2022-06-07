from __future__ import annotations

import dataclasses
import functools
import importlib.resources
import json
import logging
from datetime import datetime, timezone
from typing import Any

import dateutil.parser
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
# TODO: generalize to other storage
ASSET_EXTRA_FIELDS = {"table:storage_options": {"account_name": "bingmlbuildings"}}


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


def create_collection(extra_fields: dict[str, Any] | None) -> Collection:
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
    ]

    collection = Collection(
        id="bing-buildings",
        title="Bing Building Footprints",
        description="Machine-learning detected building footprints. The underlying imagery is from Bing Maps and includes imagery from Maxar and Airbus.",  # noqa: E501
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
            "https://github.com/microsoft/GlobalMLBuildingFootprints/blob/main/images/footprints-sample.png",  # noqa: E501
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
    Parse a path like "footprints/geo/2022-05-25/ml-buildings.parquet/RegionName=Abyei/"
    into its component parts.
    """

    path: str

    def __post_init__(self) -> None:
        region_part = self.path.rstrip("/").split("/")[-1]
        datetime_part = self.path.rstrip("/").split("/")[-3]

        self.region = region_part.split("=", 1)[-1]
        self.datetime = dateutil.parser.parse(datetime_part).astimezone(timezone.utc)


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
    }
    if has_data:
        datetime = None
        geom = shapely.geometry.box(
            data["MinCentroidLongitude"],
            data["MinCentroidLatitude"],
            data["MaxCentroidLongitude"],
            data["MaxCentroidLatitude"],
        )
        geometry = shapely.geometry.mapping(geom)
        bbox = list(geom.bounds)
        properties.update(
            {"start_datetime": start_datetime, "end_datetime": end_datetime}
        )
    else:
        datetime = parts.datetime
        geometry = bbox = None

    template = Item(
        id=parts.region,
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

    # TODO: make configurable upstream
    item.assets["data"].title = ASSET_TITLE
    item.assets["data"].description = ASSET_DESCRIPTION

    return item
