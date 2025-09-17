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