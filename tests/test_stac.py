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
    asset_href = "abfs://footprints/delta/2023-04-25/ml-buildings.parquet/RegionName=Abyei/quadkey=122321003/"  # noqa: E501

    item = stac.create_item(
        asset_href,
        asset_extra_fields={
            "table:storage_options": {"account_name": "bingmlbuildings"}
        },
        storage_options={"account_name": "bingmlbuildings", "credential": token},
    )
    item.validate()

    assert item.id == "Abyei_122321003_2023-04-25"
    assert item.bbox
    assert item.geometry
    assert item.datetime is None
    assert item.properties["start_datetime"] == "2016-03-31T00:00:00+00:00"
    assert item.properties["end_datetime"] == "2016-06-20T00:00:00+00:00"
    assert item.properties["msbuildings:region"] == "Abyei"
    assert item.properties["msbuildings:quadkey"] == 122321003
    assert item.properties["msbuildings:processing-date"] == "2023-04-25"
    assert item.assets["data"].to_dict() == {
        "href": "abfs://footprints/delta/2023-04-25/ml-buildings.parquet/RegionName=Abyei/quadkey=122321003/",  # noqa: E501
        "type": "application/x-parquet",
        "title": "Building Footprints",
        "description": "Parquet dataset with the building footprints for this region.",
        "table:storage_options": {"account_name": "bingmlbuildings"},
        "roles": ["data"],
    }

    assert item.properties["table:columns"] == [
        {
            "description": "Building footprint polygons",
            "name": "geometry",
            "type": "byte_array",
        },
        {"name": "meanHeight", "type": "float"},
    ]
    assert item.properties["table:row_count"] == 171
    assert "proj:bbox" not in item.properties
    assert item.geometry == {
        "coordinates": (
            (
                (29.53125, 9.795677582829734),
                (29.53125, 10.487811882056686),
                (28.828125, 10.487811882056686),
                (28.828125, 9.795677582829734),
                (29.53125, 9.795677582829734),
            ),
        ),
        "type": "Polygon",
    }
    assert item.bbox == [28.828125, 9.795677582829734, 29.53125, 10.487811882056686]
