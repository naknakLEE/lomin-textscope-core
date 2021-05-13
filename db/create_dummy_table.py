import psycopg2
import pandas as pd
import pandas.io.sql as psql
import os

#Establishing the connection
# host = host = os.popen("docker inspect -f '{{ .NetworkSettings.Networks.python_web_postgres.IPAddress }}' postgres").read()
# print(host)
postgresConnection = psycopg2.connect(
    host="172.20.0.6",
    database="shinuk",
    user="shinuk",
    password="1q2w3e4r"
)

# Get cursor object from the database connection

cursor = postgresConnection.cursor()

 

name_Table = "user_information"

 
# Create table statement
# Create a table in PostgreSQL database
cursor.execute(f"DROP TABLE IF EXISTS {name_Table}")
sqlCreateTable = f"create table {name_Table} ( \
    id bigint, \
    username varchar(128), \
    full_name varchar(128), \
    email varchar(256), \
    hashed_password varchar(256), \
    disabled boolean, \
    story text);"
cursor.execute(sqlCreateTable)


schema = "public"
username = "shinuk"
record_to_insert1 = (
    111,
    "shinuk",
    "Shinuk Yi",
    "shinuk@example.com",
    "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
    False
)
record_to_insert2 = (
    121,
    "micky",
    "micky Yi",
    "micky@example.com",
    "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
    False
)
record_to_insert3 = (
    123,
    "johndoe",
    "john Doe",
    "shuwhan@example.com",
    "$2b$12$3kvrUJTX6KWAvL0bv7lc7u4ht2Ri3fdjqVTclSQ8fkDpy6lqVn42e",
    False
)
sqlInsertContents = f"INSERT INTO {schema}.{name_Table}(id, username, full_name, email, hashed_password, disabled) \
    VALUES (%s, %s, %s, %s, %s, %s);"

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

cursor.execute(f"SELECT * FROM {name_Table} WHERE username = '{username}'")
# for desc in cursor.description:
#     print(desc[0], desc[1])
row = cursor.fetchone()
print(row[0], row[1])
# while row is not None:
#     print(row)
#     row = cursor.fetchone()

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