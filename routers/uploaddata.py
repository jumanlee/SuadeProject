from schemas.schemas import UploadData, ErrorResponse, Summary
import csv
import io
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any, Set

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from database import get_session
from models.models import User, Product, Transaction  


#there are only 2 endpoints for this project, I don't think services layer/folder is necessary. 

headers = ["transaction_id", "user_id", "product_id", "timestamp", "transaction_amount"]

#number of rows to insert in one batch, for faster performance, for each insert operation
batch_size = 100000 

#parsed from csv.DictReader, which gives Dict[str, str]
def transform_row(row:Dict[str, str]):

    #csv values are all str, need to convert to appropriate types

    #transaction_id. This becomes uuid.UUID object
    try:
        transaction_id = uuid.UUID(row["transaction_id"])
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {row['transaction_id']}")

    
    #user_id and product_id, become int
    try:
        user_id = int(row["user_id"])
        product_id = int(row["product_id"])
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid user_id or product_id: {row['user_id']}, {row['product_id']}")

    #timestamp, become datetime object
    timestamp_str = (row.get("timestamp") or "").strip()
    if not timestamp_str:
        raise HTTPException(status_code=400, detail="Missing timestamp")
    try:
        #"%Y-%m-%d %H:%M:%S.%f" is the format for csv date time. No time zone not provided, so assume so and omit time zone info
        timestamp = datetime.strptime(timestamp_raw, "%Y-%m-%d %H:%M:%S.%f")

    except ValueError:
        try:
            #try without microseconds
            timestamp = datetime.strptime(timestamp_raw, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid timestamp format: {timestamp_raw}, make sure it's in '%Y-%m-%d %H:%M:%S' or '%Y-%m-%d %H:%M:%S.%f' format")

    #transaction_amount, become Decimal
    try:
        transaction_amount = Decimal(row["transaction_amount"]).quantize(Decimal("0.01"))
    except (InvalidOperation, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"Invalid transaction_amount: {row['transaction_amount']}, must be a decimal number with up to 2 decimal places")

    return {
        "transaction_id": transaction_id,
        "user_id": user_id,
        "product_id": product_id,   
        "timestamp": timestamp,
        "transaction_amount": transaction_amount,
    }
    





    
