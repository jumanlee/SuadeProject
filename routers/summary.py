from datetime import datetime, date, time
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from models.models import Transaction
from models.schemas import Summary

router = APIRouter()

#check and parse the datetime
def parse_datetime(date_raw: str | datetime | date | None) -> Optional[datetime]:
    if not date_raw:
        return None

    #if already datetime, just return
    if isinstance(date_raw, datetime):
        #check there's no timezone, just in case, as the raw data doesn't have timezone, for this mini project we're assuming there's no timezone.
        if date_raw.tzinfo is not None: 
            raise HTTPException(status_code=400, detail="Datetime with timezone is not supported")
        return date_raw

    if isinstance(date_raw, date):
        #time min would give 00:00:00
        return datetime.combine(date_raw, time.min)

    if isinstance(date_raw, str):
        try:
            #if only date but no time, in "YYYY-MM-DD" format
            if len(date_raw) == 10 and date_raw[4] == "-" and date_raw[7] == "-":
                #date.fromisoformat() is a built-in method from Python, parses string to date object 
                return datetime.combine(date.fromisoformat(date_raw), time.min)
            return datetime.fromisoformat(date_raw)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid datetime format: {date_raw}, must be in e.g. '2023-10-05' or '2023-10-05 00:00:00'")

    raise HTTPException(status_code=422, detail="Invalid datetime input: must be in e.g. '2023-10-05' or '2023-10-05 00:00:00'")



#added response_model_exclude_none=True so null fields are not ommited
@router.get("/{user_id}", response_model=Summary, response_model_exclude_none=True)
async def get_summary(
    user_id: int,
    start: Optional[str] = Query(None, description="format in e.g. 2023-10-05 00:00:00"),
    end: Optional[str]   = Query(None, description="format in e.g. 2023-10-05 00:00:00"),
    session: AsyncSession = Depends(get_session),
):

    parsed_start = parse_datetime(start)
    parsed_end = parse_datetime(end)

    #check validity of dates
    if parsed_start and parsed_end and not (parsed_start < parsed_end):
        raise HTTPException(status_code=422, detail="`end` must be greater than `start`")
    
    #build the conditions for query filter
    conditions = [Transaction.user_id == user_id]
    if parsed_start:
        conditions.append(Transaction.timestamp >= parsed_start)
    if parsed_end:
        conditions.append(Transaction.timestamp < parsed_end)

    sql = select(
        #SELECT COUNT(*) AS total FROM transactions; Knows it's transactions because of conditions = [Transaction.user_id == user_id]
        func.count().label("total"),

        func.min(Transaction.transaction_amount).label("min_amount"),
        func.max(Transaction.transaction_amount).label("max_amount"),
        func.avg(Transaction.transaction_amount).label("mean_amount"),
    ).where(*conditions)

    #result object
    result = await session.execute(sql)

    #return only one row (should only be one row) and if not, then crash
    total, min_amount, max_amount, mean_amount = result.one()

    if total == 0:
        raise HTTPException(status_code=404, detail="No data for given filters")

    return Summary(
        user_id=user_id,
        start_date=parsed_start,
        end_date=parsed_end,
        transaction_count=total,
        mean=mean_amount,
        maximum=max_amount,
        minimum=min_amount,
    )





