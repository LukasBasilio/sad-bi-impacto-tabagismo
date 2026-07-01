import os
import pandas as pd
from dimensao import Dimensao
from loguru import logger
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import time

class DimensaoCalendario(Dimensao):

    def __init__(self):
        super().__init__()
        self.df = None
        
    def extract(self):
        logger.info("Iniciando a extração do Calendário na Staging (SIH)...")
        
        query = text("""
            SELECT DISTINCT
                CAST("ANO_CMPT" AS INTEGER) AS nu_ano,
                CAST("MES_CMPT" AS INTEGER) AS nu_mes,
                
                -- Nome do Mês
                CASE CAST("MES_CMPT" AS INTEGER)
                    WHEN 1 THEN 'Janeiro'
                    WHEN 2 THEN 'Fevereiro'
                    WHEN 3 THEN 'Março'
                    WHEN 4 THEN 'Abril'
                    WHEN 5 THEN 'Maio'
                    WHEN 6 THEN 'Junho'
                    WHEN 7 THEN 'Julho'
                    WHEN 8 THEN 'Agosto'
                    WHEN 9 THEN 'Setembro'
                    WHEN 10 THEN 'Outubro'
                    WHEN 11 THEN 'Novembro'
                    WHEN 12 THEN 'Dezembro'
                    ELSE 'Desconhecido'
                END AS no_mes,
                
                -- Trimestre
                CASE 
                    WHEN CAST("MES_CMPT" AS INTEGER) IN (1, 2, 3) THEN 1
                    WHEN CAST("MES_CMPT" AS INTEGER) IN (4, 5, 6) THEN 2
                    WHEN CAST("MES_CMPT" AS INTEGER) IN (7, 8, 9) THEN 3
                    WHEN CAST("MES_CMPT" AS INTEGER) IN (10, 11, 12) THEN 4
                    ELSE 0
                END AS nu_trimestre

            FROM staging.raw_sih
            WHERE "ANO_CMPT" IS NOT NULL AND "MES_CMPT" IS NOT NULL;
        """)
        
        self.df = pd.read_sql_query(sql=query, con=self.engine)
        
        
        self.df = self.df.sort_values(by=['nu_ano', 'nu_mes']).reset_index(drop=True)
        logger.info(f"Extração concluída! Encontrados {len(self.df)} meses únicos no histórico.")
        
    def transform(self):
        logger.info("Gerando a Chave Primária (sk_calendario)...")
        self.df.insert(0, 'sk_calendario', range(1, len(self.df) + 1))
        logger.info("Transformação concluída e pronta para o DW.")
        
    def load(self):
        logger.info("Injetando os dados no Data Warehouse (dw.d_calendario)...")
        self.df.to_sql(name='d_calendario', schema='dw', con=self.engine, if_exists='replace', index=False)
        logger.success("Tabela d_calendario carregada com sucesso!")
        
    def run(self):
        logger.info("--- INICIANDO PIPELINE: DIMENSÃO CALENDÁRIO ---")
        start_time = time.time()
        
        self.extract()
        self.transform()
        self.load()
        
        end_time = time.time()
        logger.success(f"--- PIPELINE FINALIZADO EM {round(end_time - start_time, 2)} SEGUNDOS ---")


# Teste para rodar apenas esse arquivo
if __name__ == "__main__":
    robo = DimensaoCalendario()
    robo.run()