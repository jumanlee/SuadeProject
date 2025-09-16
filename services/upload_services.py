import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any, Set
from fastapi import HTTPException               
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from models.models import User, Product, Transaction

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
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")

    except ValueError:
        try:
            #try without microseconds
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid timestamp format: {timestamp_str}, make sure it's in '%Y-%m-%d %H:%M:%S' or '%Y-%m-%d %H:%M:%S.%f' format")

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

async def upsert_users(session: AsyncSession, user_ids: Set[int]) -> int:
    if not user_ids:
        return 0
    sql = (
        #insert is imported from sqlalchemy.dialects.postgresql
        #insert to User table
        #INSERT INTO users (id) VALUES (101), (102), (103)
        #.on_conflict_do_nothing for if a row with the same id already exists, just skip it. Don’t throw an error.
        insert(User)
        .values([{"id": user_id} for user_id in user_ids])
        .on_conflict_do_nothing(index_elements=[User.id])
    )

    result = await session.execute(sql)
    return result.rowcount or 0

#upsert products
async def upsert_products(session: AsyncSession, product_ids: Set[int]) -> int:
    if not product_ids:
        return 0
    sql = (
        insert(Product)
        .values([{"id": product_id} for product_id in product_ids])
        .on_conflict_do_nothing(index_elements=[Product.id])
    )

    result = await session.execute(sql)
    return result.rowcount or 0

    
async def insert_transactions(session: AsyncSession, rows: List[Dict[str, Any]]) -> tuple[int, int]:
    if not rows:
        return (0, 0)
    sql = (
        insert(Transaction)
        .values(rows)
        .on_conflict_do_nothing(index_elements=[Transaction.transaction_id])

        #better not use the following .returning, as it may return large number of rows, causing performance issues
        # .returning(Transaction.id) 
    )

    result = await session.execute(sql)
    inserted_count = result.rowcount or 0
    duplicates_ignored = len(rows) - inserted_count
    return (inserted_count, duplicates_ignored)
