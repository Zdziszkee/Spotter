import sqlite3
from contextlib import closing

from pypika.queries import Query, Table
from pypika.terms import Field

offers_table = Table("offers")

db_path = "database.db"
connection = sqlite3.connect(db_path)

create_table_query = (
    Query.create_table(offers_table)
    .if_not_exists()
    .columns(
        Field("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        Field("title", "VARCHAR(255)"),
        Field("price", "FLOAT"),
        Field("size", "FLOAT"),
        Field("location", "VARCHAR(255)"),
        Field("listed_date", "TIMESTAMP"),
        Field("description", "TEXT"),
        Field("url", "VARCHAR(255)"),
        Field("website", "VARCHAR(255)"),
        Field("images", "TEXT"),
    )
)

with closing(connection.cursor()) as cursor:
    cursor.execute(str(create_table_query))

connection.commit()
