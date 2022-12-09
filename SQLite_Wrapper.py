"""
Main Tutorial
https://docs.python.org/3/library/sqlite3.html

Schema Table
https://www.sqlite.org/schematab.html

Placeholders to bind values
https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders


"""

import sqlite3
import os
import numpy as np

class SQLiteWrapper():
    """
    A wrapper class for SQLite
    
    The SQL Schema will be a table containing:
    timestamps
    labels
    values
    """
    def __init__(self):
        self.db_name = 'metrics.db'
        self.first_run = False

        if not os.path.exists(self.db_name):
            print(f"Warning! SQLite DB '{self.db_name}' not found!")
            print("Default action is to create it now.")
            self.first_run = True
            #os.remove(self.db_name)

        self.conn = sqlite3.connect(self.db_name)
        print("Opened database successfully")

        # In order to execute SQL statements and fetch results from
        # SQL queries, we will need to use a database cursor.
        self.cur = self.conn.cursor()

        if self.first_run:
            self.create_table()

        # Close the Connection
        #self.conn.close()

    def create_table(self):
        """
        Creates a table in the DB. WARNING! cannot create a table if name
        already exists as a table!
        """
        query = "CREATE TABLE metrics(timestamp, label, value)"
        self.cur.execute(query)

    def add_values(self, t_stamp, val_dict):
        """
        val_dict should contain {label1: value1,....}
        """
        data = []
        for label, value in val_dict.items():
            entry = (t_stamp, label, value)
            data.append(entry)

        self.cur.executemany("INSERT INTO metrics VALUES(?, ?, ?)", data)
        self.conn.commit()  # Remember to commit the transaction after executing INSERT.


    def load_values(self):
        """
        Dict Structure is:

        {label: { timestamp: value},...},....}
        """

        out_dict = {}
        # First find the labels and add them to the dict top level.
        d_query = "SELECT DISTINCT label FROM metrics"
        db_load = self.cur.execute(d_query)
        for row in db_load:
            label = row[0]
            out_dict[label] = {}

        # Now load in the values.
        query = "SELECT timestamp, label, value FROM metrics ORDER BY timestamp"
        db_load = self.cur.execute(query)

        for row in db_load:
            timestamp = row[0]
            label = row[1]
            val = row[2]

            #print(row)
            out_dict[label][timestamp] = val

        return out_dict

def main():
    """
    a lil test function
    """

    # If the DB exists, delete it.
    db_name = 'metrics.db'
    if os.path.exists(db_name):
        os.remove(db_name)

    sql = SQLiteWrapper()
    for i in range(15):
        vals = [np.random.randint(10) for _ in range(3)]
        entry = {"kills": vals[0],
                 "deaths": vals[1],
                 "lives": vals[2]}
        sql.add_values(i, entry)

    out_dict = sql.load_values()
    import json
    print(json.dumps(out_dict, indent=2, default=str))

if __name__ == "__main__":
    main()
