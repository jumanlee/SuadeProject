import io
import uuid
import csv
from pathlib import Path
import pytest

#mark pytest as asyncio test
@pytest.mark.asyncio
async def test_upload_csv(client):
    #use existing .csv test data
    #.resolve() gets the absolute path, .parents[1] goes up two levels from current file (tests/) to project root, then /data/test_data.csv
    #for reference, parents[0] is data/
    csv_path = Path(__file__).resolve().parents[1] / "data" / "test_data.csv"

    #read the file as raw bytes, because upload endpoint expects to receive a file in an HTTP reques in raw bytes
    payload = csv_path.read_bytes()

    resp = await client.post(
        "/upload/",
        #"text/csv" is MIME type telling the kind of file being uploaded
        files={"file": (csv_path.name, payload, "text/csv")},
    )

    #resp.text is response body as text, for debugging, error message and etc
    assert resp.status_code == 200, resp.text

    data = resp.json()

    #sanity checks
    assert "row_count" in data
    assert "transaction_count" in data
    assert "duplicates_ignored" in data
    assert "user_count" in data
    assert "product_count" in data

@pytest.mark.asyncio
async def test_upload_rejects_non_csv(client):
    resp = await client.post(
        "/upload/",
        files={"file": ("notcsv.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code == 400
    assert "Only CSV files are supported" in resp.text