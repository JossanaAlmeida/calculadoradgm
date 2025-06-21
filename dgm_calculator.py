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

# Fórmulas para CSR
def calcular_csr(kv, alvo_filtro):
    try:
        kv = float(kv)
        formulas = {
            'Mo/Mo': 0.01 * kv + 0.08,
            'Mo/Rh': 0.0067 * kv + 0.2333,
            'Rh/Rh': 0.0167 * kv - 0.0367,
            'W/Rh': 0.0067 * kv + 0.3533
        }
        return round(formulas.get(alvo_filtro, "Alvo/filtro inválido"), 2)
    except ValueError:
        return "Entrada inválida para Kv"

# Função para calcular o fator g
def calcular_fator_g(csr, espessura):
    try:
        csr = float(csr)
        espessura = int(espessura)

        g_values = {
            0.30: [0.390, 0.274, 0.207, 0.183, 0.164, 0.135, 0.114, 0.098, 0.0859, 0.0763, 0.0687],
            0.35: [0.433, 0.309, 0.235, 0.208, 0.187, 0.154, 0.130, 0.112, 0.0981, 0.0873, 0.0783],
            0.40: [0.473, 0.342, 0.261, 0.232, 0.209, 0.172, 0.145, 0.126, 0.1106, 0.0986, 0.0887],
        }

        espessuras_cm = [2, 3, 4, 4.5, 5, 6, 7, 8, 9, 10, 11]
        csr_proximo = min(g_values, key=lambda x: abs(x - csr))

        try:
            indice_espessura = espessuras_cm.index(espessura)
            return g_values[csr_proximo][indice_espessura]
        except ValueError:
            return "Espessura da mama inválida"
    except ValueError:
        return "Entrada inválida"

# Função para calcular a glandularidade
def calcular_glandularidade(idade, espessura_mama):
    espessuras_cm = [2, 3, 4, 4.5, 5, 6, 7, 8, 9, 10, 11]
    if 40 <= idade <= 49:
        porcentagens = [100, 82, 65, 49, 35, 24, 14, 8, 5, 5, 5]
    elif 50 <= idade <= 64:
        porcentagens = [100, 72, 50, 33, 21, 12, 7, 4, 3, 3, 3]
    else:
        return "Idade fora do intervalo considerado."

    try:
        indice_espessura = espessuras_cm.index(espessura_mama)
        return porcentagens[indice_espessura]
    except ValueError:
        return "Espessura da mama inválida."

# Função para calcular o fator C
def calcular_fator_c(csr, espessura, glandularidade):
    try:
        espessura = float(espessura)
        glandularidade = float(glandularidade)

        if glandularidade <= 25:
            grupo = 1
        elif glandularidade <= 50:
            grupo = 2
        elif glandularidade <= 75:
            grupo = 3
        else:
            grupo = 4

        formulas = {
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

# --- FIM DICIONÁRIOS GLOBAIS E CONSTANTES DE INCERTEZA ---


# --- FUNÇÃO GENÉRICA DE PROPAGAÇÃO DE INCERTEZAS (USANDO SYMPY) ---
@st.cache_data
def calcular_incerteza_propagada(func_expr, value_dict, uncertainty_dict):
    """
    Calcula a incerteza propagada usando a fórmula da raiz quadrada da soma dos quadrados.
    Args:
        func_expr (sympy.Expr): A expressão simbólica da função.
        value_dict (dict): Dicionário de {símbolo: valor numérico}.
        uncertainty_dict (dict): Dicionário de {símbolo: incerteza numérica}.
    Returns:
        float: A incerteza propagada.
    """
    sum_of_squares = 0
    for var in func_expr.free_symbols:
        if var in uncertainty_dict and var in value_dict:
            # Calcula a derivada parcial
            partial_derivative = diff(func_expr, var)
            # Avalia a derivada parcial nos valores numéricos
            partial_derivative_val = partial_derivative.subs(value_dict)
            
            # Adiciona o termo ao somatório
            sum_of_squares += (partial_derivative_val * uncertainty_dict[var])**2
    
    return float(sqrt(sum_of_squares))
# --- FIM FUNÇÃO GENÉRICA DE PROPAGAÇÃO DE INCERTEZAS ---

# Fórmulas para CSR (função)
def calcular_csr(kv_val, alvo_filtro, d_kv):
    try:
        kv_sym = symbols('kv')
        const_a = formulas_csr.get(alvo_filtro)
        const_k = offsets_csr.get(alvo_filtro)
        if const_a is None or const_k is None:
            return "Alvo/filtro inválido", 0.0

        csr_expr = const_a * kv_sym + const_k
        csr_val = round(csr_expr.subs(kv_sym, kv_val), 2)

        uncertainties = {kv_sym: d_kv}
        values = {kv_sym: kv_val}
        incerteza_csr = calcular_incerteza_propagada(csr_expr, values, uncertainties)

        return csr_val, round(incerteza_csr, 4)
    except ValueError:
        return "Entrada inválida para Kv", 0.0

# FUNÇÃO calcular_fator_g
def calcular_fator_g(csr_val, espessura_val, d_espessura, d_a0, d_a1, d_a2, d_a3):
    """
    Calcula o fator g e sua incerteza.
    """
    try:
        csr_sym, espessura_sym, a0_sym, a1_sym, a2_sym, a3_sym = symbols('csr espessura a0 a1 a2 a3')

        a0, a1, a2, a3 = 0, 0, 0, 0
        if csr_val <= 0.30:
            a0, d_a0_val = 0.6862414, d_a0
            a1, d_a1_val = -0.1903851, d_a1
            a2, d_a2_val = 0.0211549, d_a2
            a3, d_a3_val = -0.0008170, d_a3
        elif csr_val <= 0.35:
            a0, d_a0_val = 0.7520924, d_a0
            a1, d_a1_val = -0.2040045, d_a1
            a2, d_a2_val = 0.0223514, d_a2
            a3, d_a3_val = -0.0008553, d_a3
        elif csr_val <= 0.40:
            a0, d_a0_val = 0.8135159, d_a0
            a1, d_a1_val = -0.2167391, d_a1
            a2, d_a2_val = 0.0234949, d_a2
            a3, d_a3_val = -0.0008925, d_a3
        elif csr_val <= 0.45:
            a0, d_a0_val = 0.8587792, d_a0
            a1, d_a1_val = -0.2213542, d_a1
            a2, d_a2_val = 0.0235061, d_a2
            a3, d_a3_val = -0.0008817, d_a3
        elif csr_val <= 0.50:
            a0, d_a0_val = 0.8926865, d_a0
            a1, d_a1_val = -0.2192870, d_a1
            a2, d_a2_val = 0.0224164, d_a2
            a3, d_a3_val = -0.0008171, d_a3
        elif csr_val <= 0.55:
            a0, d_a0_val = 0.9237367, d_a0
            a1, d_a1_val = -0.2189931, d_a1
            a2, d_a2_val = 0.0221241, d_a2
            a3, d_a3_val = -0.0008050, d_a3
        elif csr_val <= 0.60:
            a0, d_a0_val = 0.9131422, d_a0
            a1, d_a1_val = -0.1996713, d_a1
            a2, d_a2_val = 0.0190965, d_a2
            a3, d_a3_val = -0.0006696, d_a3
        else:
            return "CSR fora do intervalo suportado para cálculo do fator g.", 0.0

        fator_g_expr = a0_sym + a1_sym * espessura_sym + a2_sym * espessura_sym**2 + a3_sym * espessura_sym**3
        fator_g_calculado = (a0 + (a1 * espessura_val) + (a2 * (espessura_val**2)) + (a3 * (espessura_val**3)))
        fator_g_val = max(0, round(fator_g_calculado, 4))

        uncertainties = {
            espessura_sym: d_espessura,
            a0_sym: d_a0_val,
            a1_sym: d_a1_val,
            a2_sym: d_a2_val,
            a3_sym: d_a3_val
        }
        values = {
            espessura_sym: espessura_val,
            a0_sym: a0,
            a1_sym: a1,
            a2_sym: a2,
            a3_sym: a3
        }
        incerteza_fator_g = calcular_incerteza_propagada(fator_g_expr, values, uncertainties)

        return fator_g_val, round(incerteza_fator_g, 4)
    
    except ValueError:
        return "Entrada inválida para o cálculo do fator g", 0.0

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

# Função para calcular o fator C (incerteza não propagada aqui, assumida como exata)
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

        csr_aproximado = min(formulas_fator_c.keys(), key=lambda x: abs(x - csr))

        if csr_aproximado not in formulas_fator_c:
            return "CSR fora do intervalo suportado."

        fator_c = formulas_fator_c[csr_aproximado][grupo_val](espessura)
        return round(fator_c, 4)

    except (ValueError, TypeError):
        return "Entrada inválida"

# Função para calcular o Ki (incerteza não propagada aqui, assumida como exata)
def calcular_ki(kv, alvo_filtro, mas, espessura_mama):
    x = tabela_ki_global.get((alvo_filtro, int(kv)), 0)
    
    if x == 0:
        return "Combinação de alvo/filtro e Kv não encontrada na tabela de Ki."
    
    divisor = (63 - espessura_mama)**2
    if divisor == 0:
        return "Erro: A espessura da mama é inválida para o cálculo de Ki (63 - espessura deve ser diferente de zero)."

    return round(((x * mas)*2500) / divisor, 2)

# --- FUNÇÃO calcular_dgm (AGORA RETORNA VALOR E INCERTEZA) ---
def calcular_dgm(ki, s, fator_g, fator_c, incerteza_ki, incerteza_s, incerteza_fator_g, incerteza_fator_c):
    try:
        # Define símbolos para SymPy
        ki_sym, s_sym, fg_sym, fc_sym = symbols('ki s fg fc')
        
        # Expressão simbólica para a DGM
        dgm_expr = ki_sym * s_sym * fg_sym * fc_sym
        
        # Valor numérico da DGM
        dgm = ki * s * fator_g * fator_c
        
        # Calcula incerteza da DGM
        uncertainties = {
            ki_sym: incerteza_ki,
            s_sym: incerteza_s,
            fg_sym: incerteza_fator_g,
            fc_sym: incerteza_fator_c
        }
        values = {
            ki_sym: ki,
            s_sym: s,
            fg_sym: fator_g,
            fc_sym: fator_c
        }
        incerteza_dgm = calcular_incerteza_propagada(dgm_expr, values, uncertainties)

        return round(dgm, 2), round(incerteza_dgm, 4)
    except (ValueError, TypeError):
        return "Entrada inválida para o cálculo do DGM", 0.0
# --- FIM FUNÇÃO calcular_dgm ---

# Funções para Exportação (CSV)
@st.cache_data
def to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

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
        "Glandularidade (%)", "Grupo Glandularidade", "Valor s", "CSR", "Fator g", "Fator C", "Ki",
        "DGM (mGy)", "Incerteza DGM (mGy)" # Nova coluna para incerteza
    ])

# Sidebar para inputs
with st.sidebar:
    st.header("Dados de Entrada")
    idade = st.number_input('Idade:', min_value=1, max_value=120, value=45, help="Idade da paciente (usado para glandularidade automática)")
    espessura_mama = st.number_input('Espessura da Mama (cm):', min_value=1.0, max_value=20.0, value=6.0, step=0.1, help="Espessura da mama comprimida em centímetros")
    alvo_filtro = st.selectbox('Alvo/Filtro:', options=list
