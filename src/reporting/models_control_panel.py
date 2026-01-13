"""
ChurnInsight — N2 — Models Control Panel (Telco-style)

Arquivo: src/reporting/models_control_panel.py

Objetivo
- Painel interativo para seleção de modelos e hiperparâmetros (Seção 8).
- Execução SOMENTE ao clicar em "Rodar experimento".
- Saída do processamento no estilo "log do notebook" (print padrão), como no projeto Telco.

Notas importantes (clareza conceitual)
- As métricas (accuracy/precision/recall/f1/roc_auc) pertencem ao PAINEL (S8).
  Elas sempre são calculadas aqui e não "dependem" de seções anteriores para existir.
- A Seção 7 (S7) pode registrar uma RECOMENDAÇÃO de critério de decisão (ex.: recall),
  mas isso não limita o painel: você pode ordenar o Leaderboard por qualquer métrica.

Compatibilidade
- Mantém a função `render_section8_models_panel(...)` como alias, para notebooks legados.
  Se você atualizar seus imports para `render_models_control_panel`, pode remover o arquivo
  section8_panel.py com segurança (desde que nenhum notebook/import ainda o referencie).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional

import pandas as pd
import ipywidgets as W
from IPython.display import display

from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB


# -----------------------------------------------------------------------------
# S8 state (exportável)
# -----------------------------------------------------------------------------
#
# A Seção 8 (painel) é executada interativamente e precisa expor artefatos
# treinados para a Seção 9 (dump/exportação) SEM retraining.
#
# Este estado é propositalmente simples (MVP):
# - best_estimators: dict[model_key] -> estimador treinado (ou best_estimator_)
# - leaderboard_df: DataFrame com as métricas exibidas no painel
# - runs: lista de dicts (mesmo conteúdo que vira o DataFrame)
#
# Importante:
# - Não há decisão automática aqui.
# - A S9 escolhe explicitamente qual model_key exportar.

_STATE_S8: Dict[str, Any] = {
    "best_estimators": {},
    "leaderboard_df": None,
    "runs": [],
}


def get_payload_s8() -> Dict[str, Any]:
    """Retorna um snapshot consumível da execução mais recente do painel (S8)."""
    return {
        "best_estimators": _STATE_S8.get("best_estimators", {}) or {},
        "leaderboard_df": _STATE_S8.get("leaderboard_df"),
        "runs": _STATE_S8.get("runs", []) or [],
    }


# -----------------------------
# Utils
# -----------------------------

def _now_str() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _fmt4(x: Any) -> str:
    try:
        return f"{float(x):.4f}"
    except Exception:
        return str(x)


def _safe_literal_dict(text: str) -> Dict[str, Any]:
    """Lê um dict a partir do textarea (ast.literal_eval — seguro)."""
    import ast
    obj = ast.literal_eval(text)
    if not isinstance(obj, dict):
        raise ValueError("O texto não avaliou para um dict.")
    return obj


def _set_enabled(widget: W.Widget, enabled: bool) -> None:
    """Habilita/desabilita um widget e seus filhos (quando aplicável)."""
    try:
        widget.disabled = not enabled
    except Exception:
        pass

    if hasattr(widget, "children"):
        for c in (widget.children or []):
            if isinstance(c, W.Widget):
                _set_enabled(c, enabled)


def _compute_metrics(y_true, y_pred, y_score=None, positive_label=1) -> Dict[str, float]:
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, pos_label=positive_label, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, pos_label=positive_label, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, pos_label=positive_label, zero_division=0)),
    }
    if y_score is not None:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_score))
        except Exception:
            metrics["roc_auc"] = float("nan")
    else:
        metrics["roc_auc"] = float("nan")
    return metrics


def _resolve_splits_canonical(
    payload_s6: dict,
    payload_s5: dict | None = None,
    split: dict | None = None,
    **_kw,
):
    """
    Resolve X_train/X_test/y_train/y_test pelo contrato canônico do pipeline.

    Preferência (mais estrito e canônico):
    1) `split` (argumento explícito)
    2) `payload_s6['split']` (fallback)
    3) `payload_s5['split']` (canônico)
    """
    if isinstance(split, dict) and all(k in split for k in ("X_train", "X_test", "y_train", "y_test")):
        return split["X_train"], split["X_test"], split["y_train"], split["y_test"], "split (arg)"

    if isinstance(payload_s6, dict) and isinstance(payload_s6.get("split"), dict):
        s = payload_s6["split"]
        if all(k in s for k in ("X_train", "X_test", "y_train", "y_test")):
            return s["X_train"], s["X_test"], s["y_train"], s["y_test"], "payload_s6['split']"

    if isinstance(payload_s5, dict) and isinstance(payload_s5.get("split"), dict):
        s = payload_s5["split"]
        if all(k in s for k in ("X_train", "X_test", "y_train", "y_test")):
            return s["X_train"], s["X_test"], s["y_train"], s["y_test"], "payload_s5['split']"

    raise KeyError(
        "Não encontrei X_train/X_test/y_train/y_test.\n"
        "Contrato canônico: splits vêm da Seção 5 em payload_s5['split'].\n"
        "Passe `payload_s5=payload_s5` ao chamar o painel, ou `split=payload_s5['split']`.\n"
        "Alternativamente, empacote `payload_s6['split']`."
    )


# -----------------------------
# Model specs + grids
# -----------------------------

@dataclass
class _ModelSpec:
    key: str
    name: str
    make_estimator: Any
    default_params: Dict[str, Any]
    light_grid: Dict[str, List[Any]]
    recommended_grid: Dict[str, List[Any]]


def _specs() -> Dict[str, _ModelSpec]:
    return {
        "logreg": _ModelSpec(
            key="logreg",
            name="Logistic Regression",
            make_estimator=lambda: LogisticRegression(),
            default_params={"C": 1.0, "penalty": "l2", "solver": "lbfgs", "max_iter": 1000, "n_jobs": -1},
            light_grid={
                "C": [0.01, 0.1, 1.0, 10.0],
                "penalty": ["l2"],
                "solver": ["liblinear", "lbfgs"],
                "class_weight": [None, "balanced"],
                "max_iter": [500],
            },
            recommended_grid={
                "C": [0.01, 0.1, 1.0, 10.0, 100.0],
                "class_weight": [None, "balanced"],
                "max_iter": [500, 1500],
                "penalty": ["l2"],
                "solver": ["lbfgs", "newton-cg"],
            },
        ),
        "rf": _ModelSpec(
            key="rf",
            name="Random Forest",
            make_estimator=lambda: RandomForestClassifier(random_state=42),
            default_params={
                "n_estimators": 300,
                "max_depth": 20,
                "min_samples_split": 2,
                "min_samples_leaf": 1,
                "max_features": "sqrt",
                "bootstrap": True,
                "n_jobs": -1,
            },
            light_grid={
                "n_estimators": [100, 300],
                "max_depth": [None, 5, 10],
                "min_samples_split": [2, 5],
                "min_samples_leaf": [1, 3],
                "class_weight": [None, "balanced"],
                "random_state": [42],
            },
            recommended_grid={
                "n_estimators": [200, 300, 500],
                "max_depth": [None, 10, 20, 40],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4],
                "max_features": ["sqrt", "log2"],
                "bootstrap": [True, False],
                "class_weight": [None, "balanced"],
                "n_jobs": [-1],
            },
        ),
        "knn": _ModelSpec(
            key="knn",
            name="K-Nearest Neighbors",
            make_estimator=lambda: KNeighborsClassifier(),
            default_params={"n_neighbors": 5, "weights": "uniform", "metric": "minkowski", "p": 2},
            light_grid={
                "n_neighbors": [3, 5, 7, 11],
                "weights": ["uniform", "distance"],
                "metric": ["euclidean", "manhattan"],
            },
            recommended_grid={
                "metric": ["minkowski", "euclidean", "manhattan"],
                "n_neighbors": [3, 5, 7, 9, 15, 25],
                "p": [1, 2],
                "weights": ["uniform", "distance"],
            },
        ),
        "dt": _ModelSpec(
            key="dt",
            name="Decision Tree",
            make_estimator=lambda: DecisionTreeClassifier(random_state=42),
            default_params={"max_depth": 20, "min_samples_split": 2, "min_samples_leaf": 1, "criterion": "gini"},
            light_grid={
                "max_depth": [None, 5, 10],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 3, 5],
                "criterion": ["gini", "entropy"],
                "class_weight": [None, "balanced"],
                "random_state": [42],
            },
            recommended_grid={
                "max_depth": [None, 5, 10, 20, 40],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4],
                "criterion": ["gini", "entropy"],
                "class_weight": [None, "balanced"],
            },
        ),
        "gnb": _ModelSpec(
            key="gnb",
            name="Gaussian Naive Bayes",
            make_estimator=lambda: GaussianNB(),
            default_params={"var_smoothing": 1e-9},
            light_grid={
                "var_smoothing": [1e-9, 1e-8, 1e-7],
            },
            recommended_grid={"var_smoothing": [1e-12, 1e-10, 1e-9, 1e-8]},
        ),
    }


# -----------------------------
# UI per model (single params)
# -----------------------------

@dataclass
class _ModelUI:
    checkbox: W.Checkbox
    tab_root: W.Widget
    mode: W.ToggleButtons
    panel_box: W.Widget
    dict_area: W.Textarea
    widgets: Dict[str, W.Widget]


def _mk_logreg_panel(defaults: Dict[str, Any]) -> Tuple[W.Widget, Dict[str, W.Widget]]:
    wC = W.FloatSlider(value=float(defaults["C"]), min=0.01, max=10.0, step=0.01, description="C",
                       readout_format=".3f", layout=W.Layout(width="360px"))
    wpen = W.Dropdown(options=["l2"], value=str(defaults["penalty"]), description="penalty",
                      layout=W.Layout(width="360px"))
    wsol = W.Dropdown(options=["lbfgs", "newton-cg"], value=str(defaults["solver"]), description="solver",
                      layout=W.Layout(width="360px"))
    witer = W.IntSlider(value=int(defaults["max_iter"]), min=200, max=3000, step=50, description="max_iter",
                        layout=W.Layout(width="360px"))
    wjobs = W.IntSlider(value=int(defaults["n_jobs"]), min=-1, max=8, step=1, description="n_jobs",
                        layout=W.Layout(width="360px"))
    box = W.VBox([wC, wpen, wsol, witer, wjobs], layout=W.Layout(padding="6px 2px"))
    return box, {"C": wC, "penalty": wpen, "solver": wsol, "max_iter": witer, "n_jobs": wjobs}


def _mk_rf_panel(defaults: Dict[str, Any]) -> Tuple[W.Widget, Dict[str, W.Widget]]:
    wne = W.IntSlider(value=int(defaults["n_estimators"]), min=50, max=800, step=50, description="n_estimators",
                      layout=W.Layout(width="360px"))
    wmd = W.Dropdown(options=[None, 10, 20, 30, 40, 60], value=defaults.get("max_depth"),
                     description="max_depth", layout=W.Layout(width="360px"))
    wms = W.IntSlider(value=int(defaults["min_samples_split"]), min=2, max=20, step=1, description="min_split",
                      layout=W.Layout(width="360px"))
    wml = W.IntSlider(value=int(defaults["min_samples_leaf"]), min=1, max=10, step=1, description="min_leaf",
                      layout=W.Layout(width="360px"))
    wmf = W.Dropdown(options=["sqrt", "log2"], value=str(defaults["max_features"]), description="max_feat",
                     layout=W.Layout(width="360px"))
    wbs = W.Checkbox(value=bool(defaults["bootstrap"]), description="bootstrap")
    wjobs = W.IntSlider(value=int(defaults["n_jobs"]), min=-1, max=8, step=1, description="n_jobs",
                        layout=W.Layout(width="360px"))
    box = W.VBox([wne, wmd, wms, wml, wmf, wbs, wjobs], layout=W.Layout(padding="6px 2px"))
    return box, {
        "n_estimators": wne,
        "max_depth": wmd,
        "min_samples_split": wms,
        "min_samples_leaf": wml,
        "max_features": wmf,
        "bootstrap": wbs,
        "n_jobs": wjobs,
    }


def _mk_knn_panel(defaults: Dict[str, Any]) -> Tuple[W.Widget, Dict[str, W.Widget]]:
    wnn = W.IntSlider(value=int(defaults["n_neighbors"]), min=1, max=50, step=1, description="n_neighbors",
                      layout=W.Layout(width="360px"))
    wwt = W.Dropdown(options=["uniform", "distance"], value=str(defaults["weights"]), description="weights",
                     layout=W.Layout(width="360px"))
    wmet = W.Dropdown(options=["minkowski", "euclidean", "manhattan"], value=str(defaults["metric"]),
                      description="metric", layout=W.Layout(width="360px"))
    wp = W.IntSlider(value=int(defaults["p"]), min=1, max=2, step=1, description="p",
                     layout=W.Layout(width="360px"))
    box = W.VBox([wnn, wwt, wmet, wp], layout=W.Layout(padding="6px 2px"))
    return box, {"n_neighbors": wnn, "weights": wwt, "metric": wmet, "p": wp}


def _mk_dt_panel(defaults: Dict[str, Any]) -> Tuple[W.Widget, Dict[str, W.Widget]]:
    wmd = W.Dropdown(options=[None, 5, 10, 20, 40, 60], value=defaults.get("max_depth"),
                     description="max_depth", layout=W.Layout(width="360px"))
    wms = W.IntSlider(value=int(defaults["min_samples_split"]), min=2, max=20, step=1, description="min_split",
                      layout=W.Layout(width="360px"))
    wml = W.IntSlider(value=int(defaults["min_samples_leaf"]), min=1, max=10, step=1, description="min_leaf",
                      layout=W.Layout(width="360px"))
    wcr = W.Dropdown(options=["gini", "entropy"], value=str(defaults.get("criterion", "gini")),
                     description="criterion", layout=W.Layout(width="360px"))
    box = W.VBox([wmd, wms, wml, wcr], layout=W.Layout(padding="6px 2px"))
    return box, {"max_depth": wmd, "min_samples_split": wms, "min_samples_leaf": wml, "criterion": wcr}


def _mk_gnb_panel(defaults: Dict[str, Any]) -> Tuple[W.Widget, Dict[str, W.Widget]]:
    wvs = W.FloatLogSlider(value=float(defaults["var_smoothing"]), base=10, min=-12, max=-6, step=0.1,
                           description="var_smoothing", layout=W.Layout(width="360px"))
    box = W.VBox([wvs], layout=W.Layout(padding="6px 2px"))
    return box, {"var_smoothing": wvs}


def _mk_panel_for(model_key: str, defaults: Dict[str, Any]) -> Tuple[W.Widget, Dict[str, W.Widget]]:
    if model_key == "logreg":
        return _mk_logreg_panel(defaults)
    if model_key == "rf":
        return _mk_rf_panel(defaults)
    if model_key == "knn":
        return _mk_knn_panel(defaults)
    if model_key == "dt":
        return _mk_dt_panel(defaults)
    if model_key == "gnb":
        return _mk_gnb_panel(defaults)
    raise ValueError(f"Modelo desconhecido: {model_key}")


# -----------------------------
# Public API
# -----------------------------

def render_models_control_panel(
    payload_s6: Dict[str, Any],
    payload_s7: Dict[str, Any],
    payload_s5: Optional[Dict[str, Any]] = None,
    split: Optional[Dict[str, Any]] = None,
) -> None:
    decision = payload_s7.get("decision") or {}

    # S7 pode sugerir um critério (recomendação), mas o painel é livre.
    recommended_metric = str(decision.get("primary_metric") or "recall")
    positive_label = int(decision.get("positive_label") or 1)

    # Para "estilo Telco": default visual do leaderboard = F1 (padrão)
    default_leaderboard_metric = "f1"

    # Split canônico
    X_train, X_test, y_train, y_test, split_path = _resolve_splits_canonical(
        payload_s6, payload_s5=payload_s5, split=split
    )

    specs = _specs()
    order = ["logreg", "rf", "knn", "dt", "gnb"]

    # Header checkboxes
    checkboxes: Dict[str, W.Checkbox] = {}
    for k in order:
        default_on = k in ["logreg", "rf", "knn", "dt"]  # gnb off por padrão
        checkboxes[k] = W.Checkbox(value=default_on, description=specs[k].name)
    header = W.HBox(list(checkboxes.values()), layout=W.Layout(flex_flow="row wrap", gap="18px"))

    # Leaderboard output
    lb_out = W.Output(layout=W.Layout(border="1px solid rgba(0,0,0,0.15)", padding="10px", width="100%"))

    # Dropdown (nomenclatura idêntica ao Telco)
    order_by = W.Dropdown(
        options=[
            ("F1 (padrão)", "f1"),
            ("Accuracy", "accuracy"),
            ("Precision", "precision"),
            ("Recall", "recall"),
            ("ROC-AUC", "roc_auc"),
        ],
        value=default_leaderboard_metric,
        description="Ordenar por:",
        layout=W.Layout(width="260px"),
    )

    run_btn = W.Button(description="▶ Rodar experimento", button_style="primary")

    log_out = W.Output(layout=W.Layout(border="1px solid rgba(0,0,0,0.15)", padding="10px", width="100%"))


    models_ui: Dict[str, _ModelUI] = {}

    def _render_leaderboard() -> None:
        # leaderboard sempre vem do último run do painel
        df = _STATE_S8.get("leaderboard_df")
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return

        sort_col = order_by.value or "f1"
        if sort_col not in df.columns:
            sort_col = "f1"

        out = df.sort_values(by=sort_col, ascending=False).reset_index(drop=True)
        out.insert(0, "rank", range(1, len(out) + 1))

        lb_out.clear_output()
        with lb_out:
            # Destaque da coluna selecionada (Telco-like)
            styler = out.style
            if sort_col in out.columns:
                def _bold_selected(col):
                    if col.name == sort_col:
                        return ["font-weight: bold"] * len(col)
                    return [""] * len(col)
                styler = styler.apply(_bold_selected, axis=0)

            # Formatação leve (mantém leitura)
            for c in ["accuracy", "precision", "recall", "f1", "roc_auc"]:
                if c in out.columns:
                    styler = styler.format({c: "{:.4f}"})
            display(styler)

    def _on_order_change(_change):
        _render_leaderboard()

    order_by.observe(_on_order_change, "value")

    def _apply_mode_rules(model_key: str) -> None:
        ui = models_ui[model_key]
        if not ui.checkbox.value:
            _set_enabled(ui.tab_root, False)
            return

        _set_enabled(ui.tab_root, True)

        # modo exclusivo (sem loops)
        mode = ui.mode.value or "Busca de hiperparâmetros"
        search = mode == "Busca de hiperparâmetros"

        if search:
            _set_enabled(ui.panel_box, False)
            _set_enabled(ui.dict_area, True)
        else:
            _set_enabled(ui.panel_box, True)
            _set_enabled(ui.dict_area, False)

    def _mk_model_tab(model_key: str) -> W.Widget:
        spec = specs[model_key]

        mode = W.ToggleButtons(
            options=["Busca de hiperparâmetros", "Treino simples"],
            value="Busca de hiperparâmetros",
            layout=W.Layout(width="420px"),
        )

        def _mode_change(_=None):
            _apply_mode_rules(model_key)

        mode.observe(_mode_change, "value")

        panel_box, widgets = _mk_panel_for(model_key, spec.default_params)

        # default textarea: grid leve + cv=3 (fluidez demo)
        search_config = {
            "cv": 3,
            "model_key": model_key,
            "n_jobs": -1,
            "param_grid": spec.light_grid,
            "refit": "f1",
            "scoring": "f1",
            "search_type": "grid",
            "verbose": 0,
        }
        dict_area = W.Textarea(value=str(search_config), layout=W.Layout(width="680px", height="260px"))

        left = W.VBox(
            [
                W.Label(spec.name),
                W.Label("Modo"),
                mode,
                W.Label("Treino simples — parâmetros"),
                panel_box,
            ],
            layout=W.Layout(width="420px", padding="4px 6px"),
        )

        right = W.VBox(
            [
                W.Label("Configuração para busca de hiperparâmetros (dict)"),
                dict_area,
            ],
            layout=W.Layout(width="720px", padding="4px 6px"),
        )

        root = W.HBox([left, right], layout=W.Layout(gap="18px"))

        ui = _ModelUI(
            checkbox=checkboxes[model_key],
            tab_root=root,
            mode=mode,
            panel_box=panel_box,
            dict_area=dict_area,
            widgets=widgets,
        )
        models_ui[model_key] = ui

        def _cb_change(_=None):
            _apply_mode_rules(model_key)

        ui.checkbox.observe(_cb_change, "value")
        _apply_mode_rules(model_key)
        return root

    tabs = W.Tab()
    tabs.children = [_mk_model_tab(k) for k in order]
    for i, k in enumerate(order):
        tabs.set_title(i, specs[k].name)

    def _extract_single_params(model_key: str) -> Dict[str, Any]:
        ui = models_ui[model_key]
        out: Dict[str, Any] = {}
        for k, w in ui.widgets.items():
            out[k] = getattr(w, "value", None)
        if model_key in ("rf", "dt"):
            out["random_state"] = 42
        return out

    def _run(_btn):
        # Logs ancorados (Telco-style) + leaderboard separado
        log_out.clear_output()
        lb_out.clear_output()
        _STATE_S8["leaderboard_df"] = None
        _STATE_S8["runs"] = []
        _STATE_S8["best_estimators"] = {}

        # Helpers: sempre escrever dentro do Output (log ancorado)
        def _log(*args, **kwargs):
            with log_out:
                print(*args, **kwargs)

        def _pp(obj):
            with log_out:
                from pprint import pprint as _pprint
                _pprint(obj)

        runs: List[Dict[str, Any]] = []
        best_estimators: Dict[str, Any] = {}

        # Fila de execução: TODOS os modelos marcados nos checkboxes (ordem fixa)
        selected_keys = [k for k in order if models_ui[k].checkbox.value]

        _log(f"[INFO] Modelos selecionados (fila): {', '.join(selected_keys) if selected_keys else 'nenhum'}")
        _log("")

        if not selected_keys:
            _log("[WARN] Nenhum modelo selecionado. Marque pelo menos um checkbox acima e rode novamente.")
            return

        _log(f"[INFO] Iniciando experimentos em {_now_str()}...")
        _log(f"[INFO] Splits resolvidos via: {split_path}")
        _log(f"[INFO] Recomendação (S7) — critério sugerido: {recommended_metric} (não obrigatório no painel)")
        _log("")

        for model_key in selected_keys:
            ui = models_ui[model_key]
            try:

                spec = specs[model_key]
                run_type = "search" if (ui.mode.value == "Busca de hiperparâmetros") else "single"

                _log("=" * 72)
                _log(f"[INFO] Modelo: {spec.name} (key='{model_key}') | modo={run_type}")

                if run_type == "search":
                    cfg = _safe_literal_dict(ui.dict_area.value)

                    param_grid = cfg.get("param_grid") or {}
                    cv = int(cfg.get("cv") or 3)
                    n_jobs = int(cfg.get("n_jobs") or -1)
                    scoring = str(cfg.get("scoring") or "f1")
                    refit = str(cfg.get("refit") or "f1")
                    verbose = int(cfg.get("verbose") or 0)

                    _log("[INFO] Busca de hiperparâmetros com config:")
                    _pp(cfg)

                    est = spec.make_estimator()
                    gs = GridSearchCV(
                        estimator=est,
                        param_grid=param_grid,
                        cv=cv,
                        n_jobs=n_jobs,
                        scoring=scoring,
                        refit=refit,
                        verbose=verbose,
                    )
                    gs.fit(X_train, y_train)

                    best_est = gs.best_estimator_

                    # S8 → S9: salvar o melhor estimador treinado (sem decisão automática)
                    best_estimators[model_key] = best_est
                    y_pred = best_est.predict(X_test)

                    y_score = None
                    if hasattr(best_est, "predict_proba"):
                        try:
                            y_score = best_est.predict_proba(X_test)[:, 1]
                        except Exception:
                            y_score = None

                    metrics = _compute_metrics(y_test, y_pred, y_score=y_score, positive_label=positive_label)

                    _log("[INFO] Métricas (melhor modelo — teste):")
                    _log(f"  accuracy  = {_fmt4(metrics.get('accuracy'))}")
                    _log(f"  precision = {_fmt4(metrics.get('precision'))}")
                    _log(f"  recall    = {_fmt4(metrics.get('recall'))}")
                    _log(f"  f1        = {_fmt4(metrics.get('f1'))}")
                    _log(f"  roc_auc   = {_fmt4(metrics.get('roc_auc'))}")

                    runs.append(
                        {
                            "label": f"{spec.name} — search",
                            "model_name": spec.name,
                            "model_key": model_key,
                            "run_type": "search",
                            **metrics,
                        }
                    )

                else:
                    params = _extract_single_params(model_key)
                    _log(f"[INFO] Treino simples com params: {params}")

                    est = spec.make_estimator()
                    try:
                        est.set_params(**params)
                    except Exception:
                        pass

                    est.fit(X_train, y_train)

                    # S8 → S9: salvar o estimador treinado (treino simples)
                    best_estimators[model_key] = est
                    y_pred = est.predict(X_test)

                    y_score = None
                    if hasattr(est, "predict_proba"):
                        try:
                            y_score = est.predict_proba(X_test)[:, 1]
                        except Exception:
                            y_score = None

                    metrics = _compute_metrics(y_test, y_pred, y_score=y_score, positive_label=positive_label)

                    _log("[INFO] Métricas (teste):")
                    _log(f"  accuracy  = {_fmt4(metrics.get('accuracy'))}")
                    _log(f"  precision = {_fmt4(metrics.get('precision'))}")
                    _log(f"  recall    = {_fmt4(metrics.get('recall'))}")
                    _log(f"  f1        = {_fmt4(metrics.get('f1'))}")
                    _log(f"  roc_auc   = {_fmt4(metrics.get('roc_auc'))}")

                    runs.append(
                        {
                            "label": f"{spec.name} — single",
                            "model_name": spec.name,
                            "model_key": model_key,
                            "run_type": "single",
                            **metrics,
                        }
                    )

            except Exception as e:
                _log(f"[ERROR] Falha ao processar '{model_key}': {e}")
                import traceback
                with log_out:
                    traceback.print_exc()
        _log("")
        with log_out:
            _log("[INFO] Execução concluída.")

        if not runs:
            _log("Nenhum modelo selecionado.")
            return

        df = pd.DataFrame(runs)
        _STATE_S8["runs"] = runs
        _STATE_S8["leaderboard_df"] = df
        _STATE_S8["best_estimators"] = best_estimators
        _render_leaderboard()

    run_btn.on_click(_run)

    # Texto do painel: separação cristalina
    title = W.Label("")
    subtitle = W.HTML(
        f"<div style='line-height:1.35'>"

        f"</div>"
    )

    display(
        W.VBox(
            [
                title,
                subtitle,
                header,
                tabs,
                run_btn,
                W.HBox([W.Label("Logs:"), W.Label("Saída do processamento (sempre visível)")]),
                log_out,
                W.HBox([W.Label("Leaderboard:"), order_by]),
                lb_out,
            ],
            layout=W.Layout(gap="10px"),
        )
    )


# Alias de compatibilidade
def render_section8_models_panel(
    payload_s6: Dict[str, Any],
    payload_s7: Dict[str, Any],
    payload_s5: Optional[Dict[str, Any]] = None,
    split: Optional[Dict[str, Any]] = None,
) -> None:
    return render_models_control_panel(payload_s6=payload_s6, payload_s7=payload_s7, payload_s5=payload_s5, split=split)
