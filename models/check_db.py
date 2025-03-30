from sqlalchemy import inspect
from db_setup import engine

inspector = inspect(engine)
columns = inspector.get_columns("subjects")

for column in columns:
    print(column["name"], column["type"])
