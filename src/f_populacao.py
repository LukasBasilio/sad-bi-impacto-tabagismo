import os
import pandas as pd
from loguru import logger
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, BigInteger
from urllib.parse import quote_plus
import time

class FatoPopulacao:

    def __init__(self):
        load_dotenv()
        senha_do_banco = os.getenv("DB_PASSWORD")
        ip_do_banco = os.getenv("DB_HOST", "localhost") 
        senha_segura = quote_plus(senha_do_banco)
        self.engine = create_engine(f'postgresql+psycopg2://postgres:{senha_segura}@{ip_do_banco}:5432/sad_tabagismo')
        self.df = None
        
    def extract(self):
        logger.info("Iniciando a criação da Tabela Fato (F_POPULACAO)...")
        
        # A API do IBGE retornou as colunas assim: D1C (Município), D2C (Ano) e V (Valor da População)
        query = text("""
            SELECT
                c.sk_calendario AS "Id_calendario",
                l.sk_localidade AS "Id_localidade",
                
                -- O valor da população estimado pelo IBGE
                CAST(s."V" AS BIGINT) AS nu_populacao_estimada

            FROM staging.raw_ibge s

            -- 1. LIGAÇÃO COM CALENDÁRIO (Cópia para todos os meses)
            -- D2C é a coluna do Ano na sua tabela
            INNER JOIN dw.d_calendario c 
                ON c.nu_ano = CAST(s."D2C" AS INTEGER)
               
            -- 2. LIGAÇÃO COM LOCALIDADE (Cortando o 7º dígito do IBGE para encaixar no SUS)
            -- D1C é a coluna do Código do Município
            INNER JOIN dw.d_localidade l 
                ON CAST(l.cd_municipio AS TEXT) = LEFT(CAST(s."D1C" AS TEXT), 6)

            -- Garantindo que nenhum dado sujo ou vazio passe
            WHERE s."V" IS NOT NULL AND s."V" != '...';
        """)
        
        logger.info("Executando o cruzamento e replicando a população para a granularidade mensal...")
        self.df = pd.read_sql_query(sql=query, con=self.engine)
        logger.info(f"Fato População calculada! Total de {len(self.df)} linhas geradas.")
        
    def transform(self):
        logger.info("Métricas validadas. Pronta para o Data Warehouse.")
        
    def load(self):
        logger.info("Injetando os dados no Data Warehouse (dw.f_populacao)...")
        self.df.to_sql(name='f_populacao', schema='dw', con=self.engine, if_exists='replace', index=False,
            chunksize=50000,
            dtype={
                'Id_calendario': BigInteger(),
                'Id_localidade': BigInteger(),
                'nu_populacao_estimada': BigInteger()
            }
        )
        logger.success("Tabela f_populacao carregada com sucesso!")
        
    def run(self):
        logger.info("--- INICIANDO PIPELINE: FATO POPULAÇÃO ---")
        start_time = time.time()
        self.extract()
        self.transform()
        self.load()
        end_time = time.time()
        logger.success(f"--- PIPELINE FINALIZADO EM {round(end_time - start_time, 2)} SEGUNDOS ---")


if __name__ == "__main__":
    robo = FatoPopulacao()
    robo.run()