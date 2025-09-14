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

def insert_row(row:Dict[str, str]):

    #transaction_id. This becomes uuid.UUID object
    try:
        transaction_id = uuid.UUID(row["transaction_id"])
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {row['transaction_id']}")

    
    #user_id and product_id
    try:
        user_id = int(row["user_id"])
        product_id = int(row["product_id"])
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid user_id or product_id: {row['user_id']}, {row['product_id']}")
