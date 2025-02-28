import datetime

def convert_to_epoch(date_string: str) -> int:
    """Converts a datetime string (YYYY-MM-DD HH:MM:SS) to a UTC epoch timestamp."""
    dt = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.UTC)
    return int(dt.timestamp())


def convert_from_epoch(epoch_time: int) -> datetime.datetime:
    """Converts a UTC epoch timestamp into a timezone-aware datetime object in UTC."""
    if not isinstance(epoch_time, (int, float)):
        raise TypeError("Epoch time must be an integer or float.")

    return datetime.datetime.fromtimestamp(int(epoch_time), datetime.UTC)