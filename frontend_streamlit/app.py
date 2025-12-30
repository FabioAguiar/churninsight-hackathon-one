import streamlit as st
import requests

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="ChurnInsight | Team Nexus",
    page_icon="🔮",
    layout="wide"
)

# --- 2. ESTILIZAÇÃO CSS (PRETO E LARANJA NEON) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700;900&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Roboto', sans-serif;
    }

    /* Fundo Global */
    .stApp {
        background-color: #050505;
        border-top: 5px solid #ff4b4b;
    }
    
    /* Textos Gerais */
    h1, h2, h3, p, label, .stMarkdown, .stText {
        color: #e0e0e0 !important;
    }
    
    /* TÍTULO TEAM NEXUS (GIGANTE) */
    .nexus-header {
        color: #ff4b4b !important;
        font-size: 4.5em;
        font-weight: 900;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 4px;
        margin-top: -30px;
        margin-bottom: 5px;
        text-shadow: 0px 0px 15px rgba(255, 75, 75, 0.4);
    }
    
    /* LISTA DE INTEGRANTES */
    .team-list {
        color: #ff4b4b !important;
        text-align: center;
        font-size: 1.1em;
        font-weight: 500;
        margin-bottom: 40px;
        border-bottom: 1px solid #333;
        padding-bottom: 20px;
        opacity: 0.9;
    }

    /* Botões - CORREÇÃO DE LARGURA VIA CSS */
    div.stButton > button {
        background-color: #ff4b4b;
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
        text-transform: uppercase;
        width: 100%; /* Força a largura total sem precisar do Python */
    }
    div.stButton > button:hover {
        background-color: #ff2b2b;
        box-shadow: 0px 0px 10px #ff4b4b;
    }

    /* Inputs Dark */
    .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #111;
        color: white;
        border: 1px solid #333;
    }
    
    /* Slider */
    div.stSlider > div[data-baseweb = "slider"] > div > div {
        background-color: #ff4b4b !important;
    }
    
    /* Imagens Responsivas */
    img {
        max-width: 100%;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. CABEÇALHO E EQUIPE ---

integrantes = [
    "Bruno Hagemann", 
    "Fábio Aguiar", 
    "Fábio Almeida", 
    "João Vitor", 
    "Lilian Moraes", 
    "Luedji Abayomi", 
    "Lucas Frigato", 
    "Wenderson"
]
integrantes.sort()
integrantes_formatado = " • ".join(integrantes)

st.markdown('<p class="nexus-header">TEAM NEXUS</p>', unsafe_allow_html=True)
st.markdown(f'<p class="team-list">{integrantes_formatado}</p>', unsafe_allow_html=True)

# --- 4. LAYOUT PRINCIPAL ---
col_form, col_result = st.columns([1, 1.3], gap="large")

with col_form:
    st.subheader(":memo: Dados do Cliente")
    st.caption("Insira os parâmetros contratuais para simulação.")
    
    tenure = st.slider("Meses de Contrato", 0, 72, 12)
    monthly_charges = st.number_input("Fatura Mensal ($)", 0.0, 1000.0, 70.0, step=10.0)
    
    contract = st.selectbox("Tipo de Contrato", ["Month-to-month", "One year", "Two year"])
    internet_service = st.selectbox("Internet", ["Fiber optic", "DSL", "No"])
    payment_method = st.selectbox("Pagamento", ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"])
    
    st.markdown("---")
    
    c1, c2, c3 = st.columns(3)
    online_security = "Yes" if c1.checkbox("Segurança Online") else "No"
    tech_support = "Yes" if c2.checkbox("Suporte Técnico") else "No"
    paperless_billing = "Yes" if c3.checkbox("Fatura Digital") else "No"

    st.write("")
    # REMOVIDO: use_container_width=True (O CSS já resolve isso)
    analisar_btn = st.button("⚡ PROCESSAR ANÁLISE DE RISCO", type="primary")

# --- 5. RESULTADOS E INTEGRAÇÃO ---
with col_result:
    st.subheader(":chart_with_upwards_trend: Diagnóstico da I.A.")
    
    if analisar_btn:
        payload = {
            "tenure": tenure,
            "monthly_charges": monthly_charges,
            "contract": contract,
            "internet_service": internet_service,
            "payment_method": payment_method,
            "online_security": online_security,
            "tech_support": tech_support,
            "paperless_billing": paperless_billing
        }

        try:
            with st.spinner("Conectando ao Núcleo Neural (Java Spring Boot)..."):
                response = requests.post("http://localhost:8080/predict", json=payload)
            
            if response.status_code == 200:
                dados = response.json()
                previsao = dados['previsao']
                probabilidade = dados['probabilidade'] * 100
                
                container = st.container(border=True)
                
                if previsao == "Vai cancelar":
                    container.error("🚨 **ALERTA DE CHURN DETECTADO**")
                    container.markdown(f"### Probabilidade de Evasão: **{probabilidade:.1f}%**")
                    st.toast("Risco Crítico Identificado!", icon="🔥")
                else:
                    container.success("✅ **CLIENTE RETIDO**")
                    container.markdown(f"### Probabilidade de Evasão: **{probabilidade:.1f}%**")
                    st.toast("Cliente Seguro", icon="🛡️")

                st.divider()
                m1, m2 = st.columns(2)
                m1.metric("Status Atual", previsao)
                m2.metric("Score de Risco (0-1)", f"{dados['probabilidade']:.4f}")
                
                st.progress(dados['probabilidade'], text="Termômetro de Risco")

            else:
                st.error(f"Erro na API Java: {response.status_code}")
                st.code(response.text)
                
        except Exception as e:
            st.error("❌ Erro de Conexão")
            st.info("Verifique se o backend Java está rodando na porta 8080.")
            with st.expander("Detalhes do erro"):
                st.write(e)
            
    else:
        st.info("👈 Aguardando dados...")
        # REMOVIDO: use_container_width=True (Deixamos padrão para evitar erro futuro)
        st.image("https://images.unsplash.com/photo-1639322537228-f710d846310a?q=80&w=2232&auto=format&fit=crop", 
                 caption="Nexus Analytics System")