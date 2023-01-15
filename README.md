# PostgreSQL Python ORM
A minimal Python ORM for interacting with a PostgreSQL database (using [psycopg2](https://pypi.org/project/psycopg2/)) <br />

## Example
```python
from psql_orm import Database, Column, Table, ForeignKey

db = Database(
    database="test_database",
    user="postgres",
    password="1234",
    host="localhost",
    port="5432",
)

# Create tables
class School(Table):
    country = Column(str)
    name = Column(str)


class Student(Table):
    name = Column(str)
    school = ForeignKey(School)


db.create(School)
db.create(Student)

# Save school
school = School(name="Hogwarts", country="England")
db.save(school)

# Save students
harry = Student(name="Harry Potter", school=school)
ron = Student(name="Ron Weasley", school=school)
db.save([harry, ron])

# Make queries
all_students = db.all(Student)
harrys_school = db.query(Student, name="Harry Potter", limit=1).school # appends "LIMIT 1" to SQL query.
hogwarts = db.query(School, country="Eng%", limit=1)  # use % for wildcard search.
print(harrys_school.country, hogwarts.country)
assert harrys_school.country == hogwarts.country
```

## Run the test suite against a postgres container in docker. <br />
``` docker run --rm -P -p 127.0.0.1:5432:5432 -e POSTGRES_PASSWORD="1234" --name pg postgres:alpine``` <br />
```psql postgresql://postgres:1234@localhost:5432/postgres``` <br />
```CREATE DATABASE test_database;``` <br />
Preferably installation the ORM in a virtual environment.
```pip install -e .```<br />
```python -m pytest .```<br />

The code is heavily inspiered by the SQLite ORM in [this course](https://testdriven.io/authors/rahmonov/) on testdriven.io
