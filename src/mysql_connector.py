import os
import mysql.connector


class MySQLConnector:
    def __init__(self):
        # Create a persistent connection using environment variables.
        self.cnx = mysql.connector.connect(
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            host=os.getenv("MYSQL_HOST", "localhost"),
            database=os.getenv("MYSQL_DATABASE")
        )
        # Create a cursor once.
        self.cursor = self.cnx.cursor()

    def insert_data(self, history):
        insert_sql = (
            "INSERT INTO clicksend_messages "
            "(message_id, `date`, `to`, status, schedule, status_code, status_text, error_code, error_text, message_parts, message_price, from_email, list_id, carrier, body) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )

        for item in history:
            data_tuple = (
                item.get('message_id'),
                int(item.get('date')),
                item.get('to'),
                item.get('status'),
                int(item.get('schedule')),
                item.get('status_code'),
                item.get('status_text'),
                item.get('error_code'),
                item.get('error_text'),
                int(item.get('message_parts')),
                float(item.get('message_price')),
                item.get('from_email'),
                item.get('list_id'),
                item.get('carrier'),
                item.get('body')
            )
            self.cursor.execute(insert_sql, data_tuple)

        self.cnx.commit()

    def close(self):
        # Make sure to close the cursor and connection when finished.
        self.cursor.close()
        self.cnx.close()