import pandas as pd


def basic_preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica pré-processamentos básicos e padronizados ao DataFrame.

    Esta função concentra transformações iniciais mínimas que devem ser
    compartilhadas entre notebooks, pipelines de treino e demais
    componentes do projeto, garantindo consistência estrutural desde
    as primeiras etapas do fluxo.

    As operações realizadas aqui são deliberadamente simples e
    não semânticas, com o objetivo de:
    - reduzir variações desnecessárias entre ambientes
    - facilitar integração entre etapas do pipeline
    - evitar repetição de lógica básica em múltiplos pontos

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame de entrada, normalmente resultante das etapas iniciais
        de ingestão e diagnóstico.

    Retorna
    -------
    pandas.DataFrame
        Novo DataFrame com as transformações básicas aplicadas.

    Observações
    -----------
    - Atualmente, a função realiza apenas a padronização dos nomes das
      colunas para letras minúsculas.
    - Não são aplicadas limpezas, imputações ou transformações de
      significado dos dados.
    - Esta função deve permanecer enxuta; pré-processamentos mais
      complexos ou específicos devem ser tratados em etapas posteriores
      do pipeline.
    """
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]
    return df

# Mapeamento do contrato (snake_case) -> nomes usados no treino (Telco)
COLUMN_MAP = {
    "tenure": "tenure",
    "contract": "Contract",
    "internet_service": "InternetService",
    "online_security": "OnlineSecurity",
    "tech_support": "TechSupport",
    "monthly_charges": "MonthlyCharges",
    "paperless_billing": "PaperlessBilling",
    "payment_method": "PaymentMethod",
}

def preprocess_input(input_dict: dict) -> pd.DataFrame:
    """
    Converte o payload de entrada da API para o schema esperado
    pelo pipeline de dados e modelos treinados.

    Esta função atua como camada de normalização entre o contrato
    externo da API (payload em `snake_case`, orientado ao cliente)
    e o schema interno utilizado pelo projeto ChurnInsight,
    garantindo compatibilidade estrutural com o dataset Telco
    utilizado no treinamento.

    O processo inclui:
    - validação explícita dos campos recebidos
    - mapeamento de nomes de campos via `COLUMN_MAP`
    - construção de um DataFrame compatível com o pipeline

    Parâmetros
    ----------
    input_dict : dict
        Dicionário representando o payload JSON recebido pela API,
        contendo pares chave–valor correspondentes às variáveis
        de entrada do modelo.

    Retorna
    -------
    pandas.DataFrame
        DataFrame com uma única linha, estruturado exatamente
        conforme o schema esperado pelo pipeline treinado.

    Exceções
    --------
    ValueError
        Lançada quando o payload contém campos não mapeados em
        `COLUMN_MAP`, evitando inconsistências silenciosas no fluxo.

    Observações
    -----------
    - Nenhuma transformação semântica ou conversão de tipo é aplicada aqui.
    - Esta função não realiza validação de domínio (faixas, categorias).
    - O contrato de entrada é estritamente controlado para preservar
      integridade entre API, FastAPI e camada de modelagem.
    - Alterações no schema do modelo exigem atualização explícita
      do `COLUMN_MAP`.
    """
    normalized = {}

    for k, v in input_dict.items():
        if k not in COLUMN_MAP:
            raise ValueError(f"Campo inesperado no payload: {k}")
        normalized[COLUMN_MAP[k]] = v

    df = pd.DataFrame([normalized])

    return df
