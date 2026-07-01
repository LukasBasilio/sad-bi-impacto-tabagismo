import os
import pandas as pd
from dimensao import Dimensao
from loguru import logger
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import time

class DimensaoLocalidade(Dimensao):

    def __init__(self):
        super().__init__()
        self.df = None
        
    def extract(self):
        logger.info("Iniciando a extração das localidades na Staging (SIH)")
        
        query = text("""
            SELECT DISTINCT
                s."MUNIC_RES" AS cd_municipio,
                
                -- Se for código inventado do DF (530...), chama de Brasília. 
                -- Senão, corta a string no hífen (' - ') e pega o lado esquerdo (1)
                CASE 
                    WHEN s."MUNIC_RES" LIKE '530%' THEN 'Brasília'
                    ELSE TRIM(SPLIT_PART(i."D1N", ' - ', 1))
                END AS no_municipio,
                
                -- Se for DF, chama de DF. 
                -- Senão, corta a string no hífen (' - ') e pega o lado direito (2)
                CASE 
                    WHEN s."MUNIC_RES" LIKE '530%' THEN 'DF'
                    ELSE TRIM(SPLIT_PART(i."D1N", ' - ', 2))
                END AS no_uf
            FROM staging.raw_sih s
            
            LEFT JOIN staging.raw_ibge i 
                ON SUBSTRING(i."D1C", 1, 6) = s."MUNIC_RES"
                
            WHERE s."MUNIC_RES" IS NOT NULL;
        """)
        self.df = pd.read_sql_query(sql=query, con=self.engine)
        logger.info(f"Extração concluída! Encontrados {len(self.df)} municípios únicos.")
        
    def transform(self):
        logger.info("Gerando a Chave Primária (sk_localidade)...")
        
        self.df.insert(0, 'sk_localidade', range(1, len(self.df) + 1))
        logger.info("Transformação concluída e pronta para o DW.")
        
    def load(self):
        logger.info("Injetando os dados no Data Warehouse (dw.d_localidade)...")
        
        self.df.to_sql(name='d_localidade', schema='dw', con=self.engine, if_exists='replace', index=False)
        logger.success("Tabela d_localidade carregada com sucesso!")
        
        
    def run(self):
        logger.info("--- INICIANDO PIPELINE: DIMENSÃO LOCALIDADE ---")
        start_time = time.time()
        
        self.extract()
        self.transform()
        self.load()
        
        end_time = time.time()
        logger.success(f"--- PIPELINE FINALIZADO EM {round(end_time - start_time, 2)} SEGUNDOS ---")


# Teste para rodar apenas esse arquivo
if __name__ == "__main__":
    robo = DimensaoLocalidade()
    robo.run()