import unittest
import datetime
from src.time_utils import convert_to_epoch, convert_from_epoch

class TestTimeUtils(unittest.TestCase):

    def test_convert_to_epoch_valid_datetime_string(self):
        """Ensure a properly formatted datetime string in UTC converts to epoch correctly."""
        expected_epoch = 1740592800  # Corrected UTC epoch
        self.assertEqual(convert_to_epoch("2025-02-26 18:00:00"), expected_epoch)

    def test_convert_to_epoch_invalid_format(self):
        """Ensure an incorrectly formatted datetime string raises ValueError."""
        with self.assertRaises(ValueError):
            convert_to_epoch("26-02-2025 12:00:00")  # Wrong format

    def test_convert_from_epoch_valid_input(self):
        """Ensure a valid epoch time converts to a correct UTC datetime object."""
        dt = convert_from_epoch(1740592800)  # UTC timestamp
        expected_dt = datetime.datetime(2025, 2, 26, 18, 0, 0, tzinfo=datetime.UTC)
        self.assertEqual(dt, expected_dt)

    def test_convert_from_epoch_invalid_input(self):
        """Ensure passing a non-numeric value raises a TypeError."""
        with self.assertRaises(TypeError):
            convert_from_epoch("1740592800")  # String should fail

        with self.assertRaises(TypeError):
            convert_from_epoch(None)  # None should fail

        with self.assertRaises(TypeError):
            convert_from_epoch([])  # List should fail


if __name__ == "__main__":
    unittest.main()