import os
import pandas as pd
from dimensao import Dimensao
from loguru import logger
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, BigInteger, Numeric
import time

class FatoInternacao(Dimensao):

    def __init__(self):
        super().__init__()
        self.df = None
        
    def extract(self):
        logger.info("Iniciando a criação da Tabela Fato (F_INTERNACAO)...")
        
        query = text("""
            SELECT
                c.sk_calendario AS "Id_calendario",
                p.sk_paciente AS "Id_paciente",
                l.sk_localidade AS "Id_localidade",
                d.sk_diagnostico AS "Id_diagnostico",
                e.sk_estabelecimento AS "Id_estabelecimento",
                
                -- MÉTRICAS (Contagem e Somas blindadas contra vazios)
                COUNT(s."N_AIH") AS qt_internacoes,
                SUM(CAST(NULLIF(TRIM(s."MORTE"), '') AS INTEGER)) AS qt_mortes,
                SUM(CAST(NULLIF(TRIM(s."DIAS_PERM"), '') AS INTEGER)) AS qt_dias_permanencia,
                
                -- CÁLCULO CIENTÍFICO (FAP): Multiplica o valor gasto pelo percentual de culpa do Tabaco
                SUM(CAST(NULLIF(TRIM(s."VAL_TOT"), '') AS NUMERIC) * CAST(d.nu_fap AS NUMERIC)) AS vl_total

            FROM staging.raw_sih s

            -- LIGAÇÕES (Convertendo todos os cruzamentos para Texto puro)
            INNER JOIN dw.d_calendario c 
                ON c.nu_ano = CAST(NULLIF(TRIM(s."ANO_CMPT"), '') AS INTEGER) 
               AND c.nu_mes = CAST(NULLIF(TRIM(s."MES_CMPT"), '') AS INTEGER)
               
            INNER JOIN dw.d_paciente p 
                ON CAST(p.desc_sexo AS TEXT) = CASE WHEN s."SEXO" = '1' THEN 'Masculino' WHEN s."SEXO" = '3' THEN 'Feminino' ELSE 'Desconhecido' END
               AND CAST(p.desc_raca AS TEXT) = CASE WHEN s."RACA_COR" = '01' THEN 'Branca' WHEN s."RACA_COR" = '02' THEN 'Preta' WHEN s."RACA_COR" = '03' THEN 'Parda' WHEN s."RACA_COR" = '04' THEN 'Amarela' WHEN s."RACA_COR" = '05' THEN 'Indígena' ELSE 'Sem Informação' END
               AND p.nu_idade = CAST(NULLIF(TRIM(s."IDADE"), '') AS INTEGER)
               
            INNER JOIN dw.d_localidade l 
                ON CAST(l.cd_municipio AS TEXT) = CAST(s."MUNIC_RES" AS TEXT)
                
            INNER JOIN dw.d_diagnostico d 
                ON CAST(d.cd_cid AS TEXT) = CAST(s."DIAG_PRINC" AS TEXT)
                
            INNER JOIN dw.d_estabelecimento e 
                ON CAST(e.cd_cnes AS TEXT) = CAST(s."CNES" AS TEXT)

            -- FILTRO OFICIAL DO TCC: 
            -- Apenas população de 35+ anos, e isolando os 11 anos completos do IBGE
            WHERE CAST(NULLIF(TRIM(s."ANO_CMPT"), '') AS INTEGER) BETWEEN 2011 AND 2021
              AND CAST(NULLIF(TRIM(s."IDADE"), '') AS INTEGER) >= 35

            -- AGRUPAMENTO (Agrupa as métricas pelas 5 dimensões para otimizar o DW)
            GROUP BY 
                c.sk_calendario,
                p.sk_paciente,
                l.sk_localidade,
                d.sk_diagnostico,
                e.sk_estabelecimento;
        """)
        
        logger.info("Executando o JOIN massivo e calculando o FAP. Isso pode levar alguns minutos...")
        self.df = pd.read_sql_query(sql=query, con=self.engine)
        logger.info(f"Fato calculada! Total de {len(self.df)} linhas agregadas.")
        
    def transform(self):
        logger.info("Métricas validadas. Pronta para o Data Warehouse.")
        
    def load(self):
        logger.info("Injetando os dados no Data Warehouse (dw.f_internacao)...")
        self.df.to_sql(name='f_internacao', schema='dw', con=self.engine, if_exists='replace', index=False,
            chunksize=50000,
            dtype={
                'Id_calendario': BigInteger(),
                'Id_paciente': BigInteger(),
                'Id_localidade': BigInteger(),
                'Id_diagnostico': BigInteger(),
                'Id_estabelecimento': BigInteger(),
                'qt_internacoes': BigInteger(),
                'qt_mortes': BigInteger(),
                'qt_dias_permanencia': BigInteger(),
                'vl_total': Numeric(15,2)
            }
        )
        logger.success("Tabela f_internacao carregada com sucesso!")
        
    def run(self):
        logger.info("--- INICIANDO PIPELINE: FATO INTERNAÇÃO ---")
        start_time = time.time()
        
        self.extract()
        self.transform()
        self.load()
        
        end_time = time.time()
        logger.success(f"--- PIPELINE FINALIZADO EM {round(end_time - start_time, 2)} SEGUNDOS ---")

# Teste para rodar apenas esse arquivo
if __name__ == "__main__":
    robo = FatoInternacao()
    robo.run()