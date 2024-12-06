from os import path

import toml

secrets = toml.load(path.join(path.dirname(path.realpath(__file__)), '..', '.streamlit', 'secrets.toml'))


def get_api_key():
    return secrets['binance']['api_key']


def get_secret_key():
    return secrets['binance']['secret_key']
