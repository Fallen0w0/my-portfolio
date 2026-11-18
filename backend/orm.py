"""A small Object-Relational Mapper (ORM) built on Python's sqlite3 module.

An ORM maps a Python class to a database table, and each object of that
class to one row. You work with objects and methods instead of writing SQL
in the rest of the app:

    class Project(Model):
        __tablename__ = "projects"
        id = IntegerField(primary_key=True)
        title = TextField(nullable=False)

    project = Project.create(title="My site")   # INSERT  (Create)
    Project.get(1)                              # SELECT  (Read)
    Project.filter(title="My site")             # SELECT ... WHERE
    project.title = "New title"; project.save() # UPDATE  (Update)
    project.delete()                            # DELETE  (Delete)

Column names always come from the model's own field definitions and values
are always passed as query parameters, so user input is never pasted into
the SQL text (this prevents SQL injection).
"""

from datetime import datetime, timezone

from .database import connection


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# --------------------------------------------------------------------------
# Fields: describe the columns of a table
# --------------------------------------------------------------------------
class Field:
    sql_type = "TEXT"

    def __init__(self, primary_key=False, nullable=True, default=None,
                 auto_now=False, auto_now_add=False):
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.auto_now = auto_now              # set to "now" on every save
        self.auto_now_add = auto_now_add      # set to "now" on the first save

    def column_definition(self, name):
        parts = [name, self.sql_type]
        if self.primary_key:
            parts.append("PRIMARY KEY AUTOINCREMENT")
        elif not self.nullable:
            parts.append("NOT NULL")
        return " ".join(parts)

    def get_default(self):
        return self.default() if callable(self.default) else self.default


class IntegerField(Field):
    sql_type = "INTEGER"


class TextField(Field):
    sql_type = "TEXT"


class DateTimeField(Field):
    sql_type = "TEXT"  # stored as an ISO 8601 string, e.g. 2026-11-16T04:48:00+00:00


# --------------------------------------------------------------------------
# Model: the base class every table class inherits from
# --------------------------------------------------------------------------
class ModelMeta(type):
    """Collects the Field objects declared on a model class into `_fields`."""

    def __new__(mcls, name, bases, namespace):
        fields = {}
        for base in bases:
            fields.update(getattr(base, "_fields", {}))
        for key, value in list(namespace.items()):
            if isinstance(value, Field):
                fields[key] = value
                del namespace[key]  # each object stores its own values instead
        cls = super().__new__(mcls, name, bases, namespace)
        cls._fields = fields
        cls._pk = next((n for n, f in fields.items() if f.primary_key), None)
        return cls


class Model(metaclass=ModelMeta):
    __tablename__ = None

    def __init__(self, **values):
        unknown = set(values) - set(self._fields)
        if unknown:
            raise TypeError(
                f"{type(self).__name__} has no field(s): {', '.join(sorted(unknown))}"
            )
        for name, field in self._fields.items():
            setattr(self, name, values[name] if name in values else field.get_default())

    def __repr__(self):
        return f"<{type(self).__name__} {self._pk}={getattr(self, self._pk)!r}>"

    # ---- schema ----------------------------------------------------------
    @classmethod
    def table_exists(cls):
        with connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                (cls.__tablename__,),
            ).fetchone()
        return row is not None

    @classmethod
    def create_table(cls):
        """Create the table if needed. Returns True if it was created just now."""
        existed = cls.table_exists()
        columns = ", ".join(f.column_definition(n) for n, f in cls._fields.items())
        with connection() as conn:
            conn.execute(f"CREATE TABLE IF NOT EXISTS {cls.__tablename__} ({columns})")
        return not existed

    # ---- helpers ---------------------------------------------------------
    @classmethod
    def _check_fields(cls, names):
        unknown = [n for n in names if n not in cls._fields]
        if unknown:
            raise ValueError(f"{cls.__name__} has no field(s): {', '.join(unknown)}")

    @classmethod
    def _from_row(cls, row):
        obj = cls.__new__(cls)
        for name in cls._fields:
            setattr(obj, name, row[name])
        return obj

    def to_dict(self):
        return {name: getattr(self, name) for name in self._fields}

    # ---- Create ----------------------------------------------------------
    @classmethod
    def create(cls, **values):
        """Build a new object and INSERT it as a row."""
        return cls(**values).save()

    # ---- Read ------------------------------------------------------------
    @classmethod
    def get(cls, pk):
        """Return the object with this primary key, or None."""
        with connection() as conn:
            row = conn.execute(
                f"SELECT * FROM {cls.__tablename__} WHERE {cls._pk} = ?", (pk,)
            ).fetchone()
        return cls._from_row(row) if row else None

    @classmethod
    def filter(cls, order_by=None, **conditions):
        """Return all objects matching the conditions (field=value).

        order_by="title" sorts A-Z; order_by="-id" sorts newest id first.
        """
        cls._check_fields(conditions)
        sql = f"SELECT * FROM {cls.__tablename__}"
        params = list(conditions.values())
        if conditions:
            sql += " WHERE " + " AND ".join(f"{n} = ?" for n in conditions)
        if order_by:
            column = order_by.lstrip("-")
            cls._check_fields([column])
            sql += f" ORDER BY {column} {'DESC' if order_by.startswith('-') else 'ASC'}"
        with connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [cls._from_row(row) for row in rows]

    @classmethod
    def all(cls, order_by=None):
        return cls.filter(order_by=order_by)

    # ---- Update (and Create, for objects that have no id yet) --------------
    def save(self):
        """INSERT the object if it has no id yet, otherwise UPDATE its row."""
        now = _utc_now()
        for name, field in self._fields.items():
            if field.auto_now or (field.auto_now_add and getattr(self, name) is None):
                setattr(self, name, now)

        data = {n: getattr(self, n) for n in self._fields if n != self._pk}
        pk_value = getattr(self, self._pk)
        table = self.__tablename__

        with connection() as conn:
            if pk_value is None:
                columns = ", ".join(data)
                marks = ", ".join("?" for _ in data)
                cursor = conn.execute(
                    f"INSERT INTO {table} ({columns}) VALUES ({marks})", list(data.values())
                )
                setattr(self, self._pk, cursor.lastrowid)
            else:
                assignments = ", ".join(f"{n} = ?" for n in data)
                cursor = conn.execute(
                    f"UPDATE {table} SET {assignments} WHERE {self._pk} = ?",
                    [*data.values(), pk_value],
                )
                if cursor.rowcount == 0:
                    raise LookupError(f"{type(self).__name__} {pk_value} no longer exists")
        return self

    def update(self, **values):
        """Change several fields at once and save."""
        self._check_fields(values)
        if self._pk in values:
            raise ValueError("The primary key cannot be changed.")
        for name, value in values.items():
            setattr(self, name, value)
        return self.save()

    # ---- Delete ----------------------------------------------------------
    def delete(self):
        """DELETE this object's row."""
        with connection() as conn:
            conn.execute(
                f"DELETE FROM {self.__tablename__} WHERE {self._pk} = ?",
                (getattr(self, self._pk),),
            )
