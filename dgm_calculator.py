import streamlit as st
import pandas as pd
from datetime import datetime
import io
import math # Para sqrt

# Define as opções para o alvo/filtro
alvo_filtro_options = {
    'Mo/Mo': 1,
    'Mo/Rh': 1.017,
    'Rh/Rh': 1.061,
    'Rh/Al': 1.044,
    'W/Rh':  1.042
}

# --- DICIONÁRIOS GLOBAIS E CONSTANTES DE INCERTEZA ---

# Coeficientes para CSR (para calculo e derivada)
csr_coeffs = {
    'Mo/Mo': {'a': 0.01, 'b': 0.08},
    'Mo/Rh': {'a': 0.0067, 'b': 0.2333},
    'Rh/Rh': {'a': 0.0167, 'b': -0.0367},
    'W/Rh':  {'a': 0.0067, 'b': 0.3533}
}

# Tabela Ki do IRD (restaurada para os valores originais e limitados)
tabela_ki_ird = {
    ('Mo/Mo', 26): 0.1357,
    ('Mo/Mo', 27): 0.1530,
    ('Mo/Rh', 29): 0.1540,
    ('Mo/Rh', 31): 0.1830,
}

# Tabela Ki da UFRJ (dados fornecidos na última mensagem)
tabela_ki_ufrj = {
    ('Mo/Mo', 25): 0.119094303,
    ('Mo/Mo', 26): 0.136888667,
    ('Mo/Mo', 27): 0.155258424,
    ('Mo/Mo', 28): 0.175158485,
    ('Mo/Rh', 26): 0.114301394,
    ('Mo/Rh', 27): 0.131012303,
    ('Mo/Rh', 28): 0.148476121,
    ('Mo/Rh', 29): 0.166423515,
    ('Rh/Rh', 28): 0.126825394,
    ('Rh/Rh', 29): 0.142299818,
    ('Rh/Rh', 30): 0.158490424,
    ('Rh/Rh', 31): 0.175164606,
}

# Dicionário para selecionar a tabela Ki com base no local
tabelas_ki_por_local = {
    'IRD': tabela_ki_ird,
    'UFRJ': tabela_ki_ufrj,
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

# Constantes e Incertezas das constantes do Fator G (da0, da1, da2, da3)
# Estes valores são fixos para cada faixa de CSR e serão usados no calcular_fator_g
FATOR_G_CONSTANTS_UNCERTAINTIES = {
    0.30: {'a0': 0.6862414, 'da0': 0.0215771, 'a1': -0.1903851, 'da1': 0.0122059, 'a2': 0.0211549, 'da2': 0.0020598, 'a3': -0.0008170, 'da3': 0.0001055},
    0.35: {'a0': 0.7520924, 'da0': 0.0214658, 'a1': -0.2040045, 'da1': 0.0121429, 'a2': 0.0223514, 'da2': 0.0020492, 'a3': -0.0008553, 'da3': 0.0001050},
    0.40: {'a0': 0.8135159, 'da0': 0.0208152, 'a1': -0.2167391, 'da1': 0.0117749, 'a2': 0.0234949, 'da2': 0.0019871, 'a3': -0.0008925, 'da3': 0.0001018},
    0.45: {'a0': 0.8587792, 'da0': 0.02030096, 'a1': -0.2213542, 'da1': 0.01148395, 'a2': 0.0235061, 'da2': 0.00193800, 'a3': -0.0008817, 'da3': 0.00009929},
    0.50: {'a0': 0.8926865, 'da0': 0.0192286, 'a1': -0.2192870, 'da1': 0.0108773, 'a2': 0.0224164, 'da2': 0.0018356, 'a3': -0.0008171, 'da3': 0.0000940},
    0.55: {'a0': 0.9237367, 'da0': 0.0184259, 'a1': -0.2189931, 'da1': 0.0104233, 'a2': 0.0221241, 'da2': 0.0017590, 'a3': -0.0008050, 'da3': 0.0000901},
    0.60: {'a0': 0.9131422, 'da0': 0.0097610, 'a1': -0.1996713, 'da1': 0.0055217, 'a2': 0.0190965, 'da2': 0.0009318, 'a3': -0.0006696, 'da3': 0.0000477},
}

# Incertezas das entradas (em porcentagem do valor)
INCERTEZA_KV_PERCENTUAL = 0.01  # ±1%
INCERTEZA_MAS_PERCENTUAL = 0.05 # ±5%
INCERTEZA_ESPESSURA_PERCENTUAL = 0.05 # ±5% (considerando 1 a 2mm como 2% a 5% de 2 a 11cm)
INCERTEZA_X_KI_PERCENTUAL = 0.02 # ±2% para os valores de 'x' na tabela Ki
INCERTEZA_COEFS_FATOR_C_PERCENTUAL = 0.05 # ±5% para os coeficientes das fórmulas do Fator C

# --- FIM DICIONÁRIOS GLOBAIS E CONSTANTES DE INCERTEZA ---

# --- FUNÇÃO GENÉRICA DE PROPAGAÇÃO DE INCERTEZAS (MANUAL) ---
def propagate_uncertainty(value_func, uncertainty_terms):
    """
    Calcula a incerteza propagada usando a fórmula da raiz quadrada da soma dos quadrados (RSS).
    Args:
        value_func (callable): Uma função que retorna o valor da medida.
        uncertainty_terms (list of tuples): Lista de (derivada_parcial, incerteza_da_entrada).
            A derivada parcial deve ser o valor numérico avaliado.
    Returns:
        float: A incerteza propagada.
    """
    sum_of_squares = 0
    for partial_deriv, input_uncertainty in uncertainty_terms:
        sum_of_squares += (partial_deriv * input_uncertainty)**2
    
    return math.sqrt(sum_of_squares)

# --- FIM FUNÇÃO GENÉRICA DE PROPAGAÇÃO DE INCERTEZAS ---

# Função auxiliar para extrair coeficientes do Fator C.
# Movida para o escopo global para resolver o NameError.
def get_coeffs_from_lambda_for_fator_c(csr_key, group_key):
    coeffs_map = {
        0.34: {
            1: {'a': 0.0004, 'b': -0.0105, 'c': 0.093, 'd': 0.9449},
            2: {'a': 0.0001, 'b': -0.0035, 'c': 0.0295, 'd': 0.9831},
            3: {'a': -0.0001, 'b': 0.0028, 'c': -0.0242, 'd': 1.0105},
            4: {'a': -0.0005, 'b': 0.0103, 'c': -0.0773, 'd': 1.0343}
        },
        0.35: {
            1: {'a': 0.0004, 'b': -0.0105, 'c': 0.093, 'd': 0.9449},
            2: {'a': 0.0001, 'b': -0.0035, 'c': 0.0295, 'd': 0.9831},
            3: {'a': -0.0001, 'b': 0.0028, 'c': -0.0242, 'd': 1.0105},
            4: {'a': -0.0005, 'b': 0.0103, 'c': -0.0773, 'd': 1.0343}
        },
        0.36: {
            1: {'a': 0.0004, 'b': -0.0103, 'c': 0.0915, 'd': 0.9443},
            2: {'a': 0.0002, 'b': -0.0044, 'c': 0.0338, 'd': 0.9768},
            3: {'a': -0.0001, 'b': 0.0029, 'c': -0.0248, 'd': 1.0118},
            4: {'a': -0.0004, 'b': 0.0093, 'c': -0.0726, 'd': 1.03}
        },
        0.37: {
            1: {'a': 0.0005, 'b': -0.0117, 'c': 0.098, 'd': 0.9345},
            2: {'a': 0.0002, 'b': -0.0041, 'c': 0.0325, 'd': 0.9783},
            3: {'a': -0.0001, 'b': 0.003, 'c': -0.0247, 'd': 1.0117},
            4: {'a': -0.0004, 'b': 0.0091, 'c': -0.0718, 'd': 1.0304}
        },
        0.38: {
            1: {'a': 0.0005, 'b': -0.0117, 'c': 0.0978, 'd': 0.9342},
            2: {'a': 0.0002, 'b': -0.0041, 'c': 0.0324, 'd': 0.9782},
            3: {'a': -0.0001, 'b': 0.0031, 'c': -0.0252, 'd': 1.0126},
            4: {'a': -0.0004, 'b': 0.009, 'c': -0.0715, 'd': 1.0306}
        },
        0.39: {
            1: {'a': 0.0005, 'b': -0.0116, 'c': 0.0974, 'd': 0.934},
            2: {'a': 0.0002, 'b': -0.0041, 'c': 0.0324, 'd': 0.9782},
            3: {'a': -0.0001, 'b': 0.0031, 'c': -0.0251, 'd': 1.0126},
            4: {'a': -0.0004, 'b': 0.0089, 'c': -0.0712, 'd': 1.0311}
        },
        0.40: {
            1: {'a': 0.0005, 'b': -0.0114, 'c': 0.0959, 'd': 0.9335},
            2: {'a': 0.0002, 'b': -0.0041, 'c': 0.0322, 'd': 0.9779},
            3: {'a': -0.0001, 'b': 0.0031, 'c': -0.0248, 'd': 1.0128},
            4: {'a': -0.0004, 'b': 0.0087, 'c': -0.0703, 'd': 1.0324}
        },
        0.41: {
            1: {'a': 0.0007, 'b': -0.0154, 'c': 0.1207, 'd': 0.8822},
            2: {'a': 0.0002, 'b': -0.0036, 'c': 0.0299, 'd': 0.9801},
            3: {'a': -0.0001, 'b': 0.0031, 'c': -0.0248, 'd': 1.0125},
            4: {'a': -0.0004, 'b': 0.009, 'c': -0.0716, 'd': 1.0352}
        },
        0.42: {
            1: {'a': 0.0007, 'b': -0.0165, 'c': 0.1278, 'd': 0.8677},
            2: {'a': 0.0001, 'b': -0.0034, 'c': 0.0293, 'd': 0.9807},
            3: {'a': -0.0001, 'b': 0.0031, 'c': -0.0247, 'd': 1.0124},
            4: {'a': -0.0004, 'b': 0.0091, 'c': -0.0719, 'd': 1.0358}
        },
        0.43: {
            1: {'a': 0.0008, 'b': -0.0177, 'c': 0.1349, 'd': 0.853},
            2: {'a': 0.0001, 'b': -0.0033, 'c': 0.0286, 'd': 0.9815},
            3: {'a': -0.0001, 'b': 0.0031, 'c': -0.0247, 'd': 1.0124},
            4: {'a': -0.0004, 'b': 0.0092, 'c': -0.0724, 'd': 1.0368}
        },
        0.44: {
            1: {'a': 0.0009, 'b': -0.0188, 'c': 0.1419, 'd': 0.8384},
            2: {'a': 0.0001, 'b': -0.0032, 'c': 0.0279, 'd': 0.9822},
            3: {'a': -0.0001, 'b': 0.0031, 'c': -0.0246, 'd': 1.0122},
            4: {'a': -0.0004, 'b': 0.0092, 'c': -0.0727, 'd': 1.0375}
        },
        0.45: {
            1: {'a': 0.0011, 'b': -0.0229, 'c': 0.1669, 'd': 0.787},
            2: {'a': 0.00009, 'b': -0.0026, 'c': 0.0252, 'd': 0.9851},
            3: {'a': -0.0001, 'b': 0.0029, 'c': -0.0238, 'd': 1.0109},
            4: {'a': -0.0004, 'b': 0.009, 'c': -0.0719, 'd': 1.0374}
        },
        0.46: {
            1: {'a': 0.0007, 'b': -0.0162, 'c': 0.1292, 'd': 0.8523},
            2: {'a': 0.00008, 'b': -0.0024, 'c': 0.0241, 'd': 0.9865},
            3: {'a': -0.0001, 'b': 0.0029, 'c': -0.0241, 'd': 1.0127},
            4: {'a': -0.0004, 'b': 0.0087, 'c': -0.0706, 'd': 1.0377}
        },
        0.47: {
            1: {'a': 0.0006, 'b': -0.015, 'c': 0.1216, 'd': 0.8666},
            2: {'a': 0.00008, 'b': -0.0024, 'c': 0.0238, 'd': 0.9869},
            3: {'a': -0.0001, 'b': 0.0029, 'c': -0.0242, 'd': 1.0132},
            4: {'a': -0.0004, 'b': 0.0086, 'c': -0.07, 'd': 1.0375}
        },
        0.48: {
            1: {'a': 0.0008, 'b': -0.0177, 'c': 0.1349, 'd': 0.853},
            2: {'a': 0.0008, 'b': -0.0177, 'c': 0.1349, 'd': 0.853}, # Duplicado, verificar no original se é intencional
            3: {'a': 0.0004, 'b': -0.0105, 'c': 0.093, 'd': 1.077},
            4: {'a': -0.0004, 'b': 0.0093, 'c': -0.0726, 'd': 1.03}
        },
        0.50: {
            1: {'a': 0.0004, 'b': -0.0105, 'c': 0.093, 'd': 1.077},
            2: {'a': 0.0008, 'b': -0.0177, 'c': 0.1349, 'd': 0.853},
            3: {'a': 0.0004, 'b': -0.0105, 'c': 0.093, 'd': 1.077},
            4: {'a': -0.0004, 'b': 0.0093, 'c': -0.0726, 'd': 1.03}
        },
    }
    return coeffs_map.get(csr_key, {}).get(group_key, None)


# Fórmulas para CSR (função)
def calcular_csr(kv_val, alvo_filtro, d_kv_abs):
    try:
        const_a = csr_coeffs.get(alvo_filtro)['a']
        const_b = csr_coeffs.get(alvo_filtro)['b']
        
        csr_val = round(const_a * kv_val + const_b, 2)

        # Derivada parcial de CSR em relação a Kv é 'const_a'
        partial_deriv_kv = const_a
        
        incerteza_csr = propagate_uncertainty(
            lambda: csr_val,
            [(partial_deriv_kv, d_kv_abs)]
        )

        return csr_val, round(incerteza_csr, 4)
    except Exception: # Captura qualquer erro, incluindo se alvo/filtro for inválido
        return "Erro CSR", 0.0


# FUNÇÃO calcular_fator_g
def calcular_fator_g(csr_val, espessura_val, d_espessura_abs):
    """
    Calcula o fator g e sua incerteza.
    """
    try:
        a0, a1, a2, a3 = 0, 0, 0, 0
        da0, da1, da2, da3 = 0, 0, 0, 0 # Incertezas das constantes

        # Encontra a faixa de CSR mais próxima para obter as constantes
        # Usamos FATOR_G_CONSTANTS_UNCERTAINTIES porque ela já tem todos os dados
        csr_keys = list(FATOR_G_CONSTANTS_UNCERTAINTIES.keys())
        csr_aproximado_key = min(csr_keys, key=lambda x: abs(x - csr_val))
        
        constants_data = FATOR_G_CONSTANTS_UNCERTAINTIES.get(csr_aproximado_key)

        if not constants_data:
            return "CSR fora do intervalo suportado para cálculo do fator g.", 0.0

        a0, da0 = constants_data['a0'], constants_data['da0']
        a1, da1 = constants_data['a1'], constants_data['da1']
        a2, da2 = constants_data['a2'], constants_data['da2']
        a3, da3 = constants_data['a3'], constants_data['da3']

        # Valor numérico do Fator g
        fator_g_calculado = (a0 + (a1 * espessura_val) + (a2 * (espessura_val**2)) + (a3 * (espessura_val**3)))
        fator_g_val = max(0, round(fator_g_calculado, 4))

        # Calcula as derivadas parciais manualmente
        # f(x, a0, a1, a2, a3) = a0 + a1*x + a2*x^2 + 3*a3*x^2
        # Derivada em relação a x (espessura_val): a1 + 2*a2*x + 3*a3*x^2
        partial_deriv_espessura = a1 + 2*a2*espessura_val + 3*a3*espessura_val**2
        # Derivada em relação a a0: 1
        partial_deriv_a0 = 1
        # Derivada em relação a a1: x
        partial_deriv_a1 = espessura_val
        # Derivada em relação a a2: x^2
        partial_deriv_a2 = espessura_val**2
        # Derivada em relação a a3: x^3
        partial_deriv_a3 = espessura_val**3

        incerteza_fator_g = propagate_uncertainty(
            lambda: fator_g_val, # O valor da função
            [
                (partial_deriv_espessura, d_espessura_abs),
                (partial_deriv_a0, da0),
                (partial_deriv_a1, da1),
                (partial_deriv_a2, da2),
                (partial_deriv_a3, da3)
            ]
        )

        return fator_g_val, round(incerteza_fator_g, 4)
    
    except Exception: # Captura qualquer erro
        return "Erro Fator g", 0.0

# FUNÇÃO DE GLANDULARIDADE (incerteza não propagada aqui, assumida como exata)
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

# Função para calcular o fator C (com incerteza)
def calcular_fator_c(csr, espessura, glandularidade, d_espessura_abs):
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
            return "CSR fora do intervalo suportado.", 0.0

        coeffs = get_coeffs_from_lambda_for_fator_c(csr_aproximado, grupo_val)
        if not coeffs:
            return "Erro: Coeficientes do Fator C não encontrados.", 0.0

        a, b, c, d = coeffs['a'], coeffs['b'], coeffs['c'], coeffs['d']
        
        fator_c_val = (a * espessura**3) + (b * espessura**2) + (c * espessura) + d
        fator_c_val = round(fator_c_val, 4)

        # Incertezas absolutas dos coeficientes
        da = a * INCERTEZA_COEFS_FATOR_C_PERCENTUAL
        db = b * INCERTEZA_COEFS_FATOR_C_PERCENTUAL
        dc = c * INCERTEZA_COEFS_FATOR_C_PERCENTUAL
        dd = d * INCERTEZA_COEFS_FATOR_C_PERCENTUAL

        # Derivadas parciais de Fator C = a*e^3 + b*e^2 + c*e + d
        partial_deriv_espessura = (3 * a * espessura**2) + (2
