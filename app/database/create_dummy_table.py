import psycopg2
import pandas as pd
import pandas.io.sql as psql
import os
from dotenv import load_dotenv


env_path=os.path.join('/workspace', '.env')
load_dotenv(env_path)

# print(env_path)


POSTGRES_IP_ADDR = os.getenv('POSTGRES_IP_ADDR')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

#Establishing the connection
# host = host = os.popen("docker inspect -f '{{ .NetworkSettings.Networks.python_web_postgres.IPAddress }}' postgres").read()
# print(host)
postgresConnection = psycopg2.connect(
    host=POSTGRES_IP_ADDR,
    database=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD
)

# Get cursor object from the database connection

cursor = postgresConnection.cursor()

 

name_Table = "user_information"

 
# Create table statement
# Create a table in PostgreSQL database
cursor.execute(f"DROP TABLE IF EXISTS {name_Table}")
sqlCreateTable = f"create table {name_Table} ( \
    id SERIAL PRIMARY KEY, \
    username VARCHAR(128), \
    full_name VARCHAR(128), \
    email VARCHAR(256), \
    disabled BOOLEAN, \
    hashed_password VARCHAR(256), \
    date DATE NOT NULL DEFAULT CURRENT_DATE);"
cursor.execute(sqlCreateTable)


schema = "public"
username = "shinuk"
record_to_insert1 = (
    "shinuk",
    "Shinuk Yi",
    "shinuk@example.com",
    False,
    "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
)
record_to_insert2 = (
    "micky",
    "micky Yi",
    "micky@example.com",
    False,
    "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
)
record_to_insert3 = (
    "johndoe",
    "john Doe",
    "shuwhan@example.com",
    False,
    "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
)
sqlInsertContents = f"INSERT INTO {schema}.{name_Table}(username, full_name, email, disabled, hashed_password) \
    VALUES (%s, %s, %s, %s, %s);"

cursor.execute(sqlInsertContents, record_to_insert1)
cursor.execute(sqlInsertContents, record_to_insert2)
cursor.execute(sqlInsertContents, record_to_insert3)
postgresConnection.commit()

# Get the updated list of tables
#sqlGetTableList = "\dt"
# Retrieve all the rows from the cursor
sqlGetTableList = "SELECT table_schema, table_name \
    FROM information_schema.tables \
    where table_schema='public' \
    ORDER BY table_schema,table_name ;"
cursor.execute(sqlGetTableList)
tables = cursor.fetchall()

# Print the names of the tables
# mobile_records = cursor.fetchall()
# for row in tables:
for table in tables:
    print(table)


my_table = pd.read_sql(f"select * from {name_Table} WHERE username = '{username}'", postgresConnection)
another_attempt= psql.read_sql(f"SELECT * FROM {name_Table} WHERE username = '{username}'", postgresConnection)
print(my_table)

# cursor.execute(f"SELECT * FROM {name_Table} WHERE username = '{username}'")
cursor.execute(f"SELECT * FROM {name_Table}")
# for desc in cursor.description:
#     print(desc[0], desc[1])
row = cursor.fetchone()
# print(row[0], row[1])
while row is not None:
    print(row)
    row = cursor.fetchone()

# #Creating a cursor object using the cursor() method
# cursor = conn.cursor()

# #Doping EMPLOYEE table if already exists.
# cursor.execute("DROP TABLE IF EXISTS EMPLOYEE")

# #Creating table as per requirement
# sql ='''CREATE TABLE EMPLOYEE(
#    FIRST_NAME CHAR(20) NOT NULL,
#    LAST_NAME CHAR(20),
#    AGE INT,
#    SEX CHAR(1),
#    INCOME FLOAT
# )'''
# cursor.execute(sql)

# print("Table created successfully........")

# #Closing the connection
# conn.close()