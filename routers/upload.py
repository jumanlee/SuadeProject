import csv
import io
from typing import List, Dict, Any, Set
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from models.schemas import UploadData, ErrorResponse
from services.upload_services import (
    transform_row,
    upsert_users,
    upsert_products,
    insert_transactions,
)

#creates a router object so that can define endpoints 
router = APIRouter()

headers = ["transaction_id", "user_id", "product_id", "timestamp", "transaction_amount"]

#number of rows to insert in one batch, for faster performance, for each insert operation
batch_size = 2000
    
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
                    

    

               