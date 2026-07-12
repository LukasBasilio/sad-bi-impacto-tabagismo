# Sistema de Apoio à Decisão (SAD) — Impacto do Tabagismo no SUS 📊🏥

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)
[![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)

Projeto final da disciplina de **Gerenciamento de Banco de Dados (COM11014)** — Ciência da Computação, UFES (2026/1).

Pipeline completo de **Engenharia de Dados e Business Intelligence** para analisar o impacto epidemiológico e financeiro do tabagismo no Sistema Único de Saúde (SUS) do Brasil ao longo de uma década (2011–2021).

---

## 🏗️ Arquitetura do Sistema

O projeto foi estruturado em uma arquitetura analítica de 4 camadas:

1. **Fontes de Dados Governamentais:**
   - Extração de 132 arquivos `.dbc` do **DATASUS** (Sistema de Informações Hospitalares — SIH) via FTP, utilizando a biblioteca PySUS.
   - Consumo da API SIDRA do **IBGE** para obter estimativas populacionais anuais dos 5.570 municípios brasileiros.

2. **Pipeline de ETL (Python):**
   - Scripts em Python (Pandas + SQLAlchemy) para extrair, filtrar por CID-10, aplicar a Fração Atribuível Populacional (FAP), gerar Surrogate Keys, decodificar códigos governamentais e carregar os dados no banco.

3. **Armazenamento (PostgreSQL):**
   - Schema `staging` com tabelas brutas (`raw_sih`, `raw_ibge`).
   - Schema `dw` com um **Star Schema**: 2 Tabelas Fato e 5 Tabelas Dimensão, todas com Surrogate Keys inteiras.

4. **Camada Semântica e Visualização (Power BI):**
   - Conexão direta com o PostgreSQL via conector nativo, 10 medidas dinâmicas em **DAX** e 6 Dashboards interativos.

---

## 📈 Dashboards

| Dashboard | Pergunta que responde |
|-----------|----------------------|
| **D1 — Visão Geral** | O QUE está acontecendo? (custo total, internações, óbitos) |
| **D2 — Geográfico** | ONDE a situação é mais crítica? (taxas por 100 mil hab.) |
| **D3 — Demográfico** | QUEM é a principal vítima? (sexo, faixa etária, raça) |
| **D4 — Gravidade** | QUÃO grave é cada doença? (letalidade, permanência) |
| **D5 — Per Capita** | QUANTO custa ao cidadão? (cruzamento SUS × IBGE) |
| **D6 — Tendência** | PARA ONDE estamos indo? (evolução da década) |

---

## 📁 Estrutura do Repositório

```text
sad-bi-impacto-tabagismo/
│
├── src/                            # Pipeline de ETL (Python)
│   ├── extract_sih.py              # Extração e filtragem dos dados do SUS (SIH)
│   ├── extract_ibge.py             # Extração da API SIDRA do IBGE
│   ├── dimensao.py                 # Script orquestrador das dimensões
│   ├── d_calendario.py             # Geração da dimensão Calendário
│   ├── d_localidade.py             # Geração da dimensão Localidade
│   ├── d_paciente.py               # Geração da dimensão Paciente
│   ├── d_diagnostico.py            # Geração da dimensão Diagnóstico (+ FAP)
│   ├── d_estabelecimento.py        # Geração da dimensão Estabelecimento
│   ├── f_internacao.py             # Carga da Tabela Fato de Internações
│   └── f_populacao.py              # Carga da Tabela Fato de População
│
├── docs/                           # Documentação e artefatos
│   ├── Trabalho_Integracao_...pdf  # Relatório final do projeto
│   ├── Descrição do Trabalho.pdf   # Enunciado da disciplina
│   ├── arquitetura_sistema.drawio  # Diagrama de arquitetura (editável)
│   ├── arquitetura.png             # Imagem da arquitetura
│   ├── modelo_estrela.drawio       # Diagrama Star Schema (editável)
│   ├── modelo_estrela.jpg          # Imagem do modelo estrela
│   ├── BI_TABAGISMO.pbix           # Arquivo do Power BI
│   ├── BI_TABAGISMO.pbit           # Template do Power BI
│   ├── INCA_2020.pdf               # Referência: Carga do Tabagismo no Brasil
│   └── Pinto_et_al_2015.pdf        # Referência: Artigo científico FAP
│
└── README.md
```

---

## ⚙️ Tecnologias Utilizadas

| Camada | Tecnologia | Finalidade |
|--------|-----------|------------|
| Extração | Python, PySUS, requests | Download de dados do SUS e IBGE |
| Transformação | Pandas, NumPy | Limpeza, FAP, Surrogate Keys |
| Armazenamento | PostgreSQL, SQLAlchemy | Data Warehouse (Star Schema) |
| Visualização | Power BI, DAX | Dashboards interativos |

---

> *Os dados brutos (`data/`) e ambientes virtuais (`.venv/`) foram omitidos do versionamento por questão de armazenamento.*
