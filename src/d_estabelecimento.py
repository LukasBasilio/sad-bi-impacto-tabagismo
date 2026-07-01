import os
import pandas as pd
from dimensao import Dimensao
from loguru import logger
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import time

class DimensaoEstabelecimento(Dimensao):

    def __init__(self):
        super().__init__()
        self.df = None
        
    def extract(self):
        logger.info("Iniciando a extração dos Estabelecimentos de Saúde (CNES)...")
        
        query = text("""
            SELECT DISTINCT
                s."CNES" AS cd_cnes,
                
                -- Cruza o município do hospital (MUNIC_MOV) com o IBGE para pegar a sigla do Estado
                CASE 
                    WHEN s."MUNIC_MOV" LIKE '530%' THEN 'DF'
                    ELSE TRIM(SPLIT_PART(i."D1N", ' - ', 2))
                END AS no_uf

            FROM staging.raw_sih s
            
            LEFT JOIN staging.raw_ibge i 
                ON SUBSTRING(i."D1C", 1, 6) = s."MUNIC_MOV"
                
            WHERE s."CNES" IS NOT NULL;
        """)
        
        self.df = pd.read_sql_query(sql=query, con=self.engine)
        logger.info(f"Extração concluída! Encontrados {len(self.df)} hospitais únicos.")
        
    def transform(self):
        logger.info("Gerando a Chave Primária (sk_estabelecimento)...")
        self.df.insert(0, 'sk_estabelecimento', range(1, len(self.df) + 1))
        logger.info("Transformação concluída e pronta para o DW.")
        
    def load(self):
        logger.info("Injetando os dados no Data Warehouse (dw.d_estabelecimento)...")
        self.df.to_sql(name='d_estabelecimento', schema='dw', con=self.engine, if_exists='replace', index=False)
        logger.success("Tabela d_estabelecimento carregada com sucesso!")
        
    def run(self):
        logger.info("--- INICIANDO PIPELINE: DIMENSÃO ESTABELECIMENTO ---")
        start_time = time.time()
        
        self.extract()
        self.transform()
        self.load()
        
        end_time = time.time()
        logger.success(f"--- PIPELINE FINALIZADO EM {round(end_time - start_time, 2)} SEGUNDOS ---")


# Teste para rodar apenas esse arquivo
if __name__ == "__main__":
    robo = DimensaoEstabelecimento()
    robo.run()