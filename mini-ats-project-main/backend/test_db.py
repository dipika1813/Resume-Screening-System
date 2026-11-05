from db import get_db_connection

try:
    connection = get_db_connection()

    print("MySQL Connected Successfully!")

    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")

    print("Tables in database:")

    for table in cursor.fetchall():
        print(table[0])

    cursor.close()
    connection.close()

except Exception as e:
    print("Connection Failed:", e)