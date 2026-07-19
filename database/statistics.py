import sqlite3

connection = sqlite3.connect("data/hospital.db")

cursor = connection.cursor()


def total_patients():

    cursor.execute(
        "SELECT COUNT(*) FROM patients"
    )

    return cursor.fetchone()[0]


print(total_patients())