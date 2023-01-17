# PostgreSQL Python ORM
A minimal Python ORM for interacting with a PostgreSQL database (using [psycopg2](https://pypi.org/project/psycopg2/)) <br />

## Installation

```bash
pip install post-orm
```
## Example
```python
from post_orm import Database, Column, Table, ForeignKey

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
harrys_school = db.query(Student, name="Harry Potter", limit=1).school # use limit=1 to return a single object.
hogwarts = db.query(School, country="Eng%", limit=1)  # use % for wildcard search.

assert harrys_school.country == hogwarts.country
```

## Run tests in Docker <br />
Prepare a test-databse
```
docker run --rm -P -p 127.0.0.1:5432:5432 -e POSTGRES_PASSWORD="1234" --name pg postgres:alpine
psql postgresql://postgres:1234@localhost:5432/postgres
CREATE DATABASE test_database;
```
Run tests 
```
python -m pytest .
```
This project was heavily inspiered by the SQLite ORM in [this course](https://testdriven.io/authors/rahmonov/) on testdriven.io
