import os
import requests
import pandas as pd
from loguru import logger
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import time



class Dimensao:
    def __init__(self):
        load_dotenv()
        senha_do_banco = os.getenv("DB_PASSWORD")
        ip_do_banco = os.getenv("DB_HOST", "localhost") 
        senha_segura = quote_plus(senha_do_banco)
        self.engine = create_engine(f'postgresql+psycopg2://postgres:{senha_segura}@{ip_do_banco}:5432/sad_tabagismo')

    def extract (self):
        return None
    
    def load (self):
        return None
    
    def run (self):
        return None