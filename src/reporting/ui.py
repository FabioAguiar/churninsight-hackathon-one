from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
from IPython.display import HTML, display


# ---------------------------------------------------------------------
# UI Theme (leve, neutro e "mesclado" com o fundo do notebook)
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class UITheme:
    # Cores neutras (parecer "nativo" do notebook)
    bg: str = "#ffffff"
    card_bg: str = "#ffffff"
    border: str = "#e6e8ee"
    border_soft: str = "#f0f2f6"
    text: str = "#111827"
    muted: str = "#6b7280"

    # Accent (azul discreto, estilo form)
    accent: str = "#2563eb"       # blue-600
    accent_soft: str = "#eff6ff"  # blue-50

    # Status
    ok: str = "#16a34a"           # green-600
    warn: str = "#f59e0b"         # amber-500
    bad: str = "#ef4444"          # red-500


DEFAULT_THEME = UITheme()


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _human_mb(num_bytes: int) -> float:
    """
    Converte um valor de memória em bytes para megabytes (MB).

    Esta função é utilizada exclusivamente para fins de exibição
    em elementos visuais do pipeline (UI do notebook), permitindo
    que métricas de uso de memória sejam apresentadas de forma
    legível e comparável entre etapas.

    A conversão utiliza base binária (1 MB = 1024² bytes), mantendo
    consistência com o comportamento interno do pandas ao calcular
    `memory_usage(deep=True)`.

    Parâmetros
    ----------
    num_bytes : int
        Quantidade de memória em bytes.

    Retorna
    -------
    float
        Valor equivalente em megabytes (MB).

    Observações
    -----------
    - Esta função não realiza arredondamento; a formatação final
      (casas decimais) deve ser responsabilidade da camada de UI.
    - Não deve ser utilizada para cálculos de negócio ou decisões
      técnicas, apenas para apresentação visual.
    """
    return num_bytes / (1024 ** 2)



def _safe_html(s: str) -> str:
    """
    Realiza escaping mínimo de caracteres especiais para uso seguro em HTML.

    Esta função garante que valores dinâmicos (como nomes de colunas,
    arquivos ou conteúdos textuais derivados do dataset) possam ser
    inseridos em templates HTML sem quebrar a estrutura do documento
    ou causar renderização incorreta.

    O escaping aplicado é propositalmente limitado aos caracteres
    mais comuns que interferem em HTML:
    - &
    - <
    - >
    - aspas duplas
    - aspas simples

    Parâmetros
    ----------
    s : str
        Valor de entrada que será convertido para string e escapado
        antes de ser interpolado em HTML.

    Retorna
    -------
    str
        String com caracteres especiais substituídos por entidades HTML.

    Observações
    -----------
    - Esta função **não é um sanitizador completo contra XSS**.
      Seu uso é restrito ao contexto controlado do notebook, onde
      os valores exibidos derivam do próprio dataset ou do sistema.
    - Não deve ser utilizada para escapar HTML oriundo de fontes
      externas não confiáveis.
    - O objetivo é estabilidade visual e segurança básica do display,
      não segurança web em produção.
    """
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )



def _df_to_html_table(df: pd.DataFrame, max_rows: int = 12) -> str:
    """
    Converte um DataFrame em uma tabela HTML compacta e consistente com
    a estética visual do pipeline (N1).

    Esta função é utilizada pela camada de UI para renderizar tabelas
    informativas (diagnósticas), priorizando legibilidade, estabilidade
    visual e controle de volume de dados exibidos no notebook.

    O HTML gerado:
    - evita bordas pesadas e estilos intrusivos
    - mantém alinhamento com o tema global do projeto
    - aplica truncamento controlado de linhas e valores textuais
    - realiza escaping mínimo de conteúdo para segurança do display

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame a ser renderizado. Espera-se que os dados já estejam
        preparados e ordenados pela camada de lógica do pipeline.

    max_rows : int, opcional (padrão = 12)
        Número máximo de linhas a serem exibidas. Caso o DataFrame
        possua mais linhas, apenas o topo é apresentado para preservar
        legibilidade e performance do notebook.

    Retorna
    -------
    str
        String contendo o HTML da tabela pronta para inserção direta
        no display do notebook.

    Observações
    -----------
    - Esta função não executa cálculos nem transforma dados; atua
      exclusivamente como utilitário de apresentação.
    - Não deve ser utilizada para renderização de grandes volumes
      de dados ou como substituta de componentes de visualização
      interativos.
    - O controle de conteúdo exibido (quais colunas e ordenação)
      é responsabilidade da camada de pipeline, não desta função.
    """
    view = df.copy()
    if len(view) > max_rows:
        view = view.head(max_rows)

    # Evitar colunas gigantes no HTML
    for col in view.columns:
        view[col] = view[col].astype(str).map(lambda x: x if len(x) <= 60 else x[:57] + "...")

    # HTML manual (mais controle visual do que df.to_html)
    headers = "".join([f"<th>{_safe_html(c)}</th>" for c in view.columns])
    rows_html = []
    for _, row in view.iterrows():
        tds = "".join([f"<td>{_safe_html(v)}</td>" for v in row.values])
        rows_html.append(f"<tr>{tds}</tr>")

    return f"""
    <div class="ci-table-wrap">
      <table class="ci-table" role="table">
        <thead><tr>{headers}</tr></thead>
        <tbody>
          {''.join(rows_html) if rows_html else '<tr><td colspan="99" class="ci-muted">Sem linhas para exibir.</td></tr>'}
        </tbody>
      </table>
    </div>
    """


def _dtype_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Gera um resumo da distribuição de tipos de dados do DataFrame.

    Esta função contabiliza a quantidade de colunas associadas a cada
    tipo (`dtype`) presente no DataFrame, produzindo uma visão
    estrutural agregada da tipagem dos dados.

    O resumo resultante é utilizado como elemento diagnóstico para:
    - compreensão rápida da composição estrutural do dataset
    - apoio à leitura do pipeline visual
    - antecipação de decisões de pré-processamento e tipagem

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame ativo cuja tipagem das colunas será analisada.

    Retorna
    -------
    pandas.DataFrame
        DataFrame com duas colunas:
        - dtype: representação textual do tipo de dado
        - cols: quantidade de colunas associadas a cada dtype

    Observações
    -----------
    - Os tipos refletem o estado atual do DataFrame no momento da chamada.
    - A função não realiza inferência semântica sobre as variáveis.
    - O resultado é adequado para exibição resumida, não para análise
      individual de colunas.
    """
    s = df.dtypes.astype(str).value_counts()
    out = s.reset_index()
    out.columns = ["dtype", "cols"]
    return out


def _missing_summary(df: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
    """
    Gera um resumo das colunas com valores ausentes no DataFrame.

    Esta função calcula, para cada coluna, a quantidade e o percentual
    de valores ausentes, ordenando o resultado de forma decrescente
    para destacar os pontos mais críticos do dataset.

    O resumo é utilizado como elemento diagnóstico para:
    - identificação rápida de colunas problemáticas
    - priorização de estratégias de imputação ou exclusão
    - suporte visual à avaliação inicial de qualidade dos dados

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame ativo a ser analisado quanto à presença de valores ausentes.

    top_n : int, opcional
        Número máximo de colunas a serem retornadas no resumo,
        ordenadas por maior incidência de valores ausentes.
        Padrão: 12.

    Retorna
    -------
    pandas.DataFrame
        DataFrame com as seguintes colunas:
        - column: nome da coluna
        - missing: quantidade absoluta de valores ausentes
        - dtype: tipo de dado da coluna no momento da análise
        - pct_missing: percentual de valores ausentes em relação ao total de linhas

    Observações
    -----------
    - O percentual de faltantes é calculado em relação ao número total
      de linhas do DataFrame.
    - Apenas as `top_n` colunas com maior incidência de faltantes são retornadas.
    - A função não altera o DataFrame original.
    - O resultado é adequado para exibição diagnóstica, não para
      decisões automáticas de limpeza.
    """
    miss = df.isna().sum()
    out = miss.reset_index()
    out.columns = ["column", "missing"]
    out["dtype"] = out["column"].map(df.dtypes.astype(str))
    out["pct_missing"] = (out["missing"] / len(df) * 100).round(2)

    out = out.sort_values(["missing", "pct_missing"], ascending=False)
    return out.head(top_n)


def _missing_badge(pct_missing: float, theme: UITheme) -> tuple[str, str]:
    """
    Classifica a severidade de valores ausentes para fins de exibição visual.

    Esta função traduz um percentual de valores ausentes em um rótulo
    qualitativo de severidade e em uma cor associada ao tema visual,
    permitindo sinalização rápida do estado de qualidade dos dados
    no painel do notebook.

    A classificação é utilizada exclusivamente para:
    - indicação visual (badges, cores, status)
    - apoio à leitura humana do diagnóstico
    - padronização estética entre seções do pipeline

    Parâmetros
    ----------
    pct_missing : float
        Percentual de valores ausentes no dataset ou em um subconjunto,
        expresso como valor entre 0 e 100.

    theme : UITheme
        Tema visual ativo, do qual são extraídas as cores associadas
        a cada nível de severidade.

    Retorna
    -------
    tuple[str, str]
        Tupla contendo:
        - label: rótulo textual de severidade ("OK", "Baixo", "Alto")
        - color: código de cor correspondente no tema visual

    Observações
    -----------
    - Os limiares atuais são:
        * 0%          → OK
        * >0% e ≤5%   → Baixo
        * >5%         → Alto
    - Os limiares são heurísticos e podem ser ajustados sem impacto
      no core de dados ou no pipeline de modelagem.
    - Esta função não deve ser utilizada para decisões automáticas
      de limpeza ou descarte de dados.
    """
    if pct_missing == 0:
        return ("OK", theme.ok)
    if pct_missing <= 5:
        return ("Baixo", theme.warn)
    return ("Alto", theme.bad)


# ---------------------------------------------------------------------
# Main Renderer
# ---------------------------------------------------------------------
def render_dataset_overview(
    df: pd.DataFrame,
    source_name: str = "main",
    filename: Optional[str] = None,
    max_missing_rows: int = 12,
    theme: UITheme = DEFAULT_THEME,
) -> None:
    """
    Renderiza o painel de overview do dataset no notebook (Seção 1 do pipeline).

    Este renderer compõe uma “tela” HTML integrada ao notebook, com foco em
    diagnóstico inicial e rastreabilidade da ingestão. Ele consolida, em um
    único painel, informações estruturais e indicadores simples de qualidade,
    sem aplicar qualquer transformação no DataFrame.

    Elementos exibidos (mapeáveis para documentação do pipeline):
    - Identificação do arquivo (rastreabilidade da fonte)
    - Indicador global de faltantes (badge: OK/Baixo/Alto + percentual)
    - Métricas gerais (linhas, colunas, memória)
    - Tipos de dados (contagem agregada por dtype)
    - Faltantes (top N colunas por quantidade/percentual)

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame ativo recém-ingerido (estado atual dos dados). A função
        apenas lê o conteúdo para calcular métricas diagnósticas.

    source_name : str, opcional
        Identificador lógico da origem do dataset (ex.: "main"). Mantido
        para rastreabilidade e possível expansão futura (não altera a UI
        atual de forma obrigatória).

    filename : str | None, opcional
        Nome do arquivo carregado (exibido no header). Se None, um placeholder
        é exibido.

    max_missing_rows : int, opcional
        Número máximo de linhas exibidas na tabela de faltantes (top N).
        Padrão: 12.

    theme : UITheme, opcional
        Tema visual da UI (cores e estilos). Padrão: DEFAULT_THEME.

    Retorna
    -------
    None
        A função renderiza HTML diretamente no notebook via IPython.display.

    Exceções
    --------
    TypeError
        Se `df` não for um pandas.DataFrame.

    Observações
    -----------
    - Este renderer é exclusivo para notebooks (Jupyter). Não é destinado
      a uso em APIs/serviços.
    - Toda lógica de apresentação (HTML/CSS) vive aqui; toda lógica de
      transformação/decisão deve permanecer fora (core do pipeline).
    - O indicador global de faltantes é calculado sobre todas as células
      do DataFrame e classificado por limiares heurísticos (via `_missing_badge`).
    """
    if df is None or not isinstance(df, pd.DataFrame):
        raise TypeError("render_dataset_overview espera um pandas.DataFrame em `df`.")

    n_rows, n_cols = df.shape
    mem_mb = _human_mb(int(df.memory_usage(deep=True).sum()))

    dtypes_df = _dtype_summary(df)
    missing_df = _missing_summary(df, top_n=max_missing_rows)

    # Indicador geral de faltantes (badge)
    overall_missing_pct = float((df.isna().sum().sum() / (n_rows * max(n_cols, 1))) * 100) if n_rows else 0.0
    miss_label, miss_color = _missing_badge(round(overall_missing_pct, 2), theme)

    # Construir cards de métricas (visuais)
    def metric_card(label: str, value: str, hint: str = "") -> str:
        hint_html = f'<div class="ci-metric-hint">{_safe_html(hint)}</div>' if hint else ""
        return f"""
        <div class="ci-metric">
          <div class="ci-metric-label">{_safe_html(label)}</div>
          <div class="ci-metric-value">{_safe_html(value)}</div>
          {hint_html}
        </div>
        """

    filename_display = filename or "—"

    # CSS (discreto, sem "caixa pesada")
    css = f"""
    <style>
      .ci-panel {{
        background: {theme.bg};
        border: 1px solid {theme.border_soft};
        border-radius: 14px;
        padding: 18px 18px 14px 18px;
        margin: 10px 0 14px 0;
        color: {theme.text};
        font-family: Arial, sans-serif;
      }}

      .ci-header {{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
        padding-bottom: 10px;
        border-bottom: 1px solid {theme.border_soft};
        margin-bottom: 12px;
      }}

      .ci-title {{
        margin: 0;
        font-size: 16px;
        font-weight: 700;
        letter-spacing: 0.2px;
      }}

      .ci-sub {{
        margin: 6px 0 0 0;
        color: {theme.muted};
        font-size: 12px;
        line-height: 1.35;
      }}

      .ci-badge {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid {theme.border};
        background: {theme.card_bg};
        font-size: 12px;
        color: {theme.muted};
        white-space: nowrap;
      }}
      .ci-dot {{
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: {miss_color};
      }}

      .ci-grid {{
        display: grid;
        grid-template-columns: 1.1fr 0.9fr;
        gap: 12px;
        margin-top: 12px;
      }}

      .ci-card {{
        background: {theme.card_bg};
        border: 1px solid {theme.border};
        border-radius: 14px;
        padding: 14px;
      }}

      .ci-card h4 {{
        margin: 0 0 10px 0;
        font-size: 13px;
        font-weight: 700;
        color: {theme.text};
      }}

      .ci-meta {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px 16px;
        margin-top: 8px;
      }}
      .ci-meta-item {{
        font-size: 12px;
        color: {theme.muted};
      }}
      .ci-meta-item strong {{
        color: {theme.text};
        font-weight: 700;
      }}

      .ci-metrics {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
        margin-top: 10px;
      }}

      .ci-metric {{
        border: 1px solid {theme.border_soft};
        background: {theme.accent_soft};
        border-radius: 12px;
        padding: 10px 12px;
      }}
      .ci-metric-label {{
        font-size: 11px;
        color: {theme.muted};
        margin-bottom: 6px;
      }}
      .ci-metric-value {{
        font-size: 16px;
        font-weight: 800;
        color: {theme.text};
        letter-spacing: 0.2px;
      }}
      .ci-metric-hint {{
        margin-top: 6px;
        font-size: 11px;
        color: {theme.muted};
      }}

      .ci-table-wrap {{
        width: 100%;
        overflow-x: auto;
      }}
      .ci-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 12px;
      }}
      .ci-table thead th {{
        text-align: left;
        padding: 9px 10px;
        border-bottom: 1px solid {theme.border};
        color: {theme.muted};
        font-weight: 700;
        background: #fff;
        position: sticky;
        top: 0;
      }}
      .ci-table tbody td {{
        padding: 8px 10px;
        border-bottom: 1px solid {theme.border_soft};
        color: {theme.text};
      }}
      .ci-table tbody tr:hover td {{
        background: #fafafa;
      }}
      .ci-muted {{
        color: {theme.muted};
      }}

      .ci-foot {{
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid {theme.border_soft};
        font-size: 11px;
        color: {theme.muted};
        display: flex;
        justify-content: space-between;
        gap: 10px;
        flex-wrap: wrap;
      }}

      /* responsivo */
      @media (max-width: 900px) {{
        .ci-grid {{ grid-template-columns: 1fr; }}
        .ci-metrics {{ grid-template-columns: 1fr; }}
      }}
    </style>
    """

    # Cards content
    metrics_html = f"""
    <div class="ci-metrics">
      {metric_card("Linhas", f"{n_rows:,}".replace(",", "."), "Quantidade de registros")}
      {metric_card("Colunas", f"{n_cols:,}".replace(",", "."), "Quantidade de variáveis")}
      {metric_card("Memória", f"{mem_mb:.3f} MB", "Uso aproximado (deep=True)")}
    </div>
    """

    dtype_table = _df_to_html_table(dtypes_df, max_rows=12)

    # missing table com badge por linha (OK/Baixo/Alto)
    missing_view = missing_df.copy()
    if not missing_view.empty:
        missing_view["severity"] = missing_view["pct_missing"].map(
            lambda p: _missing_badge(float(p), theme)[0]
        )
        # reordenar colunas
        missing_view = missing_view[["column", "dtype", "missing", "pct_missing", "severity"]]

    missing_table = _df_to_html_table(missing_view, max_rows=max_missing_rows)

    html = f"""
    {css}
    <div class="ci-panel">
      <div class="ci-header">
        <div>
          <!-- <h3 class="ci-title">📥 Ingestão — Visão Geral do Dataset</h3> -->
          <div class="ci-sub">
            <div><strong>Arquivo:</strong> {_safe_html(filename_display)}</div>
          </div>
        </div>

        <div class="ci-badge" title="Severidade geral aproximada de faltantes no dataset">
          <span class="ci-dot"></span>
          <span><strong>Faltantes:</strong> {_safe_html(miss_label)} ({overall_missing_pct:.2f}%)</span>
        </div>
      </div>

      <div class="ci-card">
        <h4>Métricas gerais</h4>
        {metrics_html}
      </div>

      <div class="ci-grid">
        <div class="ci-card">
          <h4>Tipos </h4>
          {dtype_table}
        </div>

        <div class="ci-card">
          <h4>Faltantes (top {max_missing_rows})</h4>
          {missing_table}
        </div>
      </div>

      <div class="ci-foot">
      </div>
    </div>
    """

    display(HTML(html))



# ============================================================
# Seção 2 — Qualidade Estrutural & Tipagem 
# ============================================================

def render_quality_typing_overview(
    *,
    impact_df: pd.DataFrame,
    conversions_df: pd.DataFrame,
    dup_info: dict,
    introduced_nans_df: pd.DataFrame,
    title: str = "🧹 Qualidade Estrutural & Tipagem",
    theme: UITheme = DEFAULT_THEME,
) -> None:
    """
    Renderiza o painel da Seção 2 do pipeline principal (N1):
    Qualidade Estrutural & Tipagem.

    Este renderer apresenta, de forma visual e organizada, os principais
    impactos estruturais decorrentes de conversões de tipo e checagens
    básicas de integridade, utilizando cards conceitualmente isolados
    e diretamente rastreáveis para a documentação técnica do pipeline.

    Mapeamento conceitual dos elementos exibidos:
    - S2.1 → Impacto estrutural (Antes × Depois)
    - S2.2 → Conversões de tipos aplicadas
    - S2.3 → Integridade estrutural (duplicidades)
    - S2.4 → Nulos introduzidos por conversão

    Parâmetros
    ----------
    impact_df : pandas.DataFrame
        Tabela comparativa (antes × depois) contendo métricas estruturais
        básicas do dataset, como linhas, colunas e uso de memória.

    conversions_df : pandas.DataFrame
        Relatório de conversões de tipo efetivamente aplicadas, contendo
        apenas colunas que sofreram alteração de dtype ou introdução
        de valores nulos.

    dup_info : dict
        Resultado da checagem de duplicidades estruturais, contendo:
        - has_duplicates (bool)
        - duplicate_count (int)

    introduced_nans_df : pandas.DataFrame
        Resumo das colunas nas quais conversões de tipo introduziram
        valores nulos, incluindo impacto absoluto e percentual.

    title : str, opcional
        Título exibido no cabeçalho da seção.
        Padrão: "🧹 Qualidade Estrutural & Tipagem".

    theme : UITheme, opcional
        Tema visual utilizado para cores, badges e estilos.
        Padrão: DEFAULT_THEME.

    Retorna
    -------
    None
        A função renderiza HTML diretamente no notebook via IPython.display.

    Observações
    -----------
    - Este renderer não executa nenhuma lógica de cálculo ou transformação.
    - Todos os dados devem chegar pré-processados a partir do core (`src/data`).
    - A função segue a mesma estética e filosofia visual da Seção 1,
      mantendo consistência entre os painéis do pipeline.
    - O layout utiliza um grid 1×2 para separar claramente:
        * conversões de tipo
        * integridade estrutural
        * nulos introduzidos
    - Esta função é destinada exclusivamente à apresentação em notebooks
      (Jupyter), não devendo ser utilizada em APIs ou serviços.
    """
    # --------------------------
    # Preparações
    # --------------------------
    has_dup = bool(dup_info.get("has_duplicates", False))
    dup_count = int(dup_info.get("duplicate_count", 0))

    dup_badge = (
        f"<span style='color:{theme.bad}; font-weight:700;'>⚠ {dup_count} duplicidades detectadas</span>"
        if has_dup
        else f"<span style='color:{theme.ok}; font-weight:700;'>✓ Nenhuma duplicidade detectada</span>"
    )

    impact_table = _df_to_html_table(impact_df, max_rows=6)

    conversions_table = (
        _df_to_html_table(conversions_df, max_rows=8)
        if conversions_df is not None and not conversions_df.empty
        else "<div class='ci-muted'>Nenhuma conversão de tipo aplicada.</div>"
    )

    introduced_nans_table = (
        _df_to_html_table(introduced_nans_df, max_rows=8)
        if introduced_nans_df is not None and not introduced_nans_df.empty
        else "<div class='ci-muted'>Sem nulos introduzidos por conversão.</div>"
    )

    html = f"""
    <div class="ci-panel">
      <div class="ci-header">
        <div>
          <p class="ci-sub">Conversões, memória e checagens estruturais básicas</p>
        </div>
      </div>

      <!-- S2.1 — Impacto estrutural -->
      <div class="ci-card">
        <h4>Impacto estrutural (Antes × Depois)</h4>
        {impact_table}
      </div>

      <!-- Grid 1×2 -->
      <div class="ci-grid">

        <!-- Coluna esquerda -->
        <div class="ci-card">
          <!-- S2.2 — Conversões de tipos -->
          <h4>Conversões de tipos aplicadas</h4>
          <div class="ci-sub">Somente colunas que sofreram alteração</div>
          {conversions_table}
        </div>

        <!-- Coluna direita -->
        <div>
          <!-- S2.3 — Integridade estrutural -->
          <div class="ci-card" style="margin-bottom:12px;">
            <h4>Integridade estrutural</h4>
            {dup_badge}
          </div>

          <!-- S2.4 — Nulos introduzidos -->
          <div class="ci-card">
            <h4>Nulos introduzidos por conversão</h4>
            {introduced_nans_table}
            <div class="ci-sub" style="margin-top:8px;">
              Valores introduzidos indicam entradas não parseáveis
              (ex.: strings vazias).
            </div>
          </div>
        </div>

      </div>

      <div class="ci-foot">
        <div>
          <strong>Nota:</strong> Nenhuma transformação semântica foi aplicada nesta seção.
        </div>
      </div>
    </div>
    """

    display(HTML(html))


# ============================================================
# Seção 3 — Conformidade ao Contrato + Diagnóstico de Candidatos à Padronização Categórica
# ============================================================
def render_contract_and_candidates_report(payload: dict) -> None:
    """
    Renderiza o painel da Seção 3 do pipeline no notebook:
    conformidade ao contrato de entrada (API) e diagnóstico de candidatos
    à padronização categórica.

    Este renderer compõe uma UI compacta em HTML para o Jupyter, exibindo
    de forma organizada e rastreável os resultados de:
    - aplicação do contrato (recorte e auditoria de colunas)
    - impacto estrutural (antes × depois)
    - diagnóstico categórico (candidatos, binários prováveis e frases de serviço)

    A função atua exclusivamente como camada de apresentação: ela não executa
    transformações semânticas, não aplica normalização e não realiza encoding.
    Todos os dados e relatórios devem ser produzidos previamente pelo core do
    pipeline (camada de features/diagnóstico) e entregues neste `payload`.

    Parâmetros
    ----------
    payload : dict
        Dicionário contendo os artefatos necessários para renderização do painel.
        Campos esperados:

        - df : pandas.DataFrame (obrigatório)
            DataFrame no estado pós-contrato (ou estado atual do pipeline), usado
            para exibição de colunas mantidas e para fallback de métricas quando
            snapshots não estiverem disponíveis.

        - contract : object | None (opcional)
            Objeto com metadados de conformidade ao contrato. A UI tenta ler,
            quando presentes:
            * kept_columns
            * dropped_columns
            * missing_contract_columns
            * snapshot_before
            * snapshot_after

        - candidates : object | None (opcional)
            Objeto com resultados do diagnóstico categórico. A UI tenta ler:
            * overview (dict com contagens agregadas)
            * top_candidates (pandas.DataFrame)
            * binary_candidates (pandas.DataFrame)
            * service_phrase_candidates (pandas.DataFrame)

        - scope : object | None (opcional)
            Estrutura de escopo semântico (ex.: NormalizationScope) contendo:
            * features (list[str])
            * target (str | None)
            Quando presente, o target é exibido na auditoria e excluído do
            diagnóstico categórico.

    Retorna
    -------
    None
        A função renderiza HTML diretamente no notebook via IPython.display.

    Exceções
    --------
    TypeError
        Se `payload` não for um dicionário.

    ValueError
        Se `payload["df"]` estiver ausente ou não for um pandas.DataFrame.

    Observações
    -----------
    - A função mantém compatibilidade com payloads parciais/antigos:
      quando `scope`, `contract` ou `candidates` não estão disponíveis,
      são aplicados fallbacks baseados no DataFrame atual e em estruturas vazias.
    - As métricas de impacto estrutural priorizam snapshots (quando fornecidos).
      Quando indisponíveis, utilizam valores calculados a partir de `df`.
    - "Total analisadas" refere-se a colunas analisadas (features), e não
      ao número de linhas do dataset. Blindagens são aplicadas para evitar
      inconsistências quando o payload traz valores inválidos.
    - Este renderer é destinado exclusivamente ao ambiente de notebook (Jupyter)
      e não deve ser utilizado em APIs/serviços.
    """
    from IPython.display import display, HTML
    import pandas as pd

    # -----------------------------
    # Validação básica
    # -----------------------------
    if not isinstance(payload, dict):
        raise TypeError("payload deve ser um dicionário.")

    df = payload.get("df")
    contract = payload.get("contract")
    candidates = payload.get("candidates")
    scope = payload.get("scope", None)

    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("payload['df'] inválido ou ausente.")

    # -----------------------------
    # Helpers
    # -----------------------------
    def _inject_styles():
        display(HTML("""
        <style>
          .ci-wrap { font-size:13px; line-height:1.35; }
          .ci-grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
          .ci-card {
            border:1px solid #e6e6e6; border-radius:10px;
            padding:10px 12px; margin:8px 0; background:#fff;
          }
          .ci-card h4 { margin:0 0 6px 0; font-size:14px; font-weight:700; }
          .ci-muted { color:#666; font-size:12px; }
          .ci-ok { color:#2e7d32; font-weight:600; }
          .ci-warn { color:#b26a00; font-weight:600; }

          .ci-chips { display:flex; flex-wrap:wrap; gap:6px; margin-top:6px; }
          .ci-chip {
            padding:3px 8px; border-radius:999px;
            border:1px solid #ededed; background:#fafafa;
            font-family: ui-monospace, monospace; font-size:12px;
          }

          table.ci-table {
            width:100%; border-collapse:collapse; font-size:12px;
          }
          table.ci-table th, table.ci-table td {
            padding:6px 8px; border-bottom:1px solid #f0f0f0;
            vertical-align:top;
          }
          table.ci-table th {
            background:#fbfbfb; font-weight:700; text-align:left;
          }

          .ci-delta-pos { color:#2e7d32; font-weight:600; }
          .ci-delta-neg { color:#b71c1c; font-weight:600; }

          @media (max-width:900px) {
            .ci-grid-2 { grid-template-columns:1fr; }
          }
        </style>
        """))

    def _chips(items):
        if not items:
            return "<span class='ci-muted'>—</span>"
        return "<div class='ci-chips'>" + "".join(
            f"<span class='ci-chip'>{i}</span>" for i in items
        ) + "</div>"

    def _chip_single(item):
        if item is None or item == "":
            return "<span class='ci-muted'>—</span>"
        return f"<div class='ci-chips'><span class='ci-chip'>{item}</span></div>"

    def _html_table(df_, max_rows=30):
        if df_ is None or df_.empty:
            return "<div class='ci-muted'>— sem dados —</div>"
        view = df_.head(max_rows).copy()

        def _cell(v):
            if isinstance(v, (list, tuple, set)):
                lst = list(v)
                return "[" + ", ".join(map(str, lst[:8])) + (", ..." if len(lst) > 8 else "") + "]"
            return v

        for c in view.columns:
            view[c] = view[c].map(_cell)

        return view.to_html(index=False, escape=True, classes="ci-table")

    def _safe(obj, attr, default=None):
        return getattr(obj, attr, default) if obj is not None else default

    # --------- FIX: leitura compatível com StructuralSnapshot (Seção 2)
    # StructuralSnapshot tem: n_rows, n_cols, memory_bytes e property memory_mb
    def _snap_rows(snap):
        if snap is None:
            return None
        v = getattr(snap, "rows", None)
        if v is None:
            v = getattr(snap, "n_rows", None)
        return int(v) if v is not None else None

    def _snap_cols(snap):
        if snap is None:
            return None
        v = getattr(snap, "cols", None)
        if v is None:
            v = getattr(snap, "n_cols", None)
        return int(v) if v is not None else None

    def _snap_mem_mb(snap):
        if snap is None:
            return None
        v = getattr(snap, "memory_mb", None)
        if v is not None:
            try:
                return float(v)
            except Exception:
                pass
        b = getattr(snap, "memory_bytes", None)
        if b is not None:
            try:
                return float(b) / (1024**2)
            except Exception:
                pass
        try:
            return float(str(v))
        except Exception:
            return None

    def _fmt_mb(v):
        try:
            return f"{float(v):.2f} MB"
        except Exception:
            return str(v)

    def _fmt_delta(v, unit=""):
        if v is None:
            return "—"
        try:
            vv = float(v)
            # Para memória: negativo é bom (reduziu) => verde
            cls = "ci-delta-pos" if vv < 0 else ("ci-delta-neg" if vv > 0 else "")
            return f"<span class='{cls}'>{vv:+.2f}{unit}</span>"
        except Exception:
            return "—"

    _inject_styles()

    # -----------------------------
    # Dados do payload
    # -----------------------------
    kept = _safe(contract, "kept_columns", list(df.columns)) or list(df.columns)
    missing = _safe(contract, "missing_contract_columns", []) or []
    dropped = _safe(contract, "dropped_columns", []) or []

    snap_before = _safe(contract, "snapshot_before", None)
    snap_after = _safe(contract, "snapshot_after", None)

    # Depois "real" (sempre confiável)
    df_after_rows = int(df.shape[0])
    df_after_cols = int(df.shape[1])
    df_after_mem = float(df.memory_usage(deep=True).sum() / (1024**2))

    # Antes/Depois (compatível com snapshot oficial)
    before_rows = _snap_rows(snap_before)
    before_cols = _snap_cols(snap_before)
    before_mem = _snap_mem_mb(snap_before)

    after_rows = _snap_rows(snap_after) or df_after_rows
    after_cols = _snap_cols(snap_after) or df_after_cols
    after_mem = _snap_mem_mb(snap_after) or df_after_mem

    # Δ
    delta_rows = (after_rows - before_rows) if before_rows is not None else None
    delta_cols = (after_cols - before_cols) if before_cols is not None else None
    delta_mem = (after_mem - before_mem) if before_mem is not None else None

    overview = _safe(candidates, "overview", {}) or {}
    top_df = _safe(candidates, "top_candidates", pd.DataFrame())
    bin_df = _safe(candidates, "binary_candidates", pd.DataFrame())
    srv_df = _safe(candidates, "service_phrase_candidates", pd.DataFrame())

    # -----------------------------
    # Scope (features/target) — compatível com payloads antigos
    # -----------------------------
    scope_target = getattr(scope, "target", None) if scope is not None else None
    scope_features = getattr(scope, "features", None) if scope is not None else None
    scope_features_count = len(scope_features) if isinstance(scope_features, list) else None

    # -----------------------------
    # Excluded columns (diagnóstico) — vindo do overview
    # -----------------------------
    excluded_cols = overview.get("excluded_columns", []) or []
    if not isinstance(excluded_cols, list):
        excluded_cols = [excluded_cols]
    excluded_clean = [str(c) for c in excluded_cols if c is not None and str(c).strip() != ""]

    # -----------------------------
    # Total analisadas (blindado: SEMPRE colunas, nunca linhas)
    # -----------------------------
    total_cols_raw = overview.get("total_columns", df.shape[1])
    try:
        total_cols = int(total_cols_raw)
    except Exception:
        total_cols = int(df.shape[1])

    df_cols = int(df.shape[1])
    # Blindagem: se vier algo "absurdo" (ex.: 7043), assume df.shape[1]
    if total_cols <= 0 or total_cols > df_cols:
        total_cols = df_cols

    # (Opcional) blindagem adicional: se tiver excluded, pode exibir também o total efetivo analisado:
    # total_effective = max(total_cols - len(excluded_clean), 0)

    # -----------------------------
    # Render
    # -----------------------------
    display(HTML("<div class='ci-wrap'>"))

    # Linha 1: Contrato + Impacto
    display(HTML(f"""
    <div class="ci-grid-2">

      <div class="ci-card">
        <h4> Conformidade ao Contrato de Entrada (API)</h4>
        <div><b>Colunas mantidas (contrato + target):</b> {len(kept)}</div>
        {_chips(kept)}
      </div>

      <div class="ci-card">
        <h4>Impacto Estrutural (antes × depois)</h4>
        <table class="ci-table">
          <thead><tr><th>Métrica</th><th>Antes</th><th>Depois</th><th>Δ</th></tr></thead>
          <tbody>
            <tr>
              <td>Linhas</td>
              <td>{before_rows if before_rows is not None else "<span class='ci-muted'>(indisponível)</span>"}</td>
              <td>{after_rows}</td>
              <td>{_fmt_delta(delta_rows, unit="")}</td>
            </tr>
            <tr>
              <td>Colunas</td>
              <td>{before_cols if before_cols is not None else "<span class='ci-muted'>(indisponível)</span>"}</td>
              <td>{after_cols}</td>
              <td>{_fmt_delta(delta_cols, unit="")}</td>
            </tr>
            <tr>
              <td>Memória</td>
              <td>{_fmt_mb(before_mem) if before_mem is not None else "<span class='ci-muted'>(indisponível)</span>"}</td>
              <td>{_fmt_mb(after_mem)}</td>
              <td>{_fmt_delta(delta_mem, unit=" MB")}</td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
    """))

    # Linha 2 — Auditoria + Descoberta (mesmo bloco HTML)
    # Atualização: incluir bloco Target (quando disponível) no card Auditoria
    target_block_html = ""
    if scope_target:
        target_block_html = f"""
        <div style="margin-bottom:8px;">
          <div><b>Target:</b></div>
          {_chip_single(scope_target)}
          <div class="ci-muted" style="margin-top:4px;">
            Mantido no dataset, porém <b>fora</b> do escopo de diagnóstico e padronização categórica desta etapa.

          </div>
          {"<div style='margin-top:6px;'><span style='font-size:15px;font-weight:700;'>Features do contrato:</span> <span style='font-size:15px;font-weight:700;'>" + str(scope_features_count) + "</span></div>" if scope_features_count is not None else ""}
          <div style="height:8px;"></div>
        </div>
        """

    excluded_block_html = ""
    if excluded_clean:
        excluded_block_html = f"""
        <div style="margin-top:8px;"><b>Excluídas do diagnóstico:</b> </div>
        {_chips(excluded_clean)}
        """

    display(HTML(f"""
    <div class="ci-grid-2">

      <div class="ci-card">
        <h4>Auditoria de Colunas</h4>

        {target_block_html}

        <div style="margin-top:8px;"><b>Colunas descartadas (fora do contrato):</b> {len(dropped)}</div>
        {_chips(dropped) if dropped else "<div class='ci-muted' style='margin-top:6px;'>Nenhuma descartada.</div>"}
      </div>

      <div class="ci-card">
        <h4>Descoberta de Candidatos</h4>
        <div class="ci-muted">Heurísticas de cardinalidade e padrões textuais</div>
        <div style="margin-top:6px;">
          <div><b>Total analisadas:</b> {total_cols}</div>
          <div><b>Candidatas:</b> {overview.get("suspected_columns", 0)}</div>
          <div><b>Prováveis binárias:</b> {overview.get("binary_candidates", 0)}</div>
          <div><b>Com frases de serviço:</b> {overview.get("service_phrase_columns", 0)}</div>
          {excluded_block_html}
        </div>
      </div>

    </div>
    """))

    # Tabelas
    display(HTML(f"""
    <div class="ci-card">
      <h4>Top candidatos</h4>
      {_html_table(top_df)}
    </div>

    <div class="ci-card">
      <h4>Provavelmente binárias (Yes/No ou 0/1)</h4>
      {_html_table(bin_df)}
    </div>

    <div class="ci-card">
      <h4>Frases de serviço detectadas</h4>
      <div class="ci-muted">Ex.: "No internet service" → "No"</div>
      {_html_table(srv_df)}
    </div>

    <div class="ci-card">
      <h4>ℹ️ Nota</h4>
      <b>Diagnóstico apenas.</b> Nenhuma padronização foi aplicada nesta etapa.
      A próxima célula deve declarar explicitamente as regras e executar a normalização.
    </div>
    """))

    display(HTML("</div>"))


def render_categorical_standardization_report(
    payload: dict,
    title: str = "Padronização Categórica (Execução)",
    theme: UITheme = DEFAULT_THEME,
) -> None:
    """
    Renderiza o painel visual da **Seção 3 — Parte 2** do pipeline (N1),
    correspondente à **execução auditável da padronização categórica**.

    Esta função é estritamente de **apresentação (UI)**:
    não executa regras de padronização, não altera dados e não infere decisões.
    Seu papel é **expor de forma explícita, rastreável e verificável** o que foi
    executado pelo core na etapa de padronização categórica.

    Filosofia de design (padrão do pipeline):
    - UI é passiva: apenas consome e apresenta artefatos
    - Cards conceituais numerados e documentáveis
    - Tolerância a payload parcial, com fallbacks seguros
    - Nenhuma lógica crítica de dados reside na UI

    Estrutura conceitual renderizada (mapeamento para documentação):
    - **S3.8**  → Decisão explícita  
      Regras e colunas definidas a partir do diagnóstico categórico.
    - **S3.9**  → Resumo da execução  
      Quantidade de células alteradas, garantias explícitas (sem encoding, target intacto).
    - **S3.10** → Impacto estrutural (Antes × Depois)  
      Auditoria técnica de linhas, colunas e uso de memória.
    - **S3.11** → Regras aplicadas  
      Tabela das substituições efetivamente utilizadas.
    - **S3.12** → Relatório de mudanças  
      Auditoria por coluna com exemplos das alterações realizadas.

    Parâmetros
    ----------
    payload : dict
        Payload consolidado produzido pelo core de padronização categórica.
        Espera conter, quando disponíveis:
        - impact_df : pandas.DataFrame
        - changes_df : pandas.DataFrame
        - rules_df : pandas.DataFrame
        - meta : dict (ex.: colunas consideradas, células alteradas)
        - decision : dict (ex.: phrase_map, cols_scope)

        O renderer é tolerante a payload incompleto e aplica placeholders quando necessário.

    title : str, opcional
        Título exibido no painel principal da UI. Não interfere na lógica de renderização.

    theme : UITheme, opcional
        Tema visual utilizado na renderização (cores, classes CSS).
        Mantém compatibilidade com o padrão visual das demais seções.

    Retorno
    -------
    None
        A função apenas renderiza HTML no notebook via IPython.display,
        não retornando valores nem alterando o estado do pipeline.

    Notas
    -----
    - Nenhum encoding é aplicado nesta etapa.
    - O target é explicitamente preservado.
    - Toda decisão exibida deve ter sido previamente tomada no core.
    - A UI atua como trilha de auditoria visual da execução.
    """
    from IPython.display import display, HTML
    import pandas as pd

    # -----------------------------
    # Validação básica
    # -----------------------------
    if not isinstance(payload, dict):
        raise TypeError("payload deve ser um dicionário.")

    impact_df = payload.get("impact_df", pd.DataFrame())
    changes_df = payload.get("changes_df", pd.DataFrame())
    rules_df = payload.get("rules_df", pd.DataFrame())
    meta = payload.get("meta", {}) or {}
    decision = payload.get("decision", {}) or {}

    # -----------------------------
    # Preparações (texto/contagens)
    # -----------------------------
    cols_considered = meta.get("scoped_cols_considered", []) or []
    total_cells_changed = int(meta.get("total_cells_changed", 0) or 0)

    phrase_map = decision.get("phrase_map", {}) or {}
    cols_scope = decision.get("cols_scope", []) or []

    # tabelas (padrão S2)
    impact_table = (
        _df_to_html_table(impact_df, max_rows=6)
        if impact_df is not None and not impact_df.empty
        else "<div class='ci-muted'>—</div>"
    )

    rules_table = (
        _df_to_html_table(rules_df, max_rows=12)
        if rules_df is not None and not rules_df.empty
        else "<div class='ci-muted'>Nenhuma regra aplicada.</div>"
    )

    changes_table = (
        _df_to_html_table(changes_df, max_rows=20)
        if changes_df is not None and not changes_df.empty
        else "<div class='ci-muted'>Nenhuma mudança registrada.</div>"
    )

    # decisão como string legível
    if phrase_map:
        # mostra até 4 pares pra não virar parede de texto
        items = list(phrase_map.items())
        head = items[:4]
        rules_preview = "; ".join([f"{k} → {v}" for k, v in head])
        if len(items) > 4:
            rules_preview += f" … (+{len(items) - 4} regras)"
    else:
        EMPTY_TXT = "Não aplicável (sem colunas textuais)"
        rules_preview = EMPTY_TXT

    cols_scope_txt = ", ".join([str(c) for c in cols_scope]) if cols_scope else EMPTY_TXT
    cols_considered_txt = ", ".join([str(c) for c in cols_considered]) if cols_considered else EMPTY_TXT

    # -----------------------------
    # Render (padrão ci-panel)
    # -----------------------------
    html = f"""
    <div class="ci-panel">
      <div class="ci-header">
        <div>
          <p class="ci-sub">
            Execução de padronização categórica derivada do diagnóstico (Seção 3),
            sem encoding e sem alterações fora do escopo do contrato.
          </p>
        </div>
      </div>

      <!-- Grid 1×2 -->
      <div class="ci-grid">

        <!-- S3.8 — Decisão explícita -->
        <div class="ci-card">
          <h4>Decisão explícita (derivada do diagnóstico)</h4>
          <div><b>Colunas sinalizadas no diagnóstico:</b> {cols_scope_txt}</div>
          <div style="margin-top:6px;"><b>Colunas consideradas (escopo final):</b> {cols_considered_txt}</div>
          <div style="margin-top:6px;"><b>Regras declaradas:</b> {len(phrase_map)}</div>
          <div class="ci-muted" style="margin-top:6px;">
            {rules_preview}
          </div>
        </div>

        <!-- S3.9 — Resumo da execução -->
        <div class="ci-card">
          <h4>Resumo da execução</h4>
          <div><b>Células alteradas:</b> {total_cells_changed}</div>
          <div style="margin-top:6px;"><b>Encoding:</b> não aplicado</div>
          <div style="margin-top:6px;"><b>Target:</b> não alterado</div>
          <div class="ci-muted" style="margin-top:8px;">
            Esta célula inaugura a fase ativa de pré-processamento,
            porém ainda limitada à padronização textual mínima.
          </div>
        </div>

      </div>

      <!-- S3.10 — Impacto estrutural -->
      <div class="ci-card">
        <h4>Impacto estrutural (Antes × Depois)</h4>
        {impact_table}
      </div>

      <!-- S3.11 — Regras aplicadas -->
      <div class="ci-card">
        <h4>Regras aplicadas</h4>
        {rules_table}
      </div>

      <!-- S3.12 — Relatório de mudanças -->
      <div class="ci-card">
        <h4>Relatório de mudanças (auditável)</h4>
        {changes_table}
        <div class="ci-sub" style="margin-top:8px;">
          O relatório descreve: coluna afetada, tipo de regra, volume de alterações e exemplos (quando disponíveis).
        </div>
      </div>
      </div>
    </div>
    """

    display(HTML(html))


# ============================================================
# Seção 3.3 — Auditoria do Target (UI)
# ============================================================
def render_target_audit_report(
    payload: dict,
    title: str = "Auditoria do Target",
    theme=None,
):
    """
    Renderiza a Seção 3.3 — Auditoria do Target em HTML (notebook-friendly).

    Exibe:
    - Um resumo compacto (target, linhas, valores únicos, nulos, inválidos, domínio esperado/observado)
    - Uma tabela auditável com distribuição (audit_df)

    Espera payload (tolerante):
    - target: str
    - audit_df: DataFrame (distribuição / inconsistências)
    - meta: dict (contagens e flags)
    - scope: dict/obj (opcional)
    """
    import pandas as pd

    # -------------------------
    # Helpers
    # -------------------------
    def _safe_html(x):
        s = "" if x is None else str(x)
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    # label em negrito, valor normal
    def _kv(k, v):
        return f"""
        <div>
          <div class="ci-k"><b>{_safe_html(k)}</b></div>
          <div class="ci-v">{_safe_html(v)}</div>
        </div>
        """

    def _card(title_txt, body_html):
        return f"""
        <div class="ci-card">
          <div class="ci-card-title">{_safe_html(title_txt)}</div>
          <div class="ci-card-body">{body_html}</div>
        </div>
        """

    def _df_to_html_table(df: pd.DataFrame, max_rows=50):
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return "<span class='ci-muted'>—</span>"
        return df.head(max_rows).to_html(index=False, escape=True, classes="ci-table")

    # -------------------------
    # Theme fallback
    # -------------------------
    class _ThemeFallback:
        border_soft = "#e8edf3"
        text = "#111827"
        muted = "#6b7280"
        bg = "#ffffff"
        bg_soft = "#f8fafc"
        ok = "#16a34a"

    theme = theme or _ThemeFallback()

    # -------------------------
    # Payload
    # -------------------------
    meta = payload.get("meta") or {}
    executed = bool(meta.get("executed", True))

    target = payload.get("target")
    audit_df = payload.get("audit_df")

    reason = meta.get("reason")
    n_rows = meta.get("n_rows", meta.get("rows", "—"))
    n_unique = meta.get("n_unique", meta.get("unique", "—"))
    missing = meta.get("missing", meta.get("missing_count", "—"))
    invalid = meta.get("invalid", meta.get("invalid_count", "—"))

    expected_values = meta.get("expected_values", None)
    observed_values = meta.get("observed_values", None)

    badge = (
        f"<span class='ci-badge ok'><b>Executado</b></span>"
        if executed
        else f"<span class='ci-badge muted'><b>Não executado</b></span>"
    )

    # -------------------------
    # Bloco resumo (compacto)
    # -------------------------
    expected_txt = "—" if not expected_values else ", ".join(map(str, expected_values))
    observed_txt = "—" if not observed_values else ", ".join(map(str, observed_values))

    s331 = f"""
    <div class="ci-note ci-note-tight">
      Diagnóstico do target <b>{_safe_html(target) if target else "—"}</b>.
      Esta etapa não transforma valores — apenas audita consistência (domínio, nulos e inválidos).
    </div>

    <div class="ci-kvwrap ci-kvwrap-compact">
      {_kv("Target", target if target is not None else "—")}
      {_kv("Linhas", n_rows)}
      {_kv("Valores únicos", n_unique)}
      {_kv("Nulos no target", missing)}
      {_kv("Inválidos (fora do domínio)", invalid)}
      {_kv("Domínio esperado", expected_txt)}
      {_kv("Valores observados", observed_txt)}
    </div>
    """

    if not executed and reason:
        s331 += f"<div class='ci-note ci-note-tight'><b>Motivo:</b> {_safe_html(reason)}</div>"

    # -------------------------
    # Tabela auditável
    # -------------------------
    s332 = _df_to_html_table(audit_df, max_rows=50)

    # -------------------------
    # CSS (mesmo padrão de cards) + compactação
    # -------------------------
    css = f"""
    <style>
      .ci-wrap {{
        font-family: Arial, sans-serif;
        color: {theme.text};
      }}

      .ci-header {{
        display:flex;
        align-items:flex-start;
        justify-content:space-between;
        gap:12px;
        margin-bottom:10px;
      }}

      .ci-title {{
        font-size:18px;
        font-weight:900;
        margin:0;
      }}

      .ci-badge {{
        border: 1px solid {theme.border_soft};
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 12px;
        font-weight: 700;
        color: {theme.muted};
        background: {theme.bg_soft};
        white-space: nowrap;
      }}
      .ci-badge.ok {{
        color: {theme.ok};
        border-color: {theme.ok};
        background: #ecfdf5;
      }}
      .ci-badge.muted {{
        color: {theme.muted};
      }}

      .ci-card {{
        border:1px solid {theme.border_soft};
        border-radius:14px;
        padding:16px;
        background:#fff;
        margin-bottom:16px;
      }}

      .ci-card-title {{
        font-size:18px;
        font-weight:900;
        margin-bottom:8px;
      }}

      .ci-card-body {{
        font-size:13px;
      }}

      .ci-note {{
        color:{theme.muted};
        font-size:13px;
        margin-bottom:10px;
        line-height:1.35;
      }}
      .ci-note-tight {{
        margin-bottom:8px;
        line-height:1.25;
      }}

      .ci-k {{
        font-size:12px;
        color:{theme.muted};
        margin-bottom:2px;
      }}

      .ci-v {{
        font-size:13px;
        overflow-wrap:anywhere;
      }}

      .ci-kvwrap {{
        display:grid;
        gap:10px;
      }}

      /* ✅ resumo mais comprimido: 3 colunas (desktop), 2 (tablet), 1 (mobile) */
      .ci-kvwrap-compact {{
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 8px 12px;
      }}
      @media (max-width: 900px) {{
        .ci-kvwrap-compact {{
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }}
      }}
      @media (max-width: 600px) {{
        .ci-kvwrap-compact {{
          grid-template-columns: 1fr;
        }}
      }}

      table.ci-table {{
        width:100%;
        border-collapse:collapse;
      }}
      table.ci-table th, table.ci-table td {{
        padding:8px;
        border-top:1px solid {theme.border_soft};
        font-size:13px;
        vertical-align:top;
      }}
      table.ci-table th {{
        color:{theme.muted};
        font-weight:800;
      }}

      .ci-muted {{
        color:{theme.muted};
      }}
    </style>
    """

    html = f"""
    {css}
    <div class="ci-wrap">
      <div class="ci-header">

      </div>

      {_card("Resumo do target", s331)}
      {_card("Tabela auditável", s332)}
    </div>
    """

    try:
        from IPython.display import HTML  # type: ignore
        return HTML(html)
    except Exception:
        return html


# ============================================================
# Seção 4 — Tratamento de Dados Faltantes
# ============================================================
def render_missing_imputation_report(
    payload: dict,
    title: str = "Tratamento de Dados Faltantes (Execução)",
    theme=None
):
    """
    Renderiza a **Seção 4 — Tratamento de Dados Faltantes** do pipeline em formato HTML,
    com foco em **clareza narrativa, auditabilidade e uso em notebooks**.

    A função transforma o estado resultante da etapa de imputação em uma visualização
    estruturada, seguindo explicitamente o fluxo conceitual do projeto:

        decisão explícita → execução → auditoria

    O relatório é dividido em cards independentes, cada um com propósito bem definido:

    - **Decisão explícita de imputação**  
      Exibe as estratégias declaradas no notebook (numéricas e categóricas), bem como
      a intenção de escopo (include/exclude) e o target preservado.

    - **Resumo da execução**  
      Apresenta métricas agregadas da etapa (células imputadas, colunas afetadas,
      número de features e preservação do target).

    - **Impacto estrutural (Antes × Depois)**  
      Mostra auditoria de shape e consumo de memória, garantindo que a imputação
      não alterou linhas ou colunas.

    - **Estratégias aplicadas**  
      Tabela-resumo por coluna, indicando tipo, estratégia utilizada e valor aplicado.

    - **Relatório de imputação (auditável)**  
      Visualização detalhada por coluna, organizada em blocos, contendo:
        • tipo e dtype  
        • estratégia aplicada  
        • valor utilizado  
        • faltantes antes/depois  
        • volume imputado e percentual  

      As colunas são ordenadas de forma “inteligente”, priorizando:
        1) colunas com imputação efetiva  
        2) colunas com faltantes detectados  
        3) ordenação alfabética  

    Características importantes:
    - **Notebook-friendly**: retorna `IPython.display.HTML` quando disponível.
    - **Tolerante ao payload**: aceita `scope` como dict ou objeto.
    - **UI em PT-BR**: rótulos amigáveis sem alterar nomes internos do DataFrame.
    - **Auditável por design**: nenhuma transformação é silenciosa ou implícita.
    - **Somente visualização**: não modifica dados nem executa imputação.

    Parâmetros
    ----------
    payload : dict
        Dicionário gerado pela etapa de imputação, contendo (de forma tolerante):
        - decision : dict
        - meta : dict
        - scope : dict ou objeto com atributos `features` e `target`
        - impact_df : pandas.DataFrame
        - changes_df : pandas.DataFrame

    title : str, opcional
        Título principal da seção (usado apenas para exibição).

    theme : objeto opcional
        Tema visual com atributos de cores e estilos. Caso não informado,
        um tema padrão é aplicado automaticamente.

    Retorno
    -------
    IPython.display.HTML ou str
        HTML renderizado do relatório, pronto para exibição em notebook
        ou para uso em outros contextos de visualização.
    """
    import pandas as pd

    # -------------------------
    # Labels PT-BR (UI apenas)
    # -------------------------
    UI_LABELS_PT = {
        "fill_value": "Valor aplicado",
        "missing_before": "Faltantes (antes)",
        "missing_after": "Faltantes (depois)",
        "imputed": "Imputados",
        "pct_imputed": "% imputado",
        "dtype": "Tipo (dtype)",
        "strategy": "Estratégia",
        "kind": "Tipo (coluna)",
    }

    # -------------------------
    # Helpers
    # -------------------------
    def _safe_html(x):
        s = "" if x is None else str(x)
        return (
            s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&#39;")
        )

    def _label(k):
        return UI_LABELS_PT.get(k, k)

    # label em negrito, valor normal
    def _kv(k, v):
        return f"""
        <div>
          <div class="ci-k"><b>{_safe_html(k)}</b></div>
          <div class="ci-v">{_safe_html(v)}</div>
        </div>
        """

    def _card(title_txt, body_html):
        return f"""
        <div class="ci-card">
          <div class="ci-card-title">{_safe_html(title_txt)}</div>
          <div class="ci-card-body">{body_html}</div>
        </div>
        """

    def _df_to_html_table(df: pd.DataFrame, max_rows=50):
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return "<span class='ci-muted'>—</span>"
        return df.head(max_rows).to_html(index=False, escape=True, classes="ci-table")

    def _to_num(v):
        try:
            if pd.isna(v):
                return 0.0
            return float(v)
        except Exception:
            return 0.0

    # -------------------------
    # Theme fallback
    # -------------------------
    class _ThemeFallback:
        border_soft = "#e8edf3"
        text = "#111827"
        muted = "#6b7280"
        bg = "#ffffff"
        bg_soft = "#f8fafc"
        ok = "#16a34a"

    theme = theme or _ThemeFallback()

    # -------------------------
    # Payload
    # -------------------------
    decision = payload.get("decision", {})
    meta = payload.get("meta", {})
    scope = payload.get("scope")
    impact_df = payload.get("impact_df")
    changes_df = payload.get("changes_df")

    # scope tolerante
    if isinstance(scope, dict):
        features = scope.get("features", [])
        target = scope.get("target")
    else:
        features = getattr(scope, "features", [])
        target = getattr(scope, "target", None)

    total_imputed = meta.get("total_imputed", 0)
    cols_affected = meta.get("cols_affected", 0)
    n_features = meta.get("n_features", len(features))
    target_preserved = meta.get("target_preserved", True)

    # -------------------------
    # S4.1 — Decisão explícita
    # -------------------------
    s41 = f"""
    <div class="ci-note">
      A decisão exibida aqui deve ter sido declarada no notebook
      (sem defaults ocultos no core).
    </div>
    <div class="ci-kvwrap">
      {_kv("numeric_strategy", decision.get("numeric_strategy", "-"))}
      {_kv("categorical_strategy", decision.get("categorical_strategy", "-"))}
      {_kv("include_cols (intenção)", "(todas as features)")}
      {_kv("exclude_cols (declaração)", "—")}
    </div>
    <div class="ci-subtitle"><b>target</b></div>
    <div>{_safe_html(target)} <span class="ci-muted">(não imputado automaticamente)</span></div>
    """

    # -------------------------
    # S4.2 — Resumo
    # -------------------------
    s42 = f"""
    <div class="ci-kvwrap">
      {_kv("Células imputadas", total_imputed)}
      {_kv("Colunas afetadas", cols_affected)}
      {_kv("Features (contrato)", n_features)}
      {_kv("Target preservado", "Sim" if target_preserved else "Não")}
    </div>
    """

    # -------------------------
    # S4.3 / S4.4
    # -------------------------
    s43 = _df_to_html_table(impact_df, 20)
    s44 = _df_to_html_table(
        changes_df[["column", "kind", "strategy", "fill_value_used"]]
        if isinstance(changes_df, pd.DataFrame) else None
    )

    # -------------------------
    # S4.5 — Relatório auditável
    # -------------------------
    blocks = []
    if isinstance(changes_df, pd.DataFrame):
        df = changes_df.copy()
        df["_imp"] = df["imputed"].apply(_to_num)
        df["_miss"] = df["missing_before"].apply(_to_num)

        df = df.sort_values(
            by=["_imp", "_miss", "column"],
            ascending=[False, False, True]
        )

        for _, r in df.iterrows():
            blocks.append(f"""
            <div class="ci-colblock">
              <div class="ci-coltitle">
                <span><b>{_safe_html(r['column'])}</b></span>
                <span class="ci-muted">{_safe_html(r['kind'])}</span>
              </div>

              <div class="ci-colmeta">
                <b>{_label("dtype")}</b>: {_safe_html(r['dtype'])}
                · <b>{_label("strategy")}</b>: {_safe_html(r['strategy'])}
              </div>

              <div class="ci-kvgrid">
                {_kv(_label("fill_value"), r["fill_value_used"])}
                {_kv(_label("missing_before"), r["missing_before"])}
                {_kv(_label("missing_after"), r["missing_after"])}
                {_kv(_label("imputed"), r["imputed"])}
                {_kv(_label("pct_imputed"), r["pct_imputed"])}
              </div>
            </div>
            """)

    report = f"<div class='ci-blockgrid'>{''.join(blocks)}</div>"

    # -------------------------
    # CSS (completo e estável)
    # -------------------------
    css = f"""
    <style>
      .ci-wrap {{
        font-family: Arial, sans-serif;
        color: {theme.text};
      }}

      .ci-grid-2 {{
        display:grid;
        grid-template-columns:1fr 1fr;
        gap:16px;
      }}
      @media (max-width:900px) {{
        .ci-grid-2 {{ grid-template-columns:1fr; }}
      }}

      .ci-card {{
        border:1px solid {theme.border_soft};
        border-radius:14px;
        padding:16px;
        background:#fff;
        margin-bottom:16px;
      }}

      .ci-card-title {{
        font-size:18px;
        font-weight:900;
        margin-bottom:8px;
      }}

      .ci-note {{
        color:{theme.muted};
        font-size:13px;
        margin-bottom:10px;
      }}

      .ci-k {{
        font-size:12px;
        color:{theme.muted};
      }}

      .ci-v {{
        font-size:14px;
        overflow-wrap:anywhere;
      }}

      .ci-kvwrap {{
        display:grid;
        gap:10px;
      }}

      .ci-subtitle {{
        margin-top:12px;
        margin-bottom:6px;
        font-size:13px;
        color:{theme.muted};
      }}

      table.ci-table {{
        width:100%;
        border-collapse:collapse;
      }}
      table.ci-table th, table.ci-table td {{
        padding:8px;
        border-top:1px solid {theme.border_soft};
        font-size:13px;
      }}

      .ci-blockgrid {{
        display:grid;
        grid-template-columns:repeat(2,minmax(0,1fr));
        gap:16px;
      }}
      @media (max-width:900px) {{
        .ci-blockgrid {{ grid-template-columns:1fr; }}
      }}

      .ci-colblock {{
        border:1px solid {theme.border_soft};
        border-radius:12px;
        padding:16px;
        background:#fff;
      }}

      .ci-coltitle {{
        display:flex;
        justify-content:space-between;
        margin-bottom:6px;
      }}

      .ci-colmeta {{
        border-bottom:1px dashed {theme.border_soft};
        padding-bottom:8px;
        margin-bottom:12px;
        font-size:12px;
        color:{theme.muted};
      }}

      .ci-kvgrid {{
        display:grid;
        grid-template-columns:1fr 1fr;
        gap:10px 14px;
      }}
      @media (max-width:700px) {{
        .ci-kvgrid {{ grid-template-columns:1fr; }}
      }}
    </style>
    """

    html = f"""
    {css}
    <div class="ci-wrap">
      <div class="ci-grid-2">
        {_card("Decisão explícita de imputação", s41)}
        {_card("Resumo da execução", s42)}
      </div>

      {_card("Impacto estrutural (Antes × Depois)", s43)}
      {_card("Estratégias aplicadas", s44)}
      {_card("Relatório de imputação (auditável)", report)}
    </div>
    """

    try:
        from IPython.display import HTML
        return HTML(html)
    except Exception:
        return html


# ============================================================
# Seção 5 — Preparação para Modelagem (UI)
# ============================================================
def render_modeling_report(payload: dict, title: str = "Seção 5 — Preparação para Modelagem (Split + Auditoria)"):
    """
    Renderer UI-only para a Seção 5 (Split treino/teste e auditoria).

    IMPORTANTE
    ----------
    Apesar do nome histórico `render_modeling_report`, esta função foi ajustada
    para consumir o payload produzido pela função core da Seção 5:
        `run_train_test_split(...)`

    Este renderer:
    - ❌ não treina modelos
    - ❌ não faz encoding/scaling
    - ❌ não transforma o target
    - ✔️ apenas apresenta a decisão explícita e os diagnósticos auditáveis pós-split

    Payload esperado (Seção 5)
    --------------------------
    - decision: dict
        - test_size, random_state, shuffle, stratify, stratify_col (quando aplicável)
        - audit_categorical_cardinality (opcional)
    - split: dict
        - X_train, X_test, y_train, y_test
    - diagnostics: dict
        - shapes: dict
        - target_distribution: pd.DataFrame
        - risk_checks: dict
        - categorical_cardinality: pd.DataFrame (opcional)
    """
    import pandas as pd

    if not isinstance(payload, dict):
        raise TypeError("payload deve ser um dicionário.")

    decision = payload.get("decision", {}) or {}
    split = payload.get("split", {}) or {}
    diagnostics = payload.get("diagnostics", {}) or {}

    shapes = diagnostics.get("shapes", {}) or {}
    target_distribution = diagnostics.get("target_distribution", None)
    risk_checks = diagnostics.get("risk_checks", {}) or {}
    categorical_cardinality = diagnostics.get("categorical_cardinality", None)

    # -------------------------
    # Helpers (HTML)
    # -------------------------
    def _safe(x) -> str:
        s = "" if x is None else str(x)
        return (
            s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&#39;")
        )

    def _card(title_txt: str, body_html: str) -> str:
        # ✅ Renderiza o título do card (padrão visual/narrativo do notebook)
        return f"""
        <div class="ci-card">
          <div class="ci-card-title">{_safe(title_txt)}</div>
          <div class="ci-card-body">{body_html}</div>
        </div>
        """

    def _df_table(df: pd.DataFrame, max_rows: int = 60) -> str:
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return "<span class='ci-muted'>—</span>"
        return df.head(max_rows).to_html(index=False, escape=True, classes="ci-table")

    def _kv(k: str, v) -> str:
        return f"""
        <div>
          <div class="ci-k"><b>{_safe(k)}</b></div>
          <div class="ci-v">{_safe(v)}</div>
        </div>
        """

    def _shape_str(obj) -> str:
        if obj is None:
            return "—"
        if isinstance(obj, dict):
            if "rows" in obj and "cols" in obj:
                return f"{obj['rows']} × {obj['cols']}"
            if "rows" in obj and "cols" not in obj:
                return f"{obj['rows']}"
        return _safe(obj)

    # -------------------------
    # Extrai shapes de forma tolerante
    # -------------------------
    X_train = split.get("X_train", None)
    X_test = split.get("X_test", None)
    y_train = split.get("y_train", None)
    y_test = split.get("y_test", None)

    X_train_shape = shapes.get("X_train")
    X_test_shape = shapes.get("X_test")
    y_train_shape = shapes.get("y_train")
    y_test_shape = shapes.get("y_test")

    if X_train_shape is None and hasattr(X_train, "shape"):
        X_train_shape = {"rows": int(X_train.shape[0]), "cols": int(X_train.shape[1])}
    if X_test_shape is None and hasattr(X_test, "shape"):
        X_test_shape = {"rows": int(X_test.shape[0]), "cols": int(X_test.shape[1])}
    if y_train_shape is None and hasattr(y_train, "shape"):
        y_train_shape = {"rows": int(y_train.shape[0])}
    if y_test_shape is None and hasattr(y_test, "shape"):
        y_test_shape = {"rows": int(y_test.shape[0])}

    # -------------------------
    # [S5.1] Card — Decisão Explícita do Split
    # -------------------------
    stratify = decision.get("stratify", "—")
    stratify_col = decision.get("stratify_col", "—")

    decision_html = f"""
    <div class="ci-note">
      Esta decisão deve ter sido declarada explicitamente no notebook. Nenhum parâmetro é inferido pela UI.
    </div>
    <div class="ci-kvwrap ci-kvwrap-compact">
      {_kv("test_size", decision.get("test_size", "—"))}
      {_kv("random_state", decision.get("random_state", "—"))}
      {_kv("shuffle", decision.get("shuffle", "—"))}
      {_kv("stratify", stratify)}
      {_kv("stratify_col", stratify_col if stratify is True else "—")}
      {_kv("audit_categorical_cardinality", decision.get("audit_categorical_cardinality", False))}
    </div>
    """

    # -------------------------
    # [S5.2] Card — Shapes de Treino e Teste
    # -------------------------
    shapes_html = f"""
    <div class="ci-kvwrap ci-kvwrap-compact">
      {_kv("X_train", _shape_str(X_train_shape))}
      {_kv("X_test", _shape_str(X_test_shape))}
      {_kv("y_train", _shape_str(y_train_shape))}
      {_kv("y_test", _shape_str(y_test_shape))}
      {_kv("n_features", shapes.get("n_features", "—"))}
    </div>
    """

    # -------------------------
    # [S5.3] Card — Distribuição do Target (Pré vs Pós-Split)
    # -------------------------
    target_html = _df_table(target_distribution, max_rows=30)

    # -------------------------
    # [S5.4] Card — Diagnóstico de Riscos Estruturais
    # -------------------------
    scope_integrity = (risk_checks.get("scope_integrity", {}) or {}) if isinstance(risk_checks, dict) else {}
    target_balance = (risk_checks.get("target_balance", {}) or {}) if isinstance(risk_checks, dict) else {}

    risks_html = f"""
    <div class="ci-note">
      Diagnóstico objetivo (sem ações automáticas). Este painel apenas expõe sinais.
    </div>

    <div class="ci-subtitle"><b>Integridade do escopo</b></div>
    <div class="ci-kvwrap ci-kvwrap-compact">
      {_kv("target_in_X_train", scope_integrity.get("target_in_X_train", "—"))}
      {_kv("target_in_X_test", scope_integrity.get("target_in_X_test", "—"))}
      {_kv("columns_match_scope_train", scope_integrity.get("columns_match_scope_train", "—"))}
      {_kv("columns_match_scope_test", scope_integrity.get("columns_match_scope_test", "—"))}
    </div>

    <div class="ci-subtitle"><b>Distribuição mínima do target</b></div>
    <div class="ci-kvwrap ci-kvwrap-compact">
      {_kv("min_class_rate_all", target_balance.get("min_class_rate_all", "—"))}
      {_kv("min_class_rate_train", target_balance.get("min_class_rate_train", "—"))}
      {_kv("min_class_rate_test", target_balance.get("min_class_rate_test", "—"))}
    </div>
    """

    # -------------------------
    # [S5.5] Card — Cardinalidade Categórica Pós-Split (Opcional)
    # -------------------------
    cat_html = _df_table(categorical_cardinality, max_rows=60)

    # -------------------------
    # CSS (similar ao padrão)
    # -------------------------
    css = """
    <style>
      .ci-wrap { font-family: Arial, sans-serif; color: #111827; }

      .ci-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
      @media (max-width:900px) { .ci-grid-2 { grid-template-columns: 1fr; } }

      .ci-card { border: 1px solid #e8edf3; border-radius: 14px; padding: 16px; background: #fff; margin-bottom: 16px; }
      .ci-card-title { font-size: 18px; font-weight: 900; margin-bottom: 8px; }
      .ci-card-body { font-size: 13px; }

      .ci-note { color: #6b7280; font-size: 13px; margin-bottom: 10px; line-height: 1.35; }
      .ci-subtitle { margin-top: 10px; margin-bottom: 6px; font-size: 13px; color: #6b7280; }

      .ci-k { font-size: 12px; color: #6b7280; }
      .ci-v { font-size: 14px; overflow-wrap: anywhere; }

      .ci-kvwrap { display: grid; gap: 10px; }
      .ci-kvwrap-compact { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px 12px; }
      @media (max-width: 900px) { .ci-kvwrap-compact { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
      @media (max-width: 600px) { .ci-kvwrap-compact { grid-template-columns: 1fr; } }

      table.ci-table { width: 100%; border-collapse: collapse; }
      table.ci-table th, table.ci-table td { padding: 8px; border-top: 1px solid #e8edf3; font-size: 13px; vertical-align: top; }
      table.ci-table th { color: #6b7280; font-weight: 800; background: #fbfbfb; }

      .ci-muted { color: #6b7280; }
      .ci-mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
      .ci-ul { margin: 8px 0 0 18px; }
    </style>
    """

    # Card “capa” opcional (se você quiser manter o title global)
    header_html = f"""
    <div class="ci-note">
      Esta seção é estritamente diagnóstica/estrutural. Nenhuma decisão de modelagem é tomada aqui.
    </div>
    """

    html = f"""
    {css}
    <div class="ci-wrap">
      <div class="ci-grid-2">
        {_card("Decisão Explícita do Split", decision_html)}
        {_card("Shapes de Treino e Teste", shapes_html)}
      </div>
      {_card("Distribuição do Target (Pré vs Pós-Split)", target_html)}
      {_card("Diagnóstico de Riscos Estruturais", risks_html)}
      {_card("Cardinalidade Categórica Pós-Split", cat_html)}
    </div>
    """

    try:
        from IPython.display import HTML
        return HTML(html)
    except Exception:
        return html

# ============================================================
# Seção 6 — Representação para Modelagem Supervisionada (UI)
# ============================================================
def render_supervised_representation_report(
    payload: dict,
    title: str = "Seção 6 — Representação para Modelagem Supervisionada",
):
    """
    Renderer UI-only para a Seção 6 do pipeline principal (N1):
    Representação para Modelagem Supervisionada.

    IMPORTANTE
    ----------
    Esta função é estritamente de apresentação:
    - ❌ não treina modelos
    - ❌ não compara algoritmos
    - ❌ não define métricas finais
    - ✔️ apenas expõe decisão explícita + auditorias pós-representação

    Payload esperado (Seção 6)
    --------------------------
    - decision: dict
    - representation: dict
    - diagnostics: dict
    """
    import pandas as pd

    if not isinstance(payload, dict):
        raise TypeError("payload deve ser um dicionário.")

    decision = payload.get("decision", {}) or {}
    representation = payload.get("representation", {}) or {}
    diagnostics = payload.get("diagnostics", {}) or {}

    def _safe(x) -> str:
        s = "" if x is None else str(x)
        return (
            s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&#39;")
        )

    def _card(title_txt: str, body_html: str) -> str:
        return f"""
        <div class="ci-card">
          <div class="ci-card-title">{_safe(title_txt)}</div>
          <div class="ci-card-body">{body_html}</div>
        </div>
        """

    def _kv(k: str, v) -> str:
        return f"""
        <div>
          <div class="ci-k"><b>{_safe(k)}</b></div>
          <div class="ci-v">{_safe(v)}</div>
        </div>
        """

    def _shape_str(obj) -> str:
        if obj is None:
            return "—"
        if isinstance(obj, dict):
            if "rows" in obj and "cols" in obj:
                return f"{obj['rows']} × {obj['cols']}"
            if "rows" in obj and "cols" not in obj:
                return f"{obj['rows']}"
        return _safe(obj)

    def _df_table(df: pd.DataFrame, max_rows: int = 60) -> str:
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return "<span class='ci-muted'>—</span>"
        return df.head(max_rows).to_html(index=False, escape=True, classes="ci-table")

    def _list_preview(items, max_items: int = 16) -> str:
        if not items:
            return "<span class='ci-muted'>—</span>"
        items = list(items)
        shown = items[:max_items]
        rest = len(items) - len(shown)
        chips = "".join([f"<span class='ci-chip'>{_safe(i)}</span>" for i in shown])
        more = f"<span class='ci-muted'>… (+{rest})</span>" if rest > 0 else ""
        return f"<div class='ci-chips'>{chips}{more}</div>"

    def _badge(ok: bool, ok_txt: str = "✓ OK", bad_txt: str = "⚠ Atenção") -> str:
        cls = "ci-badge-ok" if ok else "ci-badge-warn"
        txt = ok_txt if ok else bad_txt
        return f"<span class='ci-badge {cls}'>{_safe(txt)}</span>"

    shapes_before = diagnostics.get("shapes_before", {}) or {}
    shapes_after = diagnostics.get("shapes_after", {}) or {}

    n_features_before = diagnostics.get("n_features_before", "—")
    n_features_after = diagnostics.get("n_features_after", "—")

    consistency = diagnostics.get("train_test_consistency", {}) or {}
    same_feature_count = bool(consistency.get("same_feature_count", False))
    feature_names_match = bool(consistency.get("feature_names_match", False))
    fit_on = diagnostics.get("fit_on", "—")

    X_train_repr = representation.get("X_train")
    X_test_repr = representation.get("X_test")
    y_train_repr = representation.get("y_train")
    y_test_repr = representation.get("y_test")

    feature_names = representation.get("feature_names", []) or []
    target_mapping = representation.get("target_mapping", decision.get("y", {}).get("mapping", {})) or {}

    def _infer_shape(x):
        try:
            if hasattr(x, "shape") and x.shape is not None:
                if len(x.shape) == 1:
                    return {"rows": int(x.shape[0])}
                return {"rows": int(x.shape[0]), "cols": int(x.shape[1])}
        except Exception:
            pass
        return None

    if not isinstance(shapes_before, dict):
        shapes_before = {}
    if not isinstance(shapes_after, dict):
        shapes_after = {}

    shapes_after.setdefault("X_train", _infer_shape(X_train_repr))
    shapes_after.setdefault("X_test", _infer_shape(X_test_repr))
    shapes_after.setdefault("y_train", _infer_shape(y_train_repr))
    shapes_after.setdefault("y_test", _infer_shape(y_test_repr))

    x_dec = decision.get("X", {}) or {}
    x_cat = (x_dec.get("categorical", {}) or {})
    x_num = (x_dec.get("numeric", {}) or {})

    x_decision_html = f"""
    <div class="ci-note">
      Decisão declarada explicitamente no notebook. A UI não infere estratégias.
    </div>
    <div class="ci-kvwrap ci-kvwrap-compact">
      {_kv("X.categorical.strategy", x_cat.get("strategy", "—"))}
      {_kv("X.categorical.handle_unknown", x_cat.get("handle_unknown", "—"))}
      {_kv("X.numeric.strategy", x_num.get("strategy", "—"))}
      {_kv("fit_on", fit_on)}
      {_kv("consistência (n_features)", same_feature_count)}
      {_kv("consistência (feature_names)", feature_names_match)}
    </div>
    """

    shapes_html = f"""
    <div class="ci-subtitle"><b>Shapes (antes)</b></div>
    <div class="ci-kvwrap ci-kvwrap-compact">
      {_kv("X_train", _shape_str(shapes_before.get("X_train")))}
      {_kv("X_test", _shape_str(shapes_before.get("X_test")))}
      {_kv("n_features_before", n_features_before)}
    </div>

    <div class="ci-subtitle"><b>Shapes (depois)</b></div>
    <div class="ci-kvwrap ci-kvwrap-compact">
      {_kv("X_train", _shape_str(shapes_after.get("X_train")))}
      {_kv("X_test", _shape_str(shapes_after.get("X_test")))}
      {_kv("y_train", _shape_str(shapes_after.get("y_train")))}
      {_kv("y_test", _shape_str(shapes_after.get("y_test")))}
      {_kv("n_features_after", n_features_after)}
    </div>

    <div class="ci-note" style="margin-top:10px;">
      {_badge(same_feature_count and feature_names_match, ok_txt="✓ Treino/Teste consistentes", bad_txt="⚠ Risco: inconsistência Treino/Teste")}
      <span class="ci-muted" style="margin-left:8px;">Transformador ajustado apenas no treino (anti-leakage).</span>
    </div>
    """

    y_dec = decision.get("y", {}) or {}
    y_strategy = y_dec.get("strategy", "—")
    y_dtype = y_dec.get("dtype", "—")

    if isinstance(target_mapping, dict) and target_mapping:
        mt = pd.DataFrame([{"raw": k, "encoded": v} for k, v in target_mapping.items()])
        mapping_table = _df_table(mt, max_rows=30)
    else:
        mapping_table = "<span class='ci-muted'>—</span>"

    y_html = f"""
    <div class="ci-note">
      O target é materializado explicitamente nesta seção, sem treinar modelos.
    </div>
    <div class="ci-kvwrap ci-kvwrap-compact">
      {_kv("y.strategy", y_strategy)}
      {_kv("y.dtype", y_dtype)}
      {_kv("mapping_size", len(target_mapping) if isinstance(target_mapping, dict) else "—")}
    </div>

    <div class="ci-subtitle"><b>Mapping aplicado</b></div>
    {mapping_table}
    """

    feat_preview_html = _list_preview(feature_names, max_items=16)

    consolidation_html = f"""
    <div class="ci-note">
      Confirmação de prontidão para a Seção 7:
      X e y estão representados e auditados, sem decisões de métrica/modelo.
    </div>

    <div class="ci-kvwrap ci-kvwrap-compact">
      {_kv("n_feature_names", len(feature_names) if isinstance(feature_names, list) else "—")}
      {_kv("n_features_after", n_features_after)}
      {_kv("fit_on", fit_on)}
      {_kv("train/test aligned", (same_feature_count and feature_names_match))}
    </div>

    <div class="ci-subtitle"><b>Preview de feature_names</b></div>
    {feat_preview_html}

    <div class="ci-note" style="margin-top:10px;">
      <b>Decisões tomadas:</b> encoding de X, representação final de y.<br/>
      <b>Decisões NÃO tomadas:</b> métrica principal, baselines, escolha/tuning de modelos.
    </div>
    """

    css = """
    <style>
      .ci-wrap { font-family: Arial, sans-serif; color: #111827; }
      .ci-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
      @media (max-width:900px) { .ci-grid-2 { grid-template-columns: 1fr; } }

      .ci-card { border: 1px solid #e8edf3; border-radius: 14px; padding: 16px; background: #fff; margin-bottom: 16px; }
      .ci-card-title { font-size: 18px; font-weight: 900; margin-bottom: 8px; }
      .ci-card-body { font-size: 13px; }

      .ci-note { color: #6b7280; font-size: 13px; margin-bottom: 10px; line-height: 1.35; }
      .ci-subtitle { margin-top: 10px; margin-bottom: 6px; font-size: 13px; color: #6b7280; }

      .ci-k { font-size: 12px; color: #6b7280; }
      .ci-v { font-size: 14px; overflow-wrap: anywhere; }

      .ci-kvwrap { display: grid; gap: 10px; }
      .ci-kvwrap-compact { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px 12px; }
      @media (max-width: 900px) { .ci-kvwrap-compact { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
      @media (max-width: 600px) { .ci-kvwrap-compact { grid-template-columns: 1fr; } }

      table.ci-table { width: 100%; border-collapse: collapse; }
      table.ci-table th, table.ci-table td { padding: 8px; border-top: 1px solid #e8edf3; font-size: 13px; vertical-align: top; }
      table.ci-table th { color: #6b7280; font-weight: 800; background: #fbfbfb; }

      .ci-muted { color: #6b7280; }

      .ci-chips { display:flex; flex-wrap:wrap; gap:6px; }
      .ci-chip {
        padding:3px 8px; border-radius:999px;
        border:1px solid #ededed; background:#fafafa;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        font-size:12px;
      }

      .ci-badge {
        display:inline-flex; align-items:center; gap:6px;
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid #e8edf3;
        font-size: 12px;
        font-weight: 800;
        background: #f8fafc;
      }
      .ci-badge-ok { color: #16a34a; border-color:#bbf7d0; background:#ecfdf5; }
      .ci-badge-warn { color: #b45309; border-color:#fde68a; background:#fffbeb; }
    </style>
    """

    html = f"""
    {css}
    <div class="ci-wrap">
      <div class="ci-grid-2">
        {_card("Decisão de Representação das Features (X)", x_decision_html)}
        {_card("Execução do Pré-processamento (auditoria)", shapes_html)}
      </div>
      {_card("Decisão de Representação do Target (y)", y_html)}
      {_card("Consolidação do Dataset Modelável", consolidation_html)}
    </div>
    """

    try:
        from IPython.display import HTML
        return HTML(html)
    except Exception:
        return html



# ============================================================
# Seção 7 — Estratégia de Avaliação e Baselines
# ============================================================

def render_evaluation_report(
    payload: dict,
    title: str = "",
):
    """
    UI-only: renderiza distribuição de classes, baselines e métricas.
    Não calcula nada.
    """
    import pandas as pd
    from IPython.display import HTML, display

    decision = payload.get("decision", {}) or {}
    class_dist = payload.get("class_distribution", {}) or {}
    results = payload.get("baselines_results", []) or []

    def _df_counts(d: dict, split_name: str) -> pd.DataFrame:
        counts = (d.get(split_name, {}) or {}).get("counts", {}) or {}
        pct = (d.get(split_name, {}) or {}).get("pct", {}) or {}
        rows = []
        for k in sorted(counts.keys()):
            rows.append({"class": k, "count": counts[k], "pct": pct.get(k, 0.0)})
        return pd.DataFrame(rows)

    # tabelas
    df_train = _df_counts(class_dist, "train")
    df_test = _df_counts(class_dist, "test")

    # baselines tabela métrica
    metrics_rows = []
    for r in results:
        b = r.get("baseline", {})
        m = r.get("metrics", {})
        metrics_rows.append({
            "baseline": b.get("name"),
            "strategy": b.get("strategy"),
            "accuracy": m.get("accuracy"),
            "precision": m.get("precision"),
            "recall": m.get("recall"),
            "f1": m.get("f1"),
        })
    df_metrics = pd.DataFrame(metrics_rows)

    html = f"""
    <div class="ci-wrap">
      <h2 style="margin:0 0 10px 0;">{title}</h2>

      <div class="ci-card">
        <div class="ci-card-title">Distribuição de classes</div>
        <div class="ci-card-body">
          <div class="ci-grid-2">
            <div>
              <div class="ci-muted" style="margin-bottom:6px;"><b>Treino</b></div>
              {df_train.to_html(index=False, escape=True, classes="ci-table")}
            </div>
            <div>
              <div class="ci-muted" style="margin-bottom:6px;"><b>Teste</b></div>
              {df_test.to_html(index=False, escape=True, classes="ci-table")}
            </div>
          </div>
        </div>
      </div>

      <div class="ci-card">
        <div class="ci-card-title">Decisão de métricas</div>
        <div class="ci-card-body">
          <div><b>primary_metric:</b> {decision.get("primary_metric")}</div>
          <div><b>secondary_metrics:</b> {decision.get("secondary_metrics")}</div>
          <div><b>positive_label:</b> {decision.get("positive_label")}</div>
        </div>
      </div>

      <div class="ci-card">
        <div class="ci-card-title">Baselines e métricas</div>
        <div class="ci-card-body">
          {df_metrics.to_html(index=False, escape=True, classes="ci-table")}
          <div class="ci-muted" style="margin-top:8px;">
            Matrizes de confusão estão no payload (baselines_results[*].confusion_matrix).
          </div>
        </div>
      </div>
    </div>
    """
    display(HTML(html))



# ============================================================
# Seção 8 — Seleção de Modelos e Hiperparâmetros (UI)
# ============================================================

from IPython.display import HTML, display  # garanta que isso existe no topo ou aqui


def render_model_selection_report(
    payload: dict,
    title: str = "Seção 8 — Seleção de Modelos e Hiperparâmetros",
) -> None:
    """
    Renderiza a auditoria da Seção 8 (Leaderboard + decisão).

    Espera payload produzido por:
    - src.models.model_selection.run_section8_model_selection
    """
    if not isinstance(payload, dict):
        raise TypeError("payload deve ser um dict")

    leaderboard = payload.get("leaderboard")
    selection = payload.get("selection", {}) or {}
    inherited = payload.get("inherited_decision", {}) or {}

    selected_key = selection.get("selected_model_key")
    primary_metric = (inherited.get("primary_metric") or "recall")
    baseline_thr = selection.get("baseline_threshold")

    # Leaderboard pode ser DataFrame (ideal) ou lista de dicts (fallback)
    if leaderboard is None:
        lb_rows = []
    elif hasattr(leaderboard, "to_dict"):
        lb_rows = leaderboard.to_dict(orient="records")
    elif isinstance(leaderboard, list):
        lb_rows = leaderboard
    else:
        lb_rows = []

    def esc(x):
        return "" if x is None else str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    rows_html = []
    for r in lb_rows:
        model_key = r.get("model_key")
        eligible = r.get("eligible", True)
        tr_class = ""
        if selected_key and model_key == selected_key:
            tr_class = "selected"
        elif eligible is False:
            tr_class = "ineligible"

        rows_html.append(
            f"""
            <tr class="{tr_class}">
              <td>{esc(r.get("rank"))}</td>
              <td>{esc(r.get("model_key"))}</td>
              <td>{esc(r.get("display_name"))}</td>
              <td>{esc(r.get(primary_metric))}</td>
              <td>{esc(r.get("f1"))}</td>
              <td>{esc(r.get("accuracy"))}</td>
              <td>{esc(r.get("precision"))}</td>
              <td>{esc(r.get("eligible"))}</td>
              <td>{esc(r.get("train_mode"))}</td>
            </tr>
            """
        )

    html = f"""
    <div style="font-family: Arial, sans-serif; color: #eaeaea;">
      <div style="background:#111; border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:14px;">
        <div style="font-size:18px; font-weight:700; margin-bottom:10px;">{esc(title)}</div>

        <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:12px;">
          <div style="background:#0b1220; border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:10px 12px;">
            <div style="opacity:0.8; font-size:12px;">Métrica principal (S7)</div>
            <div style="font-weight:700;">{esc(primary_metric)}</div>
          </div>

          <div style="background:#0b1220; border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:10px 12px;">
            <div style="opacity:0.8; font-size:12px;">Gate baselines (threshold)</div>
            <div style="font-weight:700;">{esc(baseline_thr)}</div>
          </div>

          <div style="background:#071a10; border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:10px 12px;">
            <div style="opacity:0.8; font-size:12px;">Selecionado</div>
            <div style="font-weight:700;">{esc(selected_key) if selected_key else "Nenhum (não superou baselines)"}</div>
          </div>
        </div>

        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>rank</th>
                <th>model_key</th>
                <th>display_name</th>
                <th>{esc(primary_metric)}</th>
                <th>f1</th>
                <th>accuracy</th>
                <th>precision</th>
                <th>eligible</th>
                <th>train_mode</th>
              </tr>
            </thead>
            <tbody>
              {''.join(rows_html)}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <style>
      .table-wrap { overflow-x:auto; }
      .table { width: 100%; border-collapse: collapse; }
      .table th, .table td { padding: 8px 10px; border-bottom: 1px solid rgba(255,255,255,0.08); font-size: 13px; }
      .table th { text-align: left; opacity: 0.85; }
      tr.selected td { background: rgba(34,197,94,0.08); }
      tr.ineligible td { background: rgba(245,158,11,0.06); opacity: 0.8; }
    </style>
    """
    display(HTML(html))
