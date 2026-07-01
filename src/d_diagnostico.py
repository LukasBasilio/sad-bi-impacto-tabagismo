import os
import pandas as pd
from dimensao import Dimensao
from loguru import logger
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import time

class DimensaoDiagnostico(Dimensao):

    def __init__(self):
        super().__init__()
        self.df = None
        
    def extract(self):
        logger.info("Iniciando a extração dos diagnosticos na Staging (SIH)")
        
        query = text("""
            SELECT DISTINCT
                "DIAG_PRINC" AS cd_cid,
                
                -- GRUPO DA DOENÇA (desc_doenca)
                CASE 
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) IN ('C33', 'C34') THEN 'Câncer de Pulmão'
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) = 'C32' THEN 'Câncer de Laringe'
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) = 'C15' THEN 'Câncer de Esôfago'
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) BETWEEN 'C00' AND 'C14' THEN 'Câncer de Boca e Faringe'
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) = 'C67' THEN 'Câncer de Bexiga'
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) = 'C25' THEN 'Câncer de Pâncreas'
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) = 'C53' THEN 'Câncer do Colo do Útero'
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) BETWEEN 'J40' AND 'J44' THEN 'DPOC'
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) BETWEEN 'I20' AND 'I25' THEN 'Doença Isquêmica do Coração (IAM)'
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) BETWEEN 'I60' AND 'I69' THEN 'Doença Cerebrovascular (AVC)'
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) = 'I70' THEN 'Aterosclerose'
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) IN ('F17', 'T65', 'Z72') THEN 'Doenças ligadas diretamente ao Tabaco'
                    ELSE 'Outros'
                END AS desc_doenca,
                
                -- FRAÇÃO ATRIBUÍVEL (nu_fap)
                CASE 
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) = 'C32' THEN 0.80
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) IN ('C33', 'C34') THEN 0.78
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) BETWEEN 'J40' AND 'J44' THEN 0.68
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) = 'C15' THEN 0.65
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) BETWEEN 'C00' AND 'C14' THEN 0.59
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) = 'C67' THEN 0.38
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) BETWEEN 'I20' AND 'I25' THEN 0.25
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) = 'C25' THEN 0.20
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) BETWEEN 'I60' AND 'I69' THEN 0.15
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) = 'I70' THEN 0.11
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) = 'C53' THEN 0.09
                    WHEN SUBSTRING("DIAG_PRINC", 1, 3) IN ('F17', 'T65', 'Z72') THEN 1.00
                    ELSE 0.00
                END AS nu_fap
            
            FROM staging.raw_sih
            WHERE "DIAG_PRINC" IS NOT NULL;
        """)
        
        
        self.df = pd.read_sql_query(sql=query, con=self.engine)
        logger.info(f"Extração concluída! Encontrados {len(self.df)} diagnósticos únicos.")
        
    def transform(self):
        logger.info("Gerando a Chave Primária (sk_diagnostico)...")
        
        self.df.insert(0, 'sk_diagnostico', range(1, len(self.df) + 1))
        logger.info("Transformação concluída e pronta para o DW.")
        
    def load(self):
        logger.info("Injetando os dados no Data Warehouse (dw.d_diagnostico)...")
        
        self.df.to_sql(name='d_diagnostico', schema='dw', con=self.engine, if_exists='replace', index=False)
        logger.success("Tabela d_diagnostico carregada com sucesso!")
        
        
    def run(self):
        logger.info("--- INICIANDO PIPELINE: DIMENSÃO DIAGNOSTICO ---")
        start_time = time.time()
        
        self.extract()
        self.transform()
        self.load()
        
        end_time = time.time()
        logger.success(f"--- PIPELINE FINALIZADO EM {round(end_time - start_time, 2)} SEGUNDOS ---")


# Teste para rodar apenas esse arquivo
if __name__ == "__main__":
    robo = DimensaoDiagnostico()
    robo.run()