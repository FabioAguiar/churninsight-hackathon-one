import os
import requests
import streamlit as st

# ============================================================
# ChurnInsight | Team Nexus — Streamlit Frontend (Bank Context)
# Mantém compatibilidade com o contrato externo (Telco-like, 8 campos)
# e faz a ponte semântica (bridge) para o dataset bancário.
# ============================================================

# ------------------------------------------------------------
# Backend URL (Docker-friendly)
# - In Docker Compose: CHURN_JAVA_API_URL=http://java-api:8080
# - Local dev: defaults to http://localhost:8080
# ------------------------------------------------------------
BASE_URL = os.getenv("CHURN_JAVA_API_URL", "http://localhost:8080").rstrip("/")
PREDICT_URL = f"{BASE_URL}/api/predict"

st.set_page_config(
    page_title="ChurnInsight — Bank Churn | Team Nexus",
    page_icon="🏦",
    layout="wide",
)

# ============================================================
# UI Theme (Team Nexus)
# ============================================================
st.markdown(
    """
<style>
/* PAGE */
html, body, [class*="css"]  { background-color: #0b0b0f !important; color: #e8e8e8 !important; }
section[data-testid="stSidebar"] { background-color: #0b0b0f !important; }
div[data-testid="stAppViewContainer"] { background-color: #0b0b0f !important; }
div[data-testid="stHeader"] { background: rgba(0,0,0,0) !important; }

/* HEADERS */
.nexus-header {
    color: #ff4b4b !important;
    font-size: 3.2em;
    font-weight: 900;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 4px;
    margin-top: -10px;
    margin-bottom: 0px;
    text-shadow: 0px 0px 15px rgba(255, 75, 75, 0.35);
}
.team-list {
    color: #ff4b4b !important;
    text-align: center;
    font-size: 0.95em;
    opacity: 0.9;
    margin-top: -10px;
    margin-bottom: 10px;
}
.nexus-subtitle {
    text-align: center;
    opacity: 0.95;
    margin-bottom: 20px;
}

/* CARDS */
.nx-card {
    background: #111118;
    border: 1px solid rgba(255, 75, 75, 0.25);
    border-radius: 16px;
    padding: 14px 16px;
    box-shadow: 0px 0px 18px rgba(255, 75, 75, 0.08);
}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# Helpers: ponte BANK -> contrato externo (8 campos estáveis)
# ============================================================
def credit_score_to_internet_service(score: int) -> str:
    # Buckets (mantém compatibilidade com o contrato externo)
    if score >= 650:
        return "Fiber optic"
    if score >= 550:
        return "DSL"
    return "No"


def products_to_contract(products: int) -> str:
    mapping = {1: "Month-to-month", 2: "One year", 3: "Two year"}
    return mapping.get(products, "Month-to-month")


def yesno(value: bool) -> str:
    return "Yes" if value else "No"


# ============================================================
# Header
# ============================================================
integrantes = [
    "Fábio Aguiar",
    "Lilian Moraes",
    "Luedji Abayomi",
    "Lucas Frigato",
    "Wenderson Lopes",
]
integrantes.sort()
integrantes_formatado = " • ".join(integrantes)

st.markdown('<p class="nexus-header">TEAM NEXUS</p>', unsafe_allow_html=True)
st.markdown(f'<p class="team-list">{integrantes_formatado}</p>', unsafe_allow_html=True)

st.markdown(
    '<p class="nexus-subtitle">🏦 <b>ChurnInsight</b> — Previsão de Churn (Dataset Bancário) com <i>bridge</i> para contrato externo estável</p>',
    unsafe_allow_html=True,
)

with st.expander("ℹ️ Como esta tela se conecta ao modelo?", expanded=False):
    st.markdown(
        """
**Regra de ouro:** o frontend **não muda** o payload externo enviado ao Java (`POST /api/predict`).
O contrato permanece Telco-like (8 campos), e a adaptação para o **dataset bancário** acontece aqui na UI via **ponte semântica (bridge)**.

### Bridge (Bank → Contrato Externo)

- `tenure` ← **Tempo como cliente (meses)**
- `monthly_charges` ← **Salário estimado**
- `contract` ← **Número de produtos (1–3)**:
  - 1 → `Month-to-month`
  - 2 → `One year`
  - 3 → `Two year`
- `internet_service` ← **Credit Score** (bucket):
  - score ≥ 650 → `Fiber optic`
  - score ≥ 550 → `DSL`
  - senão → `No`
- `paperless_billing` ← **Possui cartão de crédito?**
- `tech_support` e `online_security` ← **Cliente ativo?** (mantidos iguais para evitar inconsistência)
- `payment_method` ← **default fixo** (apenas para completar o contrato)
"""
    )

st.divider()

# ============================================================
# Layout
# ============================================================
col_form, col_result = st.columns([1, 1.25], gap="large")

# --- Form (Bank context)
with col_form:
    st.subheader("🧾 Dados do Cliente (Banco)")
    st.caption("Preencha os campos do contexto bancário. A UI gerará o payload Telco-like compatível automaticamente.")

    with st.form("bank_form"):
        tenure = st.number_input(
            "Tempo como cliente (meses)",
            min_value=0,
            max_value=120,
            value=12,
            step=1,
        )

        estimated_salary = st.number_input(
            "Salário estimado (R$)",
            min_value=0.0,
            max_value=1_000_000.0,
            value=3500.0,
            step=100.0,
        )

        products_number = st.selectbox(
            "Número de produtos (1–3)",
            options=[1, 2, 3],
            index=1,
        )

        credit_score = st.slider(
            "Credit Score (0–1000)",
            min_value=0,
            max_value=1000,
            value=600,
            step=1,
        )

        c1, c2 = st.columns(2)
        with c1:
            has_credit_card = st.toggle("Possui cartão de crédito?", value=True)
        with c2:
            is_active_member = st.toggle("Cliente ativo?", value=True)

        submit = st.form_submit_button("📈 Analisar risco de churn", use_container_width=True)

# --- Result
with col_result:
    st.subheader("🧠 Diagnóstico")
    st.caption("O diagnóstico vem da API Java, que orquestra a inferência no serviço Python (FastAPI).")

    if submit:
        payload = {
            "tenure": int(tenure),
            "monthly_charges": float(estimated_salary),
            "contract": products_to_contract(int(products_number)),
            "internet_service": credit_score_to_internet_service(int(credit_score)),
            "payment_method": "Electronic check",
            "online_security": yesno(bool(is_active_member)),
            "tech_support": yesno(bool(is_active_member)),
            "paperless_billing": yesno(bool(has_credit_card)),
        }

        with st.expander("🛠️ Debug (opcional)", expanded=False):
            st.markdown(f"**CHURN_JAVA_API_URL / BASE_URL:** `{BASE_URL}`")
            st.markdown(f"**Endpoint:** `{PREDICT_URL}`")
            st.markdown("**Payload enviado (Telco-like, 8 campos):**")
            st.json(payload)

        try:
            with st.spinner("Conectando ao Gateway (Java Spring Boot)..."):
                resp = requests.post(PREDICT_URL, json=payload, timeout=30)

            if resp.status_code == 200:
                data = resp.json()
                previsao = data.get("previsao", "Indefinido")
                prob = float(data.get("probabilidade", 0.0)) * 100.0

                st.markdown('<div class="nx-card">', unsafe_allow_html=True)
                if previsao == "Vai cancelar":
                    st.error("🚨 **ALERTA DE CHURN DETECTADO**")
                    st.markdown(f"### Probabilidade de Evasão: **{prob:.1f}%**")
                    st.toast("Risco crítico identificado!", icon="🔥")
                else:
                    st.success("✅ **CLIENTE COM BAIXO RISCO**")
                    st.markdown(f"### Probabilidade de Evasão: **{prob:.1f}%**")
                    st.toast("Cliente com baixo risco.", icon="✅")
                st.markdown("</div>", unsafe_allow_html=True)

            else:
                st.error(f"❌ Erro na API Java: HTTP {resp.status_code}")
                try:
                    st.json(resp.json())
                except Exception:
                    st.code(resp.text)

        except requests.RequestException as e:
            st.error("❌ Falha ao conectar ao backend Java.")
            st.info(
                "Verifique se o backend Java está rodando e acessível."
                f"- URL atual: {PREDICT_URL}"
                "- Docker Compose: confirme CHURN_JAVA_API_URL=http://java-api:8080"
            )
            with st.expander("Detalhes do erro"):
                st.write(e)

    else:
        st.info("👈 Preencha o formulário ao lado e clique em **Analisar** para obter a previsão.")
        st.image(
            "https://images.unsplash.com/photo-1639322537228-f710d846310a?q=80&w=2232&auto=format&fit=crop",
            caption="Nexus Analytics System",
        )

st.divider()
st.caption(
    "Docker Compose: frontend em **http://localhost:8501** | Java em **http://localhost:8080/api/predict** (rota de inferência) | "
    "Dentro da rede Docker, o frontend usa `CHURN_JAVA_API_URL=http://java-api:8080`."
)
