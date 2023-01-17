from src.post_orm import Database, Column, Table, ForeignKey

db = Database(
    database="test_database",
    user="postgres",
    password="1234",
    host="localhost",
    port="5432",
)

#  Create tables
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
harrys_school = db.query(Student, name="Harry Potter", limit=1).school
hogwarts = db.query(School, country="Eng%", limit=1)  # use % for wildcard search.
print(harrys_school.country, hogwarts.country)
assert harrys_school.country == hogwarts.country
