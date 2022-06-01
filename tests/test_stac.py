import requests

from stactools.bingbuildings import stac


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
        "abfs://footprints/geo/2022-05-25/ml-buildings.parquet/RegionName=Abyei/"
    )

    item = stac.create_item(
        asset_href,
        asset_extra_fields={
            "table:storage_options": {"account_name": "bingmlbuildings"}
        },
        storage_options={"account_name": "bingmlbuildings", "credential": token},
    )
    item.validate()

    assert item.id == "Abyei"
    assert item.bbox
    assert item.geometry
    assert item.assets["data"].to_dict() == {
        "href": "abfs://footprints/geo/2022-05-25/ml-buildings.parquet/RegionName=Abyei/",
        "roles": ["data"],
        "title": "Building Footprints",
        "type": "application/x-parquet",
        "description": "Parquet dataset with the building footprints for this region.",
        "table:storage_options": {"account_name": "bingmlbuildings"},
    }

    assert item.properties["datetime"] == "2022-05-25T05:00:00Z"
    assert item.properties["table:columns"] == [
        {"name": "wkbBuilding", "type": "byte_array"}
    ]
    assert item.properties["table:row_count"] == 11
