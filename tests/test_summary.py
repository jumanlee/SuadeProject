import io
import uuid
import csv
from decimal import Decimal
import pytest


@pytest.mark.asyncio
async def test_summary(client):

    csv_path = Path(__file__).resolve().parents[1] / "data" / "test_summary_data.csv"
    payload = csv_path.read_bytes()

    #upload sample data
    upload = await client.post("/upload/", files={"file": (csv_path.name, payload, "text/csv")})
    assert upload.status_code == 200, upload.text

    #get summary for user=1: count=3, min=45.97, max=215.05, mean=147.29 but no dates.
    req = await client.get("/summary/1")
    assert req.status_code == 200, req.text
    data = req.json()
    assert data["user_id"] == 1
    assert data["transaction_count"] == 2
    #JSON may serialize Decimal as string, normalise via Decimal
    assert Decimal(str(data["minimum"])) == Decimal("45.97")
    assert Decimal(str(data["maximum"])) == Decimal("215.05")
    assert Decimal(str(data["mean"])) == Decimal("147.29")

    req2 = await client.get("/summary/1", params={"start": "2025-02-21", "end": "2025-07-02"})
    assert req2.status_code == 200, req2.text
    data2 = req2.json()
    assert data2["transaction_count"] == 3
    assert Decimal(str(data2["minimum"])) == Decimal("180.84")
    assert Decimal(str(data2["maximum"])) == Decimal("215.05")
    assert Decimal(str(data2["mean"])) == Decimal("197.95")

#send request but no data in the database
@pytest.mark.asyncio
async def test_summary_no_data(client):
    req = await client.get("/summary/999999")
    assert req.status_code == 404
    assert "No data for given filters" in req.text


#test date range logic
@pytest.mark.asyncio
async def test_summary_end_less_start(client):
    csv_path = Path(__file__).resolve().parents[1] / "data" / "test_summary_data.csv"
    payload = csv_path.read_bytes()

    upload = await client.post("/upload/", files={"file": (csv_path.name, payload, "text/csv")})
    assert upload.status_code == 200, upload.text

    #if end date is before start date should return 422
    req = await client.get("/summary/1", params={"start": "2025-01-03", "end": "2025-01-02"})
    assert req.status_code == 422
    assert "end must be greater than start" in req.text

    #wrong input date format
    req = await client.get("/summary/1", params={"start": "2025-01-01"})
    assert req.status_code == 422
    assert "end must be greater than start" in req.text
