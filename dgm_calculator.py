import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Define as opções para o alvo/filtro
alvo_filtro_options = {
    'Mo/Mo': 1,
    'Mo/Rh': 1.017,
    'Rh/Rh': 1.061,
    'Rh/Al': 1.044,
    'W/Rh': 1.042
}

# --- DICIONÁRIOS GLOBAIS ---

# Dicionário de fórmulas para CSR
formulas_csr = {
    'Mo/Mo': 0.01 * 0 + 0.08, # Valor inicial, será substituído
    'Mo/Rh': 0.0067 * 0 + 0.2333,
    'Rh/Rh': 0.0167 * 0 - 0.0367,
    'W/Rh': 0.0067 * 0 + 0.3533
}

# Dicionário de g_values (Fator G) - Antigo, mantido para evitar NameError se houver outras refs
g_values_old = {
    0.30: [0.390, 0.274, 0.207, 0.183, 0.164, 0.135, 0.114, 0.098, 0.0859, 0.0763, 0.0687],
    0.35: [0.433, 0.309, 0.235, 0.208, 0.187, 0.154, 0.130, 0.112, 0.0981, 0.0873, 0.0783],
    0.40: [0.473, 0.342, 0.261, 0.232, 0.209, 0.172, 0.145, 0.126, 0.1106, 0.0986, 0.0887],
    0.45: [0.509, 0.374, 0.289, 0.258, 0.232, 0.192, 0.163, 0.140, 0.1233, 0.1096, 0.0988],
    0.50: [0.543, 0.406, 0.318, 0.285, 0.258, 0.214, 0.177, 0.154, 0.1357, 0.1207, 0.1088],
    0.55: [0.573, 0.437, 0.346, 0.311, 0.287, 0.236, 0.202, 0.175, 0.1543, 0.1375, 0.1240],
    0.60: [0.587, 0.466, 0.374, 0.339, 0.310, 0.261, 0.224, 0.195, 0.1723, 0.1540, 0.1385],
}

# Tabela Ki
tabela_ki_global = {
    ('Mo/Mo', 26): 0.1357,
    ('Mo/Mo', 27): 0.1530,
    ('Mo/Rh', 29): 0.1540,
    ('Mo/Rh', 31): 0.1830,
}

# Dicionário de fórmulas para Fator C
formulas_fator_c = {
    0.34: {1: lambda e: (0.0004 * e**3) - (0.0105 * e**2) + (0.093 * e) + 0.9449, 2: lambda e: 0.0001 * e**3 - 0.0035 * e**2 + 0.0295 * e + 0.9831, 3: lambda e: -0.0001 * e**3 + 0.0028 * e**2 - 0.0242 * e + 1.0105, 4: lambda e: -0.0005 * e**3 + 0.0103 * e**2 - 0.0773 * e + 1.0343},
    0.35: {1: lambda e: (0.0004 * e**3) - (0.0105 * e**2) + (0.093 * e) + 0.9449, 2: lambda e: 0.0001 * e**3 - 0.0035 * e**2 + 0.0295 * e + 0.9831, 3: lambda e: -0.0001 * e**3 + 0.0028 * e**2 - 0.0242 * e + 1.0105, 4: lambda e: -0.0005 * e**3 + 0.0103 * e**2 - 0.0773 * e + 1.0343},
    0.36: {1: lambda e: 0.0004 * e**3 - 0.0103 * e**2 + 0.0915 * e + 0.9443, 2: lambda e: 0.0002 * e**3 - 0.0044 * e**2 + 0.0338 * e + 0.9768, 3: lambda e: -0.0001 * e**3 + 0.0029 * e**2 - 0.0248 * e + 1.0118, 4: lambda e: -0.0004 * e**3 + 0.0093 * e**2 - 0.0726 * e + 1.03},
    0.37: {1: lambda e: 0.0005 * e**3 - 0.0117 * e**2 + 0.098 * e + 0.9345, 2: lambda e: 0.0002 * e**3 - 0.0041 * e**2 + 0.0325 * e + 0.9783, 3: lambda e: -0.0001 * e**3 + 0.003 * e**2 - 0.0247 * e + 1.0117, 4: lambda e: -0.0004 * e**3 + 0.0091 * e**2 - 0.0718 * e + 1.0304},
    0.38: {1: lambda e: 0.0005 * e**3 - 0.0117 * e**2 + 0.0978 * e + 0.9342, 2: lambda e: 0.0002 * e**3 - 0.0041 * e**2 + 0.0324 * e + 0.9782, 3: lambda e: -0.0001 * e**3 + 0.0031 * e**2 - 0.0252 * e + 1.0126, 4: lambda e: -0.0004 * e**3 + 0.009 * e**2 - 0.0715 * e + 1.0306},
    0.39: {1: lambda e: 0.0005 * e**3 - 0.0116 * e**2 + 0.0974 * e + 0.934, 2: lambda e: 0.0002 * e**3 - 0.0041 * e**2 + 0.0324 * e + 0.9782, 3: lambda e: -0.0001 * e**3 + 0.0031 * e**2 - 0.0251 * e + 1.0126, 4: lambda e: -0.0004 * e**3 + 0.0089 * e**2 - 0.0712 * e + 1.0311},
    0.40: {1: lambda e: 0.0005 * e**3 - 0.0114 * e**2 + 0.0959 * e + 0.9335, 2: lambda e: 0.0002 * e**3 - 0.0041 * e**2 + 0.0322 * e + 0.9779, 3: lambda e: -0.0001 * e**3 + 0.0031 * e**2 - 0.0248 * e + 1.0128, 4: lambda e: -0.0004 * e**3 + 0.0087 * e**2 - 0.0703 * e + 1.0324},
    0.41: {1: lambda e: 0.0007 * e**3 - 0.0154 * e**2 + 0.1207 * e + 0.8822, 2: lambda e: 0.0002 * e**3 - 0.0036 * e**2 + 0.0299 * e + 0.9801, 3: lambda e: -0.0001 * e**3 + 0.0031 * e**2 - 0.0248 * e + 1.0125, 4: lambda e: -0.0004 * e**3 + 0.009 * e**2 - 0.0716 * e + 1.0352},
    0.42: {1: lambda e: 0.0007 * e**3 - 0.0165 * e**2 + 0.1278 * e + 0.8677, 2: lambda e: 0.0001 * e**3 - 0.0034 * e**2 + 0.0293 * e + 0.9807, 3: lambda e: -0.0001 * e**3 + 0.0031 * e**2 - 0.0247 * e + 1.0124, 4: lambda e: -0.0004 * e**3 + 0.0091 * e**2 - 0.0719 * e + 1.0358},
    0.43: {1: lambda e: 0.0008 * e**3 - 0.0177 * e**2 + 0.1349 * e + 0.853, 2: lambda e: 0.0001 * e**3 - 0.0033 * e**2 + 0.0286 * e + 0.9815, 3: lambda e: -0.0001 * e**3 + 0.0031 * e**2 - 0.0247 * e + 1.0124, 4: lambda e: -0.0004 * e**3 + 0.0092 * e**2 - 0.0724 * e + 1.0368},
    0.44: {1: lambda e: 0.0009 * e**3 - 0.0188 * e**2 + 0.1419 * e + 0.8384, 2: lambda e: 0.0001 * e**3 - 0.0032 * e**2 + 0.0279 * e + 0.9822, 3: lambda e: -0.0001 * e**3 + 0.0031 * e**2 - 0.0246 * e + 1.0122, 4: lambda e: -0.0004 * e**3 + 0.0092 * e**2 - 0.0727 * e + 1.0375},
    0.45: {1: lambda e: 0.0011 * e**3 - 0.0229 * e**2 + 0.1669 * e + 0.787, 2: lambda e: 0.00009 * e**3 - 0.0026 * e**2 + 0.0252 * e + 0.9851, 3: lambda e: -0.0001 * e**3 + 0.0029 * e**2 - 0.0238 * e + 1.0109, 4: lambda e: -0.0004 * e**3 + 0.009 * e**2 - 0.0719 * e + 1.0374},
    0.46: {1: lambda e: 0.0007 * e**3 - 0.0162 * e**2 + 0.1292 * e + 0.8523, 2: lambda e: 0.00008 * e**3 - 0.0024 * e**2 + 0.0241 * e + 0.9865, 3: lambda e: -0.0001 * e**3 + 0.0029 * e**2 - 0.0241 * e + 1.0127, 4: lambda e: -0.0004 * e**3 + 0.0087 * e**2 - 0.0706 * e + 1.0377},
    0.47: {1: lambda e: 0.0006 * e**3 - 0.015 * e**2 + 0.1216 * e + 0.8666, 2: lambda e: 0.00008 * e**3 - 0.0024 * e**2 + 0.0238 * e + 0.9869, 3: lambda e: -0.0001 * e**3 + 0.0029 * e**2 - 0.0242 * e + 1.0132, 4: lambda e: -0.0004 * e**3 + 0.0086 * e**2 - 0.07 * e + 1.0375},
    0.48: {1: lambda e: 0.0008 * e**3 - 0.0177 * e**2 + 0.1349 * e + 0.853, 2: lambda e: 0.0008 * e**3 - 0.0177 * e**2 + 0.1349 * e + 0.853, 3: lambda e: 0.0004 * e**3 - 0.0105 * e**2 + 0.093 * e + 1.077, 4: lambda e: -0.0004 * e**3 + 0.0093 * e**2 - 0.0726 * e + 1.03},
    0.50: {1: lambda e: (0.0004 * e**3) - (0.0105 * e**2) + (0.093 * e) + 1.077, 2: lambda e: 0.0008 * e**3 - 0.0177 * e**2 + 0.1349 * e**2 + 0.853, 3: lambda e: 0.0004 * e**3 - (0.0105 * e**2) + (0.093 * e) + 1.077, 4: lambda e: -0.0004 * e**3 + 0.0093 * e**2 - 0.0726 * e + 1.03},
}

# --- FIM DICIONÁRIOS GLOBAIS ---


# Fórmulas para CSR (função)
def calcular_csr(kv, alvo_filtro):
    try:
        kv = float(kv)
        formulas_csr_local = {
            'Mo/Mo': 0.01 * kv + 0.08,
            'Mo/Rh': 0.0067 * kv + 0.2333,
            'Rh/Rh': 0.0167 * kv - 0.0367,
            'W/Rh': 0.0067 * kv + 0.3533
        }
        return round(formulas_csr_local.get(alvo_filtro, "Alvo/filtro inválido"), 2)
    except ValueError:
        return "Entrada inválida para Kv"

# FUNÇÃO calcular_fator_g (mantida como a última versão)
def calcular_fator_g(csr, espessura):
    """
    Calcula o fator g usando a equação polinomial G = a0 + a1*x + a2*x^2 + a3*x^3,
    onde x é a espessura da mama em cm e a0, a1, a2, a3 dependem do CSR.
    """
    try:
        csr = float(csr)
        espessura = float(espessura) 

        a0, a1, a2, a3 = 0, 0, 0, 0

        if csr <= 0.30:
            a0, a1, a2, a3 = 0.6862414, -0.1903851, 0.0211549, -0.0008170
        elif csr <= 0.35:
            a0, a1, a2, a3 = 0.7520924, -0.2040045, 0.0223514, -0.0008553
        elif csr <= 0.40:
            a0, a1, a2, a3 = 0.8135159, -0.2167391, 0.0234949, -0.0008925
        elif csr <= 0.45:
            a0, a1, a2, a3 = 0.8587792, -0.2213542, 0.0235061, -0.0008817
        elif csr <= 0.50:
            a0, a1, a2, a3 = 0.8926865, -0.2192870, 0.0224164, -0.0008171
        elif csr <= 0.55:
            a0, a1, a2, a3 = 0.9237367, -0.2189931, 0.0221241, -0.0008050
        elif csr <= 0.60:
            a0, a1, a2, a3 = 0.9131422, -0.1996713, 0.0190965, -0.0006696
        else:
            return "CSR fora do intervalo suportado para cálculo do fator g."

        fator_g_calculado = (a0 + (a1 * espessura) + (a2 * (espessura**2)) + (a3 * (espessura**3)))
        
        return max(0, round(fator_g_calculado, 4))
    
    except ValueError:
        return "Entrada inválida para cálculo do fator g"

# FUNÇÃO DE GLANDULARIDADE (mantida)
def calcular_glandularidade(idade, espessura_mama_cm):
    """
    Calcula a glandularidade usando a fórmula G = at^3 + bt^2 + ct + k.
    t é a espessura da mama em mm.
    """
    espessura_mama_mm = espessura_mama_cm * 10

    # Define as constantes com base na idade
    if 30 <= idade <= 49:
        a = -0.000196
        b = 0.0666
        c = -7.450000
        k = 278
    elif 50 <= idade <= 54:
        a = -0.000255
        b = 0.0768
        c = -7.670000
        k = 259
    elif 55 <= idade <= 59:
        a = -0.000199
        b = 0.0593
        c = -6.000000
        k = 207
    elif 60 <= idade <= 88:
        a = -0.000186
        b = 0.0572
        c = -5.990000
        k = 208
    else:
        return "Idade fora do intervalo suportado para cálculo de glandularidade (30-88)."

    # Calcula G
    G = (a * (espessura_mama_mm**3)) + (b * (espessura_mama_mm**2)) + (c * espessura_mama_mm) + k
    
    return max(0, round(G, 2))

# Função para calcular o fator C (mantida)
def calcular_fator_c(csr, espessura, glandularidade):
    try:
        espessura = float(espessura)
        glandularidade = float(glandularidade)

        grupo_val = 0
        if glandularidade <= 25:
            grupo_val = 1
        elif glandularidade <= 50:
            grupo_val = 2
        elif glandularidade <= 75:
            grupo_val = 3
        else:
            grupo_val = 4

        # Usa o dicionário global: formulas_fator_c
        csr_aproximado = min(formulas_fator_c.keys(), key=lambda x: abs(x - csr))

        if csr_aproximado not in formulas_fator_c:
            return "CSR fora do intervalo suportado."

        fator_c = formulas_fator_c[csr_aproximado][grupo_val](espessura)
        return round(fator_c, 4)

    except (ValueError, TypeError):
        return "Entrada inválida"

# Função para calcular o Ki (mantida)
def calcular_ki(kv, alvo_filtro, mas, espessura_mama):
    # Usa o dicionário global: tabela_ki_global
    x = tabela_ki_global.get((alvo_filtro, int(kv)), 0)
    
    if x == 0:
        return "Combinação de alvo/filtro e Kv não encontrada na tabela de Ki."
    
    divisor = (63 - espessura_mama)**2
    if divisor == 0:
        return "Erro: A espessura da mama é inválida para o cálculo de Ki (63 - espessura deve ser diferente de zero)."

    return round(((x * mas)*2500) / divisor, 2)

# Função para calcular o DGM (mantida)
def calcular_dgm(ki, s, fator_g, fator_c):
    try:
        dgm = ki * s * fator_g * fator_c
        return round(dgm, 2)
    except (ValueError, TypeError):
        return "Entrada inválida para o cálculo do DGM"

# Funções para Excel Download (mantida)
@st.cache_data
def to_excel(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Resultados DGM')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

# --- Interface Streamlit ---
st.set_page_config(
    page_title="Calculadora de DGM",
    page_icon="🔬",
    layout="centered"
)

st.title("🔬 Calculadora de Dose Glandular Média (DGM)")
st.markdown("Preencha os campos abaixo para calcular a DGM de mamografia.")

# Inicializar st.session_state para armazenar os resultados
if 'resultados_dgm' not in st.session_state:
    st.session_state.resultados_dgm = pd.DataFrame(columns=[
        "Data/Hora", "Idade", "Espessura (cm)", "Alvo/Filtro", "Kv", "mAs",
        "Glandularidade (%)", "Grupo Glandularidade", "Valor s", "CSR", "Fator g", "Fator C", "Ki", "DGM (mGy)"
    ])

# Sidebar para inputs
with st.sidebar:
    st.header("Dados de Entrada")
    idade = st.number_input('Idade:', min_value=1, max_value=120, value=45, help="Idade da paciente (usado para glandularidade automática)")
    espessura_mama = st.number_input('Espessura da Mama (cm):', min_value=1.0, max_value=20.0, value=6.0, step=0.1, help="Espessura da mama comprimida em centímetros")
    alvo_filtro = st.selectbox('Alvo/Filtro:', options=list(alvo_filtro_options.keys()))
    kv = st.number_input('Kv:', min_value=1.0, max_value=50.0, value=28.0, step=0.1)
    mas = st.number_input('mAs:', min_value=0.1, max_value=1000.0, value=50.0, step=0.1)
    
    sabe_glandularidade = st.checkbox("Eu sei a glandularidade (marcar para inserir manualmente)")
    glandularidade_input = None
    if sabe_glandularidade:
        glandularidade_input = st.number_input('Glandularidade (%):', min_value=0.0, max_value=100.0, value=50.0, step=0.1)

# Botão de Cálculo
st.markdown("---")
if st.button("Calcular DGM"):
    st.subheader("Resultados do Cálculo Atual:")

    # --- Cálculo e Exibição de Glandularidade ---
    col1, col2 = st.columns(2)
    glandularidade = None
    with col1:
        if sabe_glandularidade and glandularidade_input is not None:
            glandularidade = glandularidade_input
            st.info(f"**Glandularidade informada:** {glandularidade:.1f}%")
        else:
            glandularidade_calc = calcular_glandularidade(idade, espessura_mama)
            if isinstance(glandularidade_calc, str):
                st.error(f"Erro ao calcular Glandularidade: {glandularidade_calc}")
                # Definir glandularidade para "Erro" ou similar para que cálculos posteriores falhem corretamente
                glandularidade = "Erro" 
            else:
                glandularidade = glandularidade_calc
                st.info(f"**Glandularidade:** {glandularidade:.1f}%") # Exibição única

    # --- Cálculo e Exibição de s ---
    with col2:
        s = alvo_filtro_options.get(alvo_filtro, "Inválido")
        if isinstance(s, str):
            st.error(f"Erro no valor de s: {s}")
            s_val = "Erro"
        else:
            st.info(f"**Valor de s:** {s}")
            s_val = s

    # --- Cálculo e Exibição de CSR e Fator g ---
    col3, col4 = st.columns(2)
    with col3:
        csr = calcular_csr(kv, alvo_filtro)
        if isinstance(csr, str):
            st.error(f"Erro no cálculo de CSR: {csr}")
            csr_val = "Erro"
        else:
            st.info(f"**Valor de CSR:** {csr}")
            csr_val = csr

    with col4:
        fator_g = calcular_fator_g(csr_val, espessura_mama)
        if isinstance(fator_g, str):
            st.error(f"Erro no cálculo do Fator g: {fator_g}")
            fator_g_val = "Erro"
        else:
            st.info(f"**Valor do Fator g:** {fator_g}")
            fator_g_val = fator_g

    # --- REMOVIDAS AS MENSAGENS DE DEBUG ---
    # st.info(f"**Debug Fator C - CSR:** {csr_val} (tipo: {type(csr_val)})")
    # st.info(f"**Debug Fator C - Glandularidade:** {glandularidade} (tipo: {type(glandularidade)})")

    # --- Cálculo e Exibição de Fator C e Ki ---
    col5, col6 = st.columns(2)
    
    grupo_glandularidade_val = "Não calculado"
    if isinstance(glandularidade, (int, float)):
        if glandularidade <= 25:
            grupo_glandularidade_val = 1
        elif glandularidade <= 50:
            grupo_glandularidade_val = 2
        elif glandularidade <= 75:
            grupo_glandularidade_val = 3
        else:
            grupo_glandularidade_val = 4

    with col5:
        fator_c = "Não calculado"
        fator_c_val = "Erro"
        if isinstance(csr_val, (int, float)) and isinstance(glandularidade, (int, float)):
            csr_possiveis_fator_c = list(formulas_fator_c.keys()) 
            csr_para_c = min(csr_possiveis_fator_c, key=lambda x: abs(x - csr_val))

            fator_c_calc = calcular_fator_c(csr_para_c, espessura_mama, glandularidade)

            if isinstance(fator_c_calc, str):
                st.error(f"Erro no cálculo do Fator C: {fator_c_calc}")
            else:
                fator_c = fator_c_calc
                st.info(f"**Valor do Fator C:** {fator_c}") # Exibição única
                fator_c_val = fator_c
        else:
            st.warning("Fator C não calculado devido a entradas inválidas de CSR ou Glandularidade.")

    with col6:
        ki = calcular_ki(kv, alvo_filtro, mas, espessura_mama)
        if isinstance(ki, str):
            st.error(f"Erro no cálculo de Ki: {ki}")
            ki_val = "Erro"
        else:
            st.info(f"**Valor de Ki:** {ki}")
            ki_val = ki

    # --- Cálculo e Exibição final da DGM ---
    st.markdown("---")
    dgm_val = "Erro"
    if all(isinstance(val, (int, float)) for val in [ki_val, s_val, fator_g_val, fator_c_val]):
        dgm = calcular_dgm(ki_val, s_val, fator_g_val, fator_c_val)
        st.success(f"**Valor da DGM:** {dgm} mGy")
        dgm_val = dgm
    else:
        st.error("Não foi possível calcular a DGM devido a erros nos valores anteriores.")

    # Armazenar resultados na sessão
    if dgm_val != "Erro":
        nova_linha = {
            "Data/Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Idade": idade,
            "Espessura (cm)": espessura_mama,
            "Alvo/Filtro": alvo_filtro,
            "Kv": kv,
            "mAs": mas,
            "Glandularidade (%)": glandularidade,
            "Grupo Glandularidade": grupo_glandularidade_val,
            "Valor s": s_val,
            "CSR": csr_val,
            "Fator g": fator_g_val,
            "Fator C": fator_c_val,
            "Ki": ki_val,
            "DGM (mGy)": dgm_val
        }
        st.session_state.resultados_dgm = pd.concat([st.session_state.resultados_dgm, pd.DataFrame([nova_linha])], ignore_index=True)

# --- (Mantenha a exibição do Histórico e botões de download/limpeza) ---
st.markdown("---")
st.subheader("Histórico de Cálculos:")

if not st.session_state.resultados_dgm.empty:
    st.dataframe(st.session_state.resultados_dgm, use_container_width=True)
    
    excel_data = to_excel(st.session_state.resultados_dgm)
    st.download_button(
        label="📥 Baixar Resultados como Excel",
        data=excel_data,
        file_name=f"resultados_dgm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    if st.button("Limpar Histórico"):
        st.session_state.resultados_dgm = pd.DataFrame(columns=[
            "Data/Hora", "Idade", "Espessura (cm)", "Alvo/Filtro", "Kv", "mAs",
            "Glandularidade (%)", "Grupo Glandularidade", "Valor s", "CSR", "Fator g", "Fator C", "Ki", "DGM (mGy)"
        ])
        st.experimental_rerun()
else:
    st.info("Nenhum cálculo realizado ainda. Os resultados aparecerão aqui.")

st.markdown("---")
st.markdown("Desenvolvido por você, com o auxílio de um modelo de linguagem.")
