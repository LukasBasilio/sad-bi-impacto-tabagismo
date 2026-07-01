import os
import pandas as pd
from dimensao import Dimensao
from loguru import logger
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import time


class DimensaoPaciente(Dimensao):

    def __init__(self):
        super().__init__()
        self.df = None

    def extract(self):
        logger.info("Iniciando a extração dos pacientes na Staging (SIH)...")
        
        query = text("""
            SELECT DISTINCT
                CAST("IDADE" AS INTEGER) AS nu_idade,
                
                CASE 
                    WHEN "SEXO" = '1' THEN 'Masculino' 
                    WHEN "SEXO" = '3' THEN 'Feminino' 
                    ELSE 'Desconhecido'
                END AS desc_sexo,
                
                CASE 
                    WHEN "RACA_COR" = '01' THEN 'Branca' 
                    WHEN "RACA_COR" = '02' THEN 'Preta' 
                    WHEN "RACA_COR" = '03' THEN 'Parda' 
                    WHEN "RACA_COR" = '04' THEN 'Amarela' 
                    WHEN "RACA_COR" = '05' THEN 'Indígena' 
                    ELSE 'Sem Informação' 
                END AS desc_raca,
                
                CASE 
                    WHEN CAST("IDADE" AS INTEGER) BETWEEN 35 AND 39 THEN '35 a 39 anos'
                    WHEN CAST("IDADE" AS INTEGER) BETWEEN 40 AND 49 THEN '40 a 49 anos'
                    WHEN CAST("IDADE" AS INTEGER) BETWEEN 50 AND 59 THEN '50 a 59 anos'
                    WHEN CAST("IDADE" AS INTEGER) BETWEEN 60 AND 69 THEN '60 a 69 anos'
                    WHEN CAST("IDADE" AS INTEGER) BETWEEN 70 AND 79 THEN '70 a 79 anos'
                    ELSE '80 anos ou mais'
                END AS desc_faixa_etaria
            FROM staging.raw_sih
            WHERE "IDADE" IS NOT NULL AND CAST("IDADE" AS INTEGER) >= 35;
        """)

        self.df = pd.read_sql_query(sql=query, con=self.engine)
        logger.info(f"Extração concluída! Encontrados {len(self.df)} perfis únicos de pacientes.")

    def transform(self):
        logger.info("Gerando a Chave Primária (sk_paciente)...")
        
        self.df.insert(0, 'sk_paciente', range(1, len(self.df) + 1))
        logger.info("Transformação concluída e pronta para o DW.")
        
    def load(self):
        logger.info("Injetando os dados no Data Warehouse (dw.d_paciente)...")
        
        self.df.to_sql(name='d_paciente', schema='dw', con=self.engine, if_exists='replace', index=False)
        logger.success("Tabela d_paciente carregada com sucesso!")

    def run(self):
        logger.info("--- INICIANDO PIPELINE: DIMENSÃO PACIENTE ---")
        start_time = time.time()
        
        self.extract()
        self.transform()
        self.load()
        
        end_time = time.time()
        logger.success(f"--- PIPELINE FINALIZADO EM {round(end_time - start_time, 2)} SEGUNDOS ---")


# Teste para rodar apenas esse arquivo
if __name__ == "__main__":
    robo = DimensaoPaciente()
    robo.run()