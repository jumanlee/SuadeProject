# Suade Project

## Setup
Make sure you have Docker Desktop running in the backround.

Then start the Docker container:

```bash
docker compose up --build
```
Once started, then generate the dummy data (1 million rows):
```bash
docker compose exec app python3 data_dummy.py
```
You'll then have dummy_transactions.csv in the root directory. Note that Bind mount is already activated in Docker Compose, so you should be able to see this in the project root directory.

## As setup by Docker Compose, the PostgreSQL database can be viewed with admine and accessed here:
```bash
http://localhost:8080/
```

### PostgreSQL database credentials (fine to disclose here as it's just a test app):
Select PostgreSQL, then:
- **Username:** `app`  
- **Password:** `app`  
- **Database name:** `suade`  

## API commands:

### upload/ endpoint:
Upload dummy_transactions.csv onto the database:

```bash
curl -X POST "http://localhost:8000/upload/" \
  -H "Accept: application/json" \
  -F "file=@./dummy_transactions.csv;type=text/csv"
```



### summary/ endpoint:

#### For more concise illustration, I will just use user_id=709, please feel free to change the variables e.g. user_id and etc for your own use cases.

For user_id=709 with no date filters:
```bash
curl -X GET "http://localhost:8000/summary/709"
```

#### For start date only (inclusive):
All transactions where timestamp >= 2025-01-01 00:00:00
```bash
curl -X GET "http://localhost:8000/summary/709?start=2025-01-01"
```

#### For end date only (exclusive):
All transactions where timestamp < 2025-07-01 00:00:00
```bash
curl -X GET "http://localhost:8000/summary/709?end=2025-07-01"
```

#### For date range with ISO-8601 T format:
```bash
curl -X GET "http://localhost:8000/summary/709?start=2025-04-29T10:26:46&end=2025-07-01T00:00:00"
```

#### Date range with a space
```bash
curl -X GET "http://localhost:8000/summary/709?start=2025-04-29%2010:26:46&end=2025-07-01%2000:00:00"
```

#### Date range only
Equivalent to 2025-04-29 00:00:00 ≤ timestamp < 2025-07-01 00:00:00

```bash
curl -X GET "http://localhost:8000/summary/709?start=2025-04-29&end=2025-07-01"
```

## To execute Pytest to test the endpoints:
### This runs all tests inside the container
```bash
docker compose exec app python3 -m pytest -v
```

## To teardown the container:

### Teardown container without removing database data:
```bash
docker compose down
```
### Teardown container AND remove database data:
```bash
docker compose down -v
```
Note: If bind mount remains activated, those files are on your host disk and won’t be deleted by -v. Only Docker-managed volumes get removed.