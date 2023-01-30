import inspect
import psycopg2


class Table:
    """Abstract class, inherit from this when declaring an ORM object."""

    def __init__(self, **kwargs) -> None:
        self._data = {
            "id": None,
        }

        for key, value in kwargs.items():
            self._data[key] = value

    def __getattribute__(self, key: str) -> str:
        _data = super().__getattribute__("_data")
        if key in _data:
            return _data[key]
        return super().__getattribute__(key)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if key in self._data:
            self._data[key] = value

    def _get_insert_sql(self):
        INSERT_SQL = (
            "INSERT INTO {name} ({fields}) VALUES ({placeholders}) RETURNING id;"
        )
        cls = self.__class__
        fields = []
        placeholders = []
        values = []

        for name, field in inspect.getmembers(cls):
            if isinstance(field, Column):
                fields.append(name)
                values.append(getattr(self, name))
                placeholders.append("%s")
            elif isinstance(field, ForeignKey):
                fields.append(name + "_fk")
                values.append(getattr(self, name).id)
                placeholders.append("%s")

        fields = ", ".join(fields)
        placeholders = ", ".join(placeholders)
        sql = INSERT_SQL.format(
            name=cls.__name__.lower(), fields=fields, placeholders=placeholders
        )

        return sql, values

    @classmethod
    def _get_select_all_sql(cls):
        SELECT_ALL_SQL = "SELECT {fields} FROM {name};"

        fields = ["id"]
        for name, field in inspect.getmembers(cls):
            if isinstance(field, Column):
                fields.append(name)
            if isinstance(field, ForeignKey):
                fields.append(name + "_fk")

        sql = SELECT_ALL_SQL.format(name=cls.__name__.lower(), fields=", ".join(fields))

        return sql, fields

    @classmethod
    def _get_query_sql(cls, query_items):
        where_clause = ""
        query_values = []
        for q in query_items:
            if not type(q[1]) == bool:
                where_clause += q[0] + " LIKE %s AND "
            else:
                where_clause += q[0] + " IS %s AND "
            query_values.append(q[1])
        where_clause = where_clause[:-5]
        SELECT_ALL_SQL = "SELECT {fields} FROM {name} WHERE {where_clause};"

        fields = ["id"]
        for name, field in inspect.getmembers(cls):
            if isinstance(field, Column):
                fields.append(name)
            if isinstance(field, ForeignKey):
                fields.append(name + "_fk")

        sql = SELECT_ALL_SQL.format(
            name=cls.__name__.lower(),
            fields=", ".join(fields),
            where_clause=where_clause,
        )

        return sql, fields, query_values

    @classmethod
    def _get_create_sql(cls):
        CREATE_TABLE_SQL = "CREATE TABLE IF NOT EXISTS {name} ({fields});"
        fields = [
            "id BIGSERIAL PRIMARY KEY",
        ]

        for name, field in inspect.getmembers(cls):
            if isinstance(field, Column):
                fields.append(f"{name} {field.sql_type}")
            elif isinstance(field, ForeignKey):
                fields.append(f"{name}_fk INTEGER")

        fields = ", ".join(fields)
        name = cls.__name__.lower()
        return CREATE_TABLE_SQL.format(name=name, fields=fields)

    @classmethod
    def _get_select_where_sql(cls, id):
        SELECT_WHERE_SQL = "SELECT {fields} FROM {name} WHERE id = %s;"

        fields = ["id"]
        for name, field in inspect.getmembers(cls):
            if isinstance(field, Column):
                fields.append(name)
            if isinstance(field, ForeignKey):
                fields.append(name + "_fk")

        sql = SELECT_WHERE_SQL.format(
            name=cls.__name__.lower(), fields=", ".join(fields)
        )
        params = [id]

        return sql, fields, params

    @classmethod
    def _get_delete_sql(cls, id):
        DELETE_SQL = "DELETE FROM {name} WHERE id = %s;"

        fields = ["id"]
        for name, field in inspect.getmembers(cls):
            if isinstance(field, Column):
                fields.append(name)
            if isinstance(field, ForeignKey):
                fields.append(name + "_fk")

        sql = DELETE_SQL.format(name=cls.__name__.lower())
        params = [id]

        return sql, params

    def _get_update_sql(self):
        UPDATE_SQL = "UPDATE {name} SET {fields} WHERE id = %s"
        cls = self.__class__
        fields = []
        values = []

        for name, field in inspect.getmembers(cls):
            if isinstance(field, Column):
                fields.append(name)
                values.append(getattr(self, name))
            elif isinstance(field, ForeignKey):
                fields.append(name + "_fk")
                values.append(getattr(self, name).id)

        values.append(getattr(self, "id"))

        sql = UPDATE_SQL.format(
            name=cls.__name__.lower(),
            fields=", ".join([f"{field} = %s" for field in fields]),
        )

        return sql, values


class ForeignKey:
    """Declares foreign key relationships between ORM objects.

    Use ´name = ForeignKey(*ORM Object*)´ to declare a class variables just ´Column´.
    """

    def __init__(self, table) -> None:
        self.table = table


class Column:
    """A ´Column´ should inherit from a python type (int, float, str, bytes, bool).

    Use ´name = Column(*type*) to declare a class variable for an ORM object.´
    """

    def __init__(self, column_type) -> None:
        self.type = column_type

    @property
    def sql_type(self):
        POSTGRESQL_TYPE_MAP = {
            int: "INTEGER",
            float: "REAL",
            str: "TEXT",
            bytes: "BLOB",
            bool: "BOOL",
        }
        return POSTGRESQL_TYPE_MAP[self.type]


class Database:
    """In charge of connecting to the Postgres databse.

    This class is a wrapper around ´psycopg2´.
    """

    def __init__(
        self, database: str, user: str, password: str, host: str, port: str
    ) -> None:
        self.conn = psycopg2.connect(
            database=database, user=user, password=password, host=host, port=port
        )

    def _generate_list(self, args):
        if type(args) == list:
            return args
        return [args]

    def create(self, table):
        for instance in self._generate_list(table):
            cursor = self.conn.cursor()
            cursor.execute(instance._get_create_sql())
            self.conn.commit()

    def save(self, save):
        for instance in self._generate_list(save):
            sql, values = instance._get_insert_sql()
            cursor = self.conn.cursor()
            cursor.execute(sql, values)
            self.conn.commit()
            instance._data["id"] = cursor.fetchone()[0]

    def get(self, table: Table, id: str):
        sql, fields, params = table._get_select_where_sql(id=id)
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        self.conn.commit()
        row = cursor.fetchone()

        if row is None:
            raise Exception(f"{table.__name__} instance with id {id}")

        instance = table()
        for field, value in zip(fields, row):
            # check if field is fk
            if field.endswith("_fk"):
                field = field[:-3]
                fk = getattr(table, field)
                value = self.get(fk.table, id=value)
            setattr(instance, field, value)
        return instance

    def query(self, table: Table, **kwargs):
        query_items = kwargs
        limit = query_items.pop("limit", False)
        sql, fields, query_values = table._get_query_sql(
            query_items=query_items.items()
        )
        if limit:
            sql = sql[:-1] + f" LIMIT {limit};"
        cursor = self.conn.cursor()
        result = []
        cursor.execute(sql, query_values)
        for row in cursor.fetchall():
            instance = table()
            for field, value in zip(fields, row):
                if field.endswith("_fk"):
                    field = field[:-3]
                    fk = getattr(table, field)
                    value = self.get(fk.table, id=value)
                setattr(instance, field, value)
            result.append(instance)
        if limit == 1:
            return result[0]
        return result

    def delete(self, instance):
        table = type(instance)
        sql, params = table._get_delete_sql(id=instance.id)
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
        except:
            raise Exception(f"No {table.__name__} instance with id {instance.id}")

    def all(self, table: Table):
        sql, fields = table._get_select_all_sql()
        cursor = self.conn.cursor()
        result = []
        cursor.execute(sql)
        for row in cursor.fetchall():
            instance = table()
            for field, value in zip(fields, row):
                if field.endswith("_fk"):
                    field = field[:-3]
                    fk = getattr(table, field)
                    value = self.get(fk.table, id=value)
                setattr(instance, field, value)
            result.append(instance)
        return result

    def update(self, instance: Table):
        cursor = self.conn.cursor()
        cursor.execute(*instance._get_update_sql())
        self.conn.commit()

    @property
    def tables(self) -> list:
        cursor = self.conn.cursor()
        SELECT_TABLES_SQL = "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
        cursor.execute(SELECT_TABLES_SQL)
        a = cursor.fetchall()
        return [x[0] for x in a]
