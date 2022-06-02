import json

import pandas as pd


def convert(path: str) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        parse_dates=["MinCaptureDate", "MaxCaptureDate"],
        index_col="RegionName",
    )
    df["MaxCaptureDate"] = [
        x.isoformat()
        for x in df.MaxCaptureDate.dt.tz_localize("UTC").dt.to_pydatetime()
    ]
    df["MinCaptureDate"] = [
        x.isoformat()
        for x in df.MinCaptureDate.dt.tz_localize("UTC").dt.to_pydatetime()
    ]
    with open("src/stactools/msbuildings/data.json", "w") as f:
        json.dump(df.to_dict(orient="index"), f)
