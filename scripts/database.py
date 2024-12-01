import csv
import os
from os import path

db_root = path.join(path.dirname(path.realpath(__file__)), '..', 'data')

if not path.exists(db_root):
    os.mkdir(db_root)


def to_db_path(file_name):
    return path.join(db_root, file_name)


def write(file_name, data, replace=False):
    file_path = to_db_path(file_name)
    exists = path.exists(file_path)

    mode = 'a' if exists and not replace else 'w'

    with open(file_path, mode, newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)


def read(file_name):
    file_path = to_db_path(file_name)

    if not path.exists(file_path):
        raise FileNotFoundError()

    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        return list(reader)[0]
