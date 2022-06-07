import datetime

import requests

from stactools.msbuildings import stac


def test_collection() -> None:
    result = stac.create_collection()
    assert result.links
    assert result.keywords
    assert "thumbnail" in result.assets
    assert "item_assets" in result.extra_fields


def test_create_item() -> None:
    token = requests.get(
        "https://planetarycomputer-staging.microsoft.com/api/sas/v1/token/bingmlbuildings/footprints"  # noqa: E501
    ).json()["token"]
    asset_href = (
        "abfs://footprints/sample/2022-06-01/ml-buildings.parquet/RegionName=Abyei/"
    )

    item = stac.create_item(
        asset_href,
        asset_extra_fields={
            "table:storage_options": {"account_name": "bingmlbuildings"}
        },
        storage_options={"account_name": "bingmlbuildings", "credential": token},
    )
    item.validate()

    assert item.id == "Abyei_2022-06-01"
    assert item.bbox
    assert item.geometry
    assert item.datetime is None
    assert item.properties["start_datetime"] == "2016-03-31T00:00:00+00:00"
    assert item.properties["end_datetime"] == "2016-06-20T00:00:00+00:00"
    assert item.assets["data"].to_dict() == {
        "href": "abfs://footprints/sample/2022-06-01/ml-buildings.parquet/RegionName=Abyei/",
        "roles": ["data"],
        "title": "Building Footprints",
        "type": "application/x-parquet",
        "description": "Parquet dataset with the building footprints for this region.",
        "table:storage_options": {"account_name": "bingmlbuildings"},
    }

    assert item.properties["table:columns"] == [
        {"name": "geometry", "type": "byte_array"}
    ]
    assert item.properties["table:row_count"] == 171
    assert "proj:bbox" not in item.properties


def test_create_item_no_metadata() -> None:
    token = requests.get(
        "https://planetarycomputer-staging.microsoft.com/api/sas/v1/token/bingmlbuildings/footprints"  # noqa: E501
    ).json()["token"]
    asset_href = (
        "abfs://footprints/sample/2022-06-01/ml-buildings.parquet/RegionName=Canada/"
    )

    item = stac.create_item(
        asset_href,
        asset_extra_fields={
            "table:storage_options": {"account_name": "bingmlbuildings"}
        },
        storage_options={"account_name": "bingmlbuildings", "credential": token},
    )
    item.validate()

    assert item.id == "Canada_2022-06-01"
    assert item.bbox
    assert item.geometry
    assert item.datetime == datetime.datetime(
        2022, 6, 1, 5, 0, tzinfo=datetime.timezone.utc
    )
    assert item.assets["data"].to_dict() == {
        "href": "abfs://footprints/sample/2022-06-01/ml-buildings.parquet/RegionName=Canada/",
        "roles": ["data"],
        "title": "Building Footprints",
        "type": "application/x-parquet",
        "description": "Parquet dataset with the building footprints for this region.",
        "table:storage_options": {"account_name": "bingmlbuildings"},
    }

    assert item.properties["table:columns"] == [
        {"name": "geometry", "type": "byte_array"}
    ]
    assert item.properties["table:row_count"] == 590145
    assert "proj:bbox" not in item.properties
