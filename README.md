# PostgreSQL Python ORM
A minimal Python ORM for interacting with a PostgreSQL database (using [psycopg2](https://pypi.org/project/psycopg2/)) <br />

Run the test suite against a postgres container in docker. <br />
``` docker run --rm -P -p 127.0.0.1:5432:5432 -e POSTGRES_PASSWORD="1234" --name pg postgres:alpine``` <br />
```psql postgresql://postgres:1234@localhost:5432/postgres``` <br />
```CREATE DATABASE test_database``` <br />
Preferably installation the ORM in a virtual environment.
```pip install -r requirements.txt```<br />
```python -m pytest .```<br />

The code is heavily inspiered by the SQLite ORM in [this course](https://testdriven.io/authors/rahmonov/) on testdriven.io


