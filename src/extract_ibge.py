import os
import requests
import pandas as pd
from loguru import logger
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import time

def main():
    logger.info("Iniciando extração de dados da API SIDRA/IBGE (Série Histórica 2011-2021)...")
    

    lotes_anos = [
        "2011,2012,2013,2014,2015",
        "2016,2017,2018,2019,2020,2021"
    ]
    
    lista_dfs = []
    
    for lote in lotes_anos:
        url = f"https://apisidra.ibge.gov.br/values/t/6579/n6/all/p/{lote}/v/all"
        logger.info(f"Estabelecendo conexão com o endpoint da Tabela 6579 para os anos: {lote}...")
        
        try:
            response = requests.get(url)
            response.raise_for_status() 
            data = response.json()
            
        
            df_lote = pd.DataFrame(data[1:])
            lista_dfs.append(df_lote)
            
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Falha na comunicação com a API do IBGE no lote {lote}: {e}")
            return
            
    logger.info("Retorno da API recebido com sucesso. Unificando os lotes brutos (Staging/Raw Data)...")
    
    df_bruto = pd.concat(lista_dfs, ignore_index=True)
    
    total_linhas = len(df_bruto)
    logger.info(f"Processamento concluído: {total_linhas} registros obtidos.")
    
    logger.info("Adicionando metadados de ingestão (data_carga)...")
    df_bruto['data_carga'] = datetime.now()
    
    logger.info("Inicializando conexão com o banco de dados PostgreSQL...")
    load_dotenv()
    senha_do_banco = os.getenv("DB_PASSWORD")
    ip_do_banco = os.getenv("DB_HOST", "localhost") 
    senha_segura = quote_plus(senha_do_banco)
    
    engine = create_engine(f'postgresql+psycopg2://postgres:{senha_segura}@{ip_do_banco}:5432/sad_tabagismo')
    
    logger.info("Executando a carga de dados na tabela 'raw_ibge' (Modo: Replace)...")
    df_bruto.to_sql(name='raw_ibge', schema='staging', con=engine, if_exists='replace', index=False)
    
    logger.info("Extração e carga dos dados do IBGE concluídas com êxito.")

if __name__ == "__main__":
    main()