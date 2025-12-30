# src/data/load_data.py

from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import csv
import pandas as pd


# ---------------------------------------------------------------------
# Diretório padrão de dados brutos
# ---------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw"



# ---------------------------------------------------------------------
# Função utilitária para conversão de tamanho de arquivos
# ---------------------------------------------------------------------
def _format_size(size_bytes: int) -> str:
    """
    Converte um tamanho em bytes para uma representação legível por humanos.

    Esta função transforma um valor bruto em bytes em uma string formatada,
    utilizando unidades progressivas (bytes, KB, MB, GB, TB), com arredondamento
    para duas casas decimais.

    O objetivo é exclusivamente **visual e informativo**, sendo utilizada para
    exibição de tamanhos de arquivos ou consumo aproximado de memória no pipeline.

    Parâmetros
    ----------
    size_bytes : int
        Tamanho em bytes a ser convertido.

    Retorna
    -------
    str
        String formatada representando o tamanho em unidade legível
        (ex.: "954.59 KB", "1.23 MB").

    Observações
    -----------
    - A conversão percorre unidades progressivamente até encontrar a mais adequada.
    - Caso o valor exceda TB, a unidade PB é utilizada como fallback.
    - Esta função não deve ser usada para cálculos numéricos ou decisões lógicas;
      seu uso é restrito à apresentação e catalogação visual.
    """
    for unit in ["bytes", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

# ---------------------------------------------------------------------
# Utilitário: resolve o diretório raw
# ---------------------------------------------------------------------
def _resolve_raw_dir(raw_dir: Optional[str | Path] = None) -> Path:
    """
    Resolve e valida o diretório que contém os dados brutos do projeto.

    Caso um diretório seja informado explicitamente, ele é utilizado como base.
    Caso contrário, o diretório padrão de dados brutos definido pelo projeto
    é assumido.

    Parâmetros
    ----------
    raw_dir : str | pathlib.Path | None, opcional
        Caminho opcional para um diretório alternativo de dados brutos.
        Se None, utiliza o diretório padrão configurado no projeto.

    Retorna
    -------
    pathlib.Path
        Objeto Path apontando para o diretório de dados brutos validado.

    Exceções
    --------
    FileNotFoundError
        Lançada quando o diretório resolvido não existir no sistema de arquivos.
    """
    path = Path(raw_dir) if raw_dir else DEFAULT_RAW_DIR
    if not path.exists():
        raise FileNotFoundError(f"Diretório de dados não encontrado: {path}")
    return path


# ---------------------------------------------------------------------
# Listar arquivos disponíveis em data/raw
# ---------------------------------------------------------------------
def list_raw_files(raw_dir: Optional[str | Path] = None) -> pd.DataFrame:
    """
    Lista e cataloga os arquivos de dados brutos disponíveis para ingestão.

    Esta função percorre o diretório de dados brutos do projeto e constrói
    um catálogo estruturado contendo apenas arquivos suportados pelo pipeline
    (CSV e Parquet), juntamente com metadados básicos para rastreabilidade
    e diagnóstico inicial.

    O catálogo gerado é utilizado para:
    - identificar quais datasets estão disponíveis para ingestão
    - apoiar a seleção explícita do arquivo no notebook
    - exibir informações de tamanho e tipo de arquivo de forma legível

    Parâmetros
    ----------
    raw_dir : str | pathlib.Path | None, opcional
        Caminho alternativo para o diretório de dados brutos.
        Se None, utiliza o diretório padrão configurado no projeto.

    Retorna
    -------
    pandas.DataFrame
        DataFrame contendo o catálogo de arquivos disponíveis, com as colunas:
        - filename: nome do arquivo
        - extension: tipo do arquivo ("csv" ou "parquet")
        - size_bytes: tamanho do arquivo em bytes
        - size_human: tamanho do arquivo em formato legível por humanos

    Exceções
    --------
    FileNotFoundError
        Lançada quando:
        - o diretório resolvido não existir, ou
        - nenhum arquivo suportado (.csv ou .parquet) for encontrado
          no diretório resolvido.

    Observações
    -----------
    - Apenas arquivos no nível raiz do diretório são considerados.
    - Arquivos com extensões diferentes de CSV e Parquet são ignorados.
    - A função não realiza leitura de conteúdo dos arquivos.
    - Atua exclusivamente como componente de catalogação e diagnóstico
      da etapa de ingestão.
    """
    raw_path = _resolve_raw_dir(raw_dir)

    records = []

    for f in raw_path.iterdir():
        if f.is_file() and f.suffix.lower() in {".csv", ".parquet"}:
            size_bytes = f.stat().st_size
            records.append({
                "filename": f.name,
                "extension": f.suffix.lower().replace(".", ""),
                "size_bytes": size_bytes,
                "size_human": _format_size(size_bytes),
            })

    if not records:
        raise FileNotFoundError(
            "Nenhum arquivo .csv ou .parquet encontrado em data/raw."
        )

    return pd.DataFrame(records).sort_values("filename").reset_index(drop=True)



# ---------------------------------------------------------------------
# Detectar delimitador de CSV
# ---------------------------------------------------------------------
def _detect_csv_delimiter(csv_path: Path, sample_size: int = 2048) -> str:
    """
    Detecta automaticamente o delimitador utilizado em um arquivo CSV.

    Esta função tenta identificar o delimitador do arquivo CSV a partir
    de uma amostra inicial do seu conteúdo, utilizando `csv.Sniffer`.
    Caso a detecção automática falhe, aplica uma estratégia de fallback
    simples baseada na frequência dos separadores mais comuns na
    primeira linha do arquivo.

    O objetivo é tornar a ingestão de dados mais tolerante a variações
    frequentes de formato encontradas em datasets públicos, reduzindo
    a necessidade de configuração manual.

    Parâmetros
    ----------
    csv_path : pathlib.Path
        Caminho para o arquivo CSV cujo delimitador será detectado.

    sample_size : int, opcional
        Número de caracteres utilizados na leitura inicial para tentativa
        de detecção automática via `csv.Sniffer`.
        Padrão: 2048.

    Retorna
    -------
    str
        Caractere correspondente ao delimitador identificado
        (ex.: ',', ';').

    Observações
    -----------
    - A detecção automática utiliza apenas uma amostra inicial do arquivo.
    - Em caso de falha, o fallback compara a frequência de `;` e `,`
      na primeira linha do CSV.
    - A função não valida o conteúdo semântico do arquivo.
    - Atua exclusivamente como helper da etapa de ingestão.
    """
    try:
        with csv_path.open("r", encoding="utf-8", errors="ignore") as f:
            sample = f.read(sample_size)

        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample)
        return dialect.delimiter

    except Exception:
        # Fallback simples e eficaz
        with csv_path.open("r", encoding="utf-8", errors="ignore") as f:
            first_line = f.readline()

        if first_line.count(";") > first_line.count(","):
            return ";"
        return ","


# ---------------------------------------------------------------------
# Carregar dataset bruto
# ---------------------------------------------------------------------
def load_raw_data(
    filename: Optional[str] = None,
    raw_dir: Optional[str | Path] = None,
) -> pd.DataFrame:
    """
    Carrega um dataset bruto a partir do diretório de dados do projeto.

    Esta função é responsável pela leitura física dos dados brutos,
    suportando arquivos nos formatos CSV e Parquet. Para arquivos CSV,
    o delimitador é detectado automaticamente antes da leitura, visando
    maior robustez na ingestão de datasets públicos heterogêneos.

    O processo de seleção do arquivo segue regras explícitas:
    - se `filename` for informado, o arquivo correspondente é carregado
    - se `filename` for None e existir apenas um arquivo disponível,
      este é carregado automaticamente
    - se existir mais de um arquivo disponível e nenhum nome for
      especificado, a função falha de forma explícita solicitando
      escolha manual

    Parâmetros
    ----------
    filename : str | None, opcional
        Nome do arquivo a ser carregado a partir do diretório de dados
        brutos. Caso None, a função tenta inferir o arquivo quando houver
        apenas um disponível.

    raw_dir : str | pathlib.Path | None, opcional
        Caminho alternativo para o diretório de dados brutos.
        Se None, utiliza o diretório padrão configurado no projeto.

    Retorna
    -------
    pandas.DataFrame
        DataFrame contendo os dados brutos carregados do arquivo selecionado,
        sem aplicação de transformações ou pré-processamentos.

    Exceções
    --------
    FileNotFoundError
        Lançada quando o diretório de dados ou o arquivo especificado
        não existem.

    ValueError
        Lançada quando:
        - há múltiplos arquivos disponíveis e `filename` não é informado
        - o formato do arquivo não é suportado pelo pipeline

    Observações
    -----------
    - Esta função não realiza limpeza, tipagem ou validação semântica
      dos dados.
    - Atua exclusivamente na etapa de ingestão física do dataset.
    - A leitura de CSV utiliza delimitador detectado automaticamente
      via `_detect_csv_delimiter`.
    - O DataFrame retornado representa o estado bruto dos dados e
      deve ser tratado em etapas posteriores do pipeline.
    """
    raw_path = _resolve_raw_dir(raw_dir)
    catalog = list_raw_files(raw_path)

    # Se não passar filename
    if filename is None:
        if len(catalog) == 1:
            filename = str(catalog.loc[0, "filename"])
        else:
            available = catalog["filename"].tolist()
            raise ValueError(
                "Mais de um arquivo encontrado em data/raw. "
                "Informe explicitamente o nome do arquivo.\n"
                f"Arquivos disponíveis: {available}"
            )

    file_path = raw_path / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    suffix = file_path.suffix.lower()

    if suffix == ".parquet":
        return pd.read_parquet(file_path)

    if suffix == ".csv":
        delimiter = _detect_csv_delimiter(file_path)
        return pd.read_csv(file_path, delimiter=delimiter)

    raise ValueError(f"Formato de arquivo não suportado: {suffix}")

# ---------------------------------------------------------------------
# Orquestrador: carregar dataset bruto e exibir overview (modo notebook)
# ---------------------------------------------------------------------
def load_and_report_raw_data(
    filename: Optional[str] = None,
    raw_dir: Optional[str | Path] = None,
) -> pd.DataFrame:
    """
    Executa a Seção 1 do pipeline principal (N1): Ingestão e Diagnóstico Inicial.

    Esta função atua como orquestradora da Seção 1 do pipeline, combinando
    a ingestão física dos dados brutos com a renderização automática de
    um painel diagnóstico no notebook.

    Ela mantém a separação arquitetural ao:
    - delegar a leitura de dados exclusivamente a `load_raw_data()`
    - concentrar aqui a lógica de apresentação e orquestração
    - garantir que falhas de UI não interrompam o fluxo de dados

    O fluxo executado inclui:
    - carregamento do dataset bruto (CSV ou Parquet)
    - resolução do nome do arquivo para fins de exibição
    - renderização do painel de overview (Seção 1)
    - retorno do DataFrame carregado para continuidade do pipeline

    Parâmetros
    ----------
    filename : str | None, opcional
        Nome do arquivo localizado no diretório de dados brutos.
        Caso None, aplica-se a mesma regra de inferência definida em
        `load_raw_data()` (carregamento automático apenas quando há
        um único arquivo disponível).

    raw_dir : str | pathlib.Path | None, opcional
        Caminho alternativo para o diretório de dados brutos.
        Se None, utiliza o diretório padrão configurado no projeto.

    Retorna
    -------
    pandas.DataFrame
        DataFrame contendo os dados brutos carregados, representando
        o estado inicial do pipeline.

    Exceções
    --------
    FileNotFoundError, ValueError
        Propagadas de `load_raw_data()` quando aplicável.

    Observações
    -----------
    - Esta função é destinada principalmente ao notebook principal (N1),
      onde o pipeline é apresentado como relatório técnico interativo.
    - A renderização do painel é desacoplada da lógica de dados e protegida
      por bloco `try/except`, garantindo que falhas visuais não interrompam
      o pipeline.
    - Nenhuma transformação, limpeza ou tipagem é aplicada aos dados
      nesta etapa.
    - O DataFrame retornado deve ser utilizado como entrada direta
      para a Seção 2 do pipeline.
    """
    # 1) Carrega os dados (core, sem UI)
    df = load_raw_data(filename=filename, raw_dir=raw_dir)

    # 2) Resolve o nome do arquivo para exibição (se não foi informado)
    resolved_filename = filename
    if resolved_filename is None:
        try:
            raw_path = _resolve_raw_dir(raw_dir)
            catalog = list_raw_files(raw_path)
            if len(catalog) == 1:
                resolved_filename = str(catalog.loc[0, "filename"])
        except Exception:
            resolved_filename = None

    # 3) Renderiza painel (sempre) — import sob demanda para evitar acoplamento duro
    try:
        from src.reporting.ui import render_dataset_overview
        render_dataset_overview(
            df=df,
            source_name="main",
            filename=resolved_filename,
            max_missing_rows=12
        )
    except Exception as e:
        # Falha de UI não deve impedir o pipeline de dados
        print(f"[WARN] Falha ao renderizar painel de overview: {e}")

    return df
