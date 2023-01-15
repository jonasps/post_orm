# test_orm.py
import os
import psycopg2

import pytest

from src.psql_orm import Database, Table, Column, ForeignKey


# fixtures


@pytest.fixture
def Author():
    class Author(Table):
        name = Column(str)
        age = Column(int)

    return Author


@pytest.fixture
def Book(Author):
    class Book(Table):
        title = Column(str)
        published = Column(bool)
        author = ForeignKey(Author)

    return Book


# tests


@pytest.fixture
def db():
    db = Database(
        database="test_database",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432",
    )
    # BE AWARE, this will clear all tabels in the *test_database*.
    # Do not run agains any real data.
    cursor = db.conn.cursor()
    DROP_TABLES_SQL = "DROP SCHEMA public CASCADE;"
    CREATE_TABLES_SQL = "CREATE SCHEMA public;"
    cursor.execute(DROP_TABLES_SQL)
    db.conn.commit()
    cursor.execute(CREATE_TABLES_SQL)
    db.conn.commit()
    return db


def test_create_db(db):
    assert db.tables == []


def test_define_tables(Author, Book):
    assert Author.name.type == str
    assert Book.author.table == Author
    assert Author.name.sql_type == "TEXT"
    assert Author.age.sql_type == "INTEGER"


def test_create_tables(db, Author, Book):
    db.create(Author)
    db.create(Book)

    assert (
        Author._get_create_sql()
        == "CREATE TABLE IF NOT EXISTS author (id BIGSERIAL PRIMARY KEY, age INTEGER, name TEXT);"
    )
    assert (
        Book._get_create_sql()
        == "CREATE TABLE IF NOT EXISTS book (id BIGSERIAL PRIMARY KEY, author_fk INTEGER, published BOOL, title TEXT);"
    )

    for table in ("author", "book"):
        assert table in db.tables


def test_create_author_instance(db, Author):
    db.create(Author)

    john = Author(name="John Doe", age=25)

    assert john.name == "John Doe"
    assert john.age == 25
    assert john.id is None


def test_save_author_instances(db, Author):
    db.create(Author)

    john = Author(name="John", age=23)
    db.save(john)
    assert john._get_insert_sql() == (
        "INSERT INTO author (age, name) VALUES (%s, %s) RETURNING id;",
        [23, "John"],
    )
    assert john.id == 1

    man = Author(name="Man", age=28)
    db.save(man)
    assert man.id == 2

    vik = Author(name="Viktor", age=43)
    db.save(vik)
    assert vik.id == 3

    jack = Author(name="Jack", age=39)
    db.save(jack)
    assert jack.id == 4


def test_query_all_authors(db, Author):
    db.create(Author)
    john = Author(name="John Doe", age=23)
    vik = Author(name="Viktor", age=43)
    db.save(john)
    db.save(vik)

    authors = db.all(Author)

    assert Author._get_select_all_sql() == (
        "SELECT id, age, name FROM author;",
        ["id", "age", "name"],
    )
    assert len(authors) == 2
    assert type(authors[0]) == Author
    assert {a.age for a in authors} == {23, 43}
    assert {a.name for a in authors} == {"John Doe", "Viktor"}


def test_get_author(db, Author):
    db.create(Author)
    roman = Author(name="John Doe", age=43)
    db.save(roman)

    john_from_db = db.get(Author, id=1)

    assert Author._get_select_where_sql(id=1) == (
        "SELECT id, age, name FROM author WHERE id = %s;",
        ["id", "age", "name"],
        [1],
    )
    assert type(john_from_db) == Author
    assert john_from_db.age == 43
    assert john_from_db.name == "John Doe"
    assert john_from_db.id == 1


def test_get_book(db, Author, Book):
    db.create(Author)
    db.create(Book)
    john = Author(name="John Doe", age=43)
    abc = Author(name="ABC", age=50)
    book = Book(title="Building", published=False, author=john)
    book2 = Book(title="Scoring", published=True, author=abc)
    db.save(john)
    db.save(abc)
    db.save(book)
    db.save(book2)

    book_from_db = db.get(Book, 2)

    assert book_from_db.title == "Scoring"
    assert book_from_db.author.name == "ABC"
    assert book_from_db.author.id == 2


def test_query_all_books(db, Author, Book):
    db.create(Author)
    db.create(Book)
    john = Author(name="John Doe", age=43)
    arash = Author(name="ABC", age=50)
    book = Book(title="Building", published=False, author=john)
    book2 = Book(title="Scoring", published=True, author=arash)
    db.save(john)
    db.save(arash)
    db.save(book)
    db.save(book2)

    books = db.all(Book)

    assert len(books) == 2
    assert books[1].author.name == "ABC"


def test_query_with_limit(db, Author, Book):
    db.create(Author)
    db.create(Book)
    dostoevsky = Author(name="dostoevsky", age=43)
    hemingway = Author(name="Hemingway", age=50)
    book = Book(title="Notes from Underground", published=True, author=dostoevsky)
    book2 = Book(title="The old man and the sea", published=True, author=hemingway)
    book3 = Book(title="A Room on the Garden Side", published=False, author=hemingway)
    db.save(dostoevsky)
    db.save(hemingway)
    db.save(book)
    db.save(book2)
    db.save(book3)

    one = db.query(Book, title="%", limit=1)
    two = db.query(Book, title="%", limit=2)
    three = db.query(Book, title="%", limit=3)

    assert len(one.title)
    assert len(two) == 2
    assert len(three) == 3


def test_query_specific_book(db, Author, Book):
    db.create(Author)
    db.create(Book)
    dostoevsky = Author(name="dostoevsky", age=43)
    hemingway = Author(name="Hemingway", age=50)
    book = Book(title="Notes from Underground", published=True, author=dostoevsky)
    book2 = Book(title="The old man and the sea", published=True, author=hemingway)
    book3 = Book(title="A Room on the Garden Side", published=False, author=hemingway)
    db.save(dostoevsky)
    db.save(hemingway)
    db.save(book)
    db.save(book2)
    db.save(book3)

    wildcard = db.query(Book, title="Notes %", limit=1)
    not_published = db.query(Book, published=False, limit=1)

    assert wildcard.title == "Notes from Underground"
    assert not_published.title == "A Room on the Garden Side"


def test_update_author(db, Author):
    db.create(Author)
    john = Author(name="John Doe", age=23)
    db.save(john)

    john.age = 43
    john.name = "John Doe"
    db.update(john)

    john_from_db = db.get(Author, id=john.id)

    assert john_from_db.age == 43
    assert john_from_db.name == "John Doe"


def test_delete_author(db, Author):
    db.create(Author)
    john = Author(name="John Doe", age=23)
    db.save(john)

    db.delete(Author, id=1)

    with pytest.raises(Exception):
        db.get(Author, 1)
