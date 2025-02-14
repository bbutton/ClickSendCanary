import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Insert the repository root into sys.path.
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Import MySQLConnector from the src folder.
try:
    from src.mysql_connector import MySQLConnector
except ModuleNotFoundError as e:
    print("Error importing MySQLConnector:", e)
    raise

class TestMySQLConnectorInitialization(unittest.TestCase):
    @patch('src.mysql_connector.mysql.connector.connect')
    def test_initialization(self, mock_connect):
        # Set up dummy environment variables.
        os.environ["MYSQL_USER"] = "dummy_user"
        os.environ["MYSQL_PASSWORD"] = "dummy_password"
        os.environ["MYSQL_HOST"] = "dummy_host"
        os.environ["MYSQL_DATABASE"] = "dummy_database"

        # Create a mock connection and cursor.
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        # Instantiate the connector.
        connector = MySQLConnector()

        # Verify that mysql.connector.connect was called with the expected arguments.
        mock_connect.assert_called_once_with(
            user="dummy_user",
            password="dummy_password",
            host="dummy_host",
            database="dummy_database"
        )

        # Verify that the connector has set its attributes correctly.
        self.assertEqual(connector.cnx, mock_connection)
        self.assertEqual(connector.cursor, mock_cursor)

if __name__ == '__main__':
    unittest.main()