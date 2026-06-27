import os
import pandas as pd
from loguru import logger
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from urllib.parse import quote_plus

if not hasattr(pd.DataFrame, "applymap"):
    pd.DataFrame.applymap = pd.DataFrame.map

from pysus.ftp.databases.sih import SIH

def main():
    logger.info("Iniciando Extração de dados do SIH/SUS (2014-2024)...")
    
    anos = list(range(2011, 2014))  
    meses = list(range(1, 13))      
    ufs = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
    grupo = "RD"
    
    pasta_destino = os.path.join("data", "raw")
    os.makedirs(pasta_destino, exist_ok=True)
    
    colunas_para_manter = [
        'N_AIH', 'UF_ZI', 'ANO_CMPT', 'MES_CMPT', 'MUNIC_RES', 'MUNIC_MOV', 
        'SEXO', 'NASC', 'IDADE', 'COD_IDADE', 'RACA_COR', 'DIAS_PERM', 
        'MORTE', 'DIAG_PRINC', 'DIAG_SECUN', 'VAL_TOT', 'CNES', 'DT_INTER'
    ]
    
    # Prefixos CID-10 relacionados ao tabagismo (Cânceres, Cardiovasculares, Respiratórias + Dicionário Oficial)
    cids_tabagismo = (
        'C00', 'C01', 'C02', 'C03', 'C04', 'C05', 'C06', 'C07', 'C08', 'C09', 'C10', 'C11', 'C12', 'C13', 'C14', 
        'C15', 'C25', 'C32', 'C33', 'C34', 'C53', 'C67',
        'I20', 'I21', 'I22', 'I23', 'I24', 'I25', 'I60', 'I61', 'I62', 'I63', 'I64', 'I65', 'I66', 'I67', 'I68', 'I69', 'I70',
        'J40', 'J41', 'J42', 'J43', 'J44', 'J45', 'J46',
        'F17', 'Z72', 'T65' 
    )
    
    logger.info("Abrindo o cofre de senhas (.env)...")
    load_dotenv()
    senha_do_banco = os.getenv("DB_PASSWORD")
    ip_do_banco = os.getenv("DB_HOST", "localhost") 
    
    senha_segura = quote_plus(senha_do_banco)
    logger.info(f"Conectando ao PostgreSQL em {ip_do_banco}...")
    engine = create_engine(f'postgresql+psycopg2://postgres:{senha_segura}@{ip_do_banco}:5432/sad_tabagismo')
    
    primeira_insercao = False
    
    sih = SIH().load()
    
    for ano in anos:
        for mes in meses:
            logger.info(f"Buscando arquivos para: Todos os Estados, Ano={ano}, Mês={mes}")
            
            try:
                arquivos = sih.get_files(group=grupo, uf=ufs, year=ano, month=mes)
                
                if not arquivos:
                    logger.warning(f"Nenhum arquivo encontrado no FTP para {mes}/{ano}. Pulando...")
                    continue
                
                logger.info(f"Baixando {len(arquivos)} arquivos de {mes}/{ano}...")
                parquets = sih.download(arquivos, local_dir=pasta_destino)
                
                logger.info("Convertendo para DataFrame unificado...")
                try:
                    df = parquets.to_dataframe()
                except AttributeError:
                    df = pd.concat([p.to_dataframe() for p in parquets], ignore_index=True)
                
                total_linhas_brutas = len(df)
                
                logger.info("Aplicando filtros de Colunas e CIDs...")
                
                colunas_existentes = [col for col in colunas_para_manter if col in df.columns]
                df_filtrado = df[colunas_existentes].copy()
                
                
                # Verifica se o CID de tabagismo está na coluna de Diagnóstico Principal
                mascara_princ = df_filtrado['DIAG_PRINC'].astype(str).str.startswith(cids_tabagismo)
                
                # Verifica se a coluna Diagnóstico Secundário existe neste arquivo antigo do SUS
                if 'DIAG_SECUN' in df_filtrado.columns:
                    # Se existir, verifica se o CID de tabagismo está no Secundário
                    mascara_sec = df_filtrado['DIAG_SECUN'].astype(str).str.startswith(cids_tabagismo)
                    
                    df_filtrado = df_filtrado[mascara_princ | mascara_sec] 
                else:
                    df_filtrado = df_filtrado[mascara_princ]
                    
                total_linhas_filtradas = len(df_filtrado)
                logger.info(f"Filtro aplicado: de {total_linhas_brutas} para apenas {total_linhas_filtradas} dados de interesse.")
                
                if total_linhas_filtradas == 0:
                    logger.info("Nenhum dado de tabagismo neste lote. Pulando inserção no banco.")
                    continue
                
                df_filtrado['data_carga'] = datetime.now()
                
                modo_insercao = 'replace' if primeira_insercao else 'append'
                
                logger.info(f"Injetando {total_linhas_filtradas} linhas no PostgreSQL (Modo: {modo_insercao})...")
                df_filtrado.to_sql(name='raw_sih', schema='staging', con=engine, if_exists=modo_insercao, index=False)
                logger.success(f"Dados de {mes}/{ano} salvos com sucesso!")
                
                primeira_insercao = False 
                
            except Exception as e:
                logger.error(f"Erro ao processar o lote {mes}/{ano}: {e}")
                logger.warning("Pulando para o próximo mês para não interromper o fluxo...")
                continue
                
    logger.info("🎉 EXTRAÇÃO DE 11 ANOS CONCLUÍDA COM SUCESSO!")

if __name__ == "__main__":
    main()