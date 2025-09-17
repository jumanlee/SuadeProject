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
async def test_upload_non_csv(client):
    resp = await client.post(
        "/upload/",
        files={"file": ("notcsv.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code == 400
    assert "Only CSV files are supported" in resp.text

#if thee's invalid header
@pytest.mark.asyncio
async def test_upload_invalid_header(client):
    bad = b"bad,verybad,badbadbad\n"
    resp = await client.post(
        "/upload/",
        files={"file": ("bad.csv", bad, "text/csv")},
    )
    assert resp.status_code == 400
    assert "Invalid CSV header" in resp.text

#if there's a bad row, e.g. missing fields
@pytest.mark.asyncio
async def test_upload_row_error_invalid_uuid(client):

    csv_path = Path(__file__).resolve().parents[1] / "data" / "bad_data.csv"
    payload = csv_path.read_bytes()
    resp = await client.post("/upload/", files={"file": (csv_path.name, payload, "text/csv")})
    assert resp.status_code == 400
    assert "Invalid UUID" in resp.text


@pytest.mark.asyncio
async def test_upload_duplicates_ignored_on_second_upload(client):
    csv_path = Path(__file__).resolve().parents[1] / "data" / "duplicate_data.csv"
    payload = csv_path.read_bytes()
    resp = await client.post("/upload/", files={"file": (csv_path.name, payload, "text/csv")})

    #first upload: 2 actual inserts, 1 duplicate ignored
    resp1 = await client.post("/upload/", files={"file": ("dups.csv", payload, "text/csv")})
    assert resp1.status_code == 200, resp1.text
    d1 = resp1.json()
    assert d1["transaction_count"] == 2
    assert d1["duplicates_ignored"] == 1

    #second upload of identical file: all 3 are duplicates now, so 0 inserts, 3 duplicates ignored
    resp2 = await client.post("/upload/", files={"file": ("dups.csv", payload, "text/csv")})
    assert resp2.status_code == 200
    d2 = resp2.json()
    assert d2["transaction_count"] == 0
    assert d2["duplicates_ignored"] == 3



