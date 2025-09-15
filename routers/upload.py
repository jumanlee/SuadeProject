from schemas import UploadData, ErrorResponse, Summary
import csv
import io
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any, Set

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from database import get_session
from models import User, Product, Transaction  


#there are only 2 endpoints for this project, I don't think s#ervices layer/folder is necessary. 

#creates a router object so that can define endpoints 
router = APIRouter()

headers = ["transaction_id", "user_id", "product_id", "timestamp", "transaction_amount"]

#number of rows to insert in one batch, for faster performance, for each insert operation
batch_size = 10000 

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
        .on_conflict_do_nothing(index_elements=["id"])
    )

    await session.execute(sql)
    return len(user_ids)

#upsert products
async def upsert_products(session: AsyncSession, product_ids: Set[int]) -> int:
    if not product_ids:
        return 0
    sql = (
        insert(Product)
        .values([{"id": product_id} for product_id in product_ids])
        .on_conflict_do_nothing(index_elements=["id"])
    )

    await session.execute(sql)
    return len(product_ids)

    
async def insert_transactions(session: AsyncSession, rows: List[Dict[str, Any]]) -> tuple[int, int]:
    if not rows:
        return (0, 0)
    sql = (
        insert(Transaction)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["transaction_id"])
        .returning(Transaction.id)
    )

    result = await session.execute(sql)
    inserted_ids = result.scalars().all()
    inserted_count = len(inserted_ids)
    duplicates_ignored = len(rows) - inserted_count
    return (inserted_count, duplicates_ignored)


    
@router.post("/", response_model=UploadData, responses={400: {"model": ErrorResponse}})
async def upload_data(
    #file is param name, UploadFile type hint to tell gastAPI is an uploaded file
    #File(...) tells FastAPI the source that this comes from a file upload in the request body
    #if didn’t use File(...), would have to manually dig the file out of the request body. FastAPI does that for us, acts as a marker
    file: UploadFile=File(...),
    #Depends(get_session) means before calling this endpoint, run get_session() and pass its return value in here
    session: AsyncSession = Depends(get_session),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    

    #wrap uploaded file for csv.DictReader, which expects a text stream
    try:
        #file.file is the underlying raw file object or binary stream
        #TextIOWrapper wraps a binary stream (bytes) and turns it into a text stream (str)
        text = io.TextIOWrapper(file.file, encoding="utf-8", newline="")
        reader = csv.DictReader(text)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Unable to read CSV. {error}")


    #check the header
    if reader.fieldnames is None:
        raise HTTPException(status_code=400, detail="Missing CSV header")
    
    normalised_headers = [header.strip().lower() for header in reader.fieldnames]

    if normalised_headers != headers:
        raise HTTPException(status_code=400, detail=f"Invalid CSV header. Expected: {headers}, got: {normalised_headers}")

    rows_inserted: int = 0
    users_upserted: int = 0
    duplicates_ignored: int = 0
    products_upserted: int = 0
    
   #batch sets
    user_ids_batch: Set[int] = set()
    product_ids_batch: Set[int] = set()
    transactions_batch: List[Dict[str, Any]] = []

    async with session.begin():
        for row in reader:
            try:
                transformed_row = transform_row(row)
            except HTTPException as e:
                raise HTTPException(status_code=400, detail=f"Error in row {reader.line_num}: {e.detail}")

            user_ids_batch.add(transformed_row["user_id"])
            product_ids_batch.add(transformed_row["product_id"])
            transactions_batch.append(transformed_row)

            if len(transactions_batch) >= batch_size:

                #insert or update users, products and transactions in batches

                users_upserted += await upsert_users(session, user_ids_batch)
                products_upserted += await upsert_products(session, product_ids_batch)
                #don't upsert transacitons, need to record duplicates ignored
                inserted, duplicates = await insert_transactions(session, transactions_batch)
                rows_inserted += inserted
                duplicates_ignored += duplicates

                user_ids_batch.clear()
                product_ids_batch.clear()
                transactions_batch.clear()

        #insert any remaining rows in the last batch
        if transactions_batch:
            users_upserted += await upsert_users(session, user_ids_batch)
            products_upserted += await upsert_products(session, product_ids_batch)
            inserted, duplicates = await insert_transactions(session, transactions_batch)
            rows_inserted += inserted
            duplicates_ignored += duplicates

        row_count = rows_inserted + duplicates_ignored
        
        #return uploade results based on schema
        return UploadData(
            row_count=row_count,
            user_count=users_upserted,
            product_count=products_upserted,
            transaction_count=rows_inserted,
            duplicates_ignored=duplicates_ignored,
        )
                    

    

               