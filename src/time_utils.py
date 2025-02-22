import datetime

def convert_to_epoch(date_string:str):
    return int(datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S").timestamp())

def convert_from_epoch(epoch_time:int):
    return datetime.datetime.utcfromtimestamp(int(epoch_time))
