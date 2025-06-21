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
    'W/Rh': 1.042
}

# --- DICIONÁRIOS GLOBAIS E CONSTANTES DE INCERTEZA ---

# Coeficientes para CSR (para calculo e derivada)
csr_coeffs = {
    'Mo/Mo': {'a': 0.01, 'b': 0.08},
    'Mo/Rh': {'a': 0.0067, 'b': 0.2333},
    'Rh/Rh': {'a': 0.0167, 'b': -0.0367},
    'W/Rh':  {'a': 0.0067, 'b': 0.3533}
}

# Tabela Ki
tabela_ki_global = {
    ('Mo/Mo', 26): 0.1357,
    ('Mo/Mo', 27): 0.1530,
    ('Mo/Rh', 29): 0.1540,
    ('Mo/Rh', 31): 0.1830,
}

# Incerteza do valor 'x' da tabela Ki
INCERTEZA_KI_X_PERCENTUAL = 0.02 # ±2%

# Dicionário de fórmulas para Fator C e suas incertezas nas constantes
# Cada lambda representa a função C(e) para um grupo e CSR
# Para cada constante (0.0004, -0.0105, 0.093, 0.9449, etc.), a incerteza será 5% do seu valor.
formulas_fator_c_details = {
    0.34: {
        1: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0004, 'c1': -0.0105, 'c2': 0.093, 'c3': 0.9449}},
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0001, 'c1': -0.0035, 'c2': 0.0295, 'c3': 0.9831}},
        3: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0001, 'c1': 0.0028, 'c2': -0.0242, 'c3': 1.0105}},
        4: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0005, 'c1': 0.0103, 'c2': -0.0773, 'c3': 1.0343}},
    },
    0.35: {
        1: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0004, 'c1': -0.0105, 'c2': 0.093, 'c3': 0.9449}},
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0001, 'c1': -0.0035, 'c2': 0.0295, 'c3': 0.9831}},
        3: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0001, 'c1': 0.0028, 'c2': -0.0242, 'c3': 1.0105}},
        4: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0005, 'c1': 0.0103, 'c2': -0.0773, 'c3': 1.0343}},
    },
    0.36: {
        1: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0004, 'c1': -0.0103, 'c2': 0.0915, 'c3': 0.9443}},
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0002, 'c1': -0.0044, 'c2': 0.0338, 'c3': 0.9768}},
        3: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0001, 'c1': 0.0029, 'c2': -0.0248, 'c3': 1.0118}},
        4: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0004, 'c1': 0.0093, 'c2': -0.0726, 'c3': 1.03}},
    },
    0.37: {
        1: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0005, 'c1': -0.0117, 'c2': 0.098, 'c3': 0.9345}},
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0002, 'c1': -0.0041, 'c2': 0.0325, 'c3': 0.9783}},
        3: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0001, 'c1': 0.003, 'c2': -0.0247, 'c3': 1.0117}},
        4: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0004, 'c1': 0.0091, 'c2': -0.0718, 'c3': 1.0304}},
    },
    0.38: {
        1: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0005, 'c1': -0.0117, 'c2': 0.0978, 'c3': 0.9342}},
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0002, 'c1': -0.0041, 'c2': 0.0324, 'c3': 0.9782}},
        3: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0001, 'c1': 0.0031, 'c2': -0.0252, 'c3': 1.0126}},
        4: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0004, 'c1': 0.009, 'c2': -0.0715, 'c3': 1.0306}},
    },
    0.39: {
        1: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0005, 'c1': -0.0116, 'c2': 0.0974, 'c3': 0.934}},
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0002, 'c1': -0.0041, 'c2': 0.0324, 'c3': 0.9782}},
        3: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0001, 'c1': 0.0031, 'c2': -0.0251, 'c3': 1.0126}},
        4: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0004, 'c1': 0.0089, 'c2': -0.0712, 'c3': 1.0311}},
    },
    0.40: {
        1: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0005, 'c1': -0.0114, 'c2': 0.0959, 'c3': 0.9335}},
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0002, 'c1': -0.0041, 'c2': 0.0322, 'c3': 0.9779}},
        3: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0001, 'c1': 0.0031, 'c2': -0.0248, 'c3': 1.0128}},
        4: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0004, 'c1': 0.0087, 'c2': -0.0703, 'c3': 1.0324}},
    },
    0.41: {
        1: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0007, 'c1': -0.0154, 'c2': 0.1207, 'c3': 0.8822}},
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0002, 'c1': -0.0036, 'c2': 0.0299, 'c3': 0.9801}},
        3: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0001, 'c1': 0.0031, 'c2': -0.0248, 'c3': 1.0125}},
        4: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0004, 'c1': 0.009, 'c2': -0.0716, 'c3': 1.0352}},
    },
    0.42: {
        1: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0007, 'c1': -0.0165, 'c2': 0.1278, 'c3': 0.8677}},
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0001, 'c1': -0.0034, 'c2': 0.0293, 'c3': 0.9807}},
        3: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0001, 'c1': 0.0031, 'c2': -0.0247, 'c3': 1.0124}},
        4: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0004, 'c1': 0.0091, 'c2': -0.0719, 'c3': 1.0358}},
    },
    0.43: {
        1: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0008, 'c1': -0.0177, 'c2': 0.1349, 'c3': 0.853}},
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0001, 'c1': -0.0033, 'c2': 0.0286, 'c3': 0.9815}},
        3: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0001, 'c1': 0.0031, 'c2': -0.0247, 'c3': 1.0124}},
        4: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0004, 'c1': 0.0092, 'c2': -0.0724, 'c3': 1.0368}},
    },
    0.44: {
        1: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0009, 'c1': -0.0188, 'c2': 0.1419, 'c3': 0.8384}},
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0001, 'c1': -0.0032, 'c2': 0.0279, 'c3': 0.9822}},
        3: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0001, 'c1': 0.0031, 'c2': -0.0246, 'c3': 1.0122}},
        4: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0004, 'c1': 0.0092, 'c2': -0.0727, 'c3': 1.0375}},
    },
    0.45: {
        1: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0011, 'c1': -0.0229, 'c2': 0.1669, 'c3': 0.787}},
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.00009, 'c1': -0.0026, 'c2': 0.0252, 'c3': 0.9851}},
        3: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0001, 'c1': 0.0029, 'c2': -0.0238, 'c3': 1.0109}},
        4: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0004, 'c1': 0.009, 'c2': -0.0719, 'c3': 1.0374}},
    },
    0.46: {
        1: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0007, 'c1': -0.0162, 'c2': 0.1292, 'c3': 0.8523}},
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.00008, 'c1': -0.0024, 'c2': 0.0241, 'c3': 0.9865}},
        3: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0001, 'c1': 0.0029, 'c2': -0.0241, 'c3': 1.0127}},
        4: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0004, 'c1': 0.0087, 'c2': -0.0706, 'c3': 1.0377}},
    },
    0.47: {
        1: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0006, 'c1': -0.015, 'c2': 0.1216, 'c3': 0.8666}},
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.00008, 'c1': -0.0024, 'c2': 0.0238, 'c3': 0.9869}},
        3: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0001, 'c1': 0.0029, 'c2': -0.0242, 'c3': 1.0132}},
        4: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0004, 'c1': 0.0086, 'c2': -0.07, 'c3': 1.0375}},
    },
    0.48: {
        1: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0008, 'c1': -0.0177, 'c2': 0.1349, 'c3': 0.853}},
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0008, 'c1': -0.0177, 'c2': 0.1349, 'c3': 0.853}}, # ATENÇÃO: Constantes duplicadas intencionalmente?
        3: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0004, 'c1': -0.0105, 'c2': 0.093, 'c3': 1.077}},
        4: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0004, 'c1': 0.0093, 'c2': -0.0726, 'c3': 1.03}},
    },
    0.50: {
        1: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0004, 'c1': -0.0105, 'c2': 0.093, 'c3': 1.077}},
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0008, 'c1': -0.0177, 'c2': 0.1349, 'c3': 0.853}}, # ATENÇÃO: Constantes duplicadas intencionalmente?
        3: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0004, 'c1': -0.0105, 'c2': 0.093, 'c3': 1.077}},
        4: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0004, 'c1': 0.0093, 'c2': -0.0726, 'c3': 1.03}},
    },
}

INCERTEZA_FATOR_C_CONST_PERCENTUAL = 0.05 # ±5% para cada constante do Fator C

# Incertezas das entradas (em porcentagem do valor)
INCERTEZA_KV_PERCENTUAL = 0.01  # ±1%
INCERTEZA_MAS_PERCENTUAL = 0.05 # ±5%
INCERTEZA_ESPESSURA_PERCENTUAL = 0.05 # ±5%

# --- FIM DICIONÁRIOS GLOBAIS E CONSTANTES DE INCERTEZA ---

# --- FUNÇÃO GENÉRICA DE PROPAGAÇÃO DE INCERTEZAS (MANUAL) ---
def propagate_uncertainty(value_func, uncertainty_terms):
    """
    Calcula a incerteza propagada usando a fórmula da raiz quadrada da soma dos quadrados (RSS).
    Args:
        value_func (callable): Uma função lambda que encapsula o cálculo do valor.
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
    except Exception:
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
        # f(x, a0, a1, a2, a3) = a0 + a1*x + a2*x^2 + a3*x^3
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
    
    except Exception:
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

# Função para calcular o fator C
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

        csr_aproximado = min(formulas_fator_c_details.keys(), key=lambda x: abs(x - csr))

        if csr_aproximado not in formulas_fator_c_details:
            return "CSR fora do intervalo suportado.", 0.0

        formula_data = formulas_fator_c_details[csr_aproximado][grupo_val]
        func = formula_data['func']
        consts = formula_data['consts']

        c0, c1, c2, c3 = consts['c0'], consts['c1'], consts['c2'], consts['c3']
        dc0 = abs(c0) * INCERTEZA_FATOR_C_CONST_PERCENTUAL
        dc1 = abs(c1) * INCERTEZA_FATOR_C_CONST_PERCENTUAL
        dc2 = abs(c2) * INCERTEZA_FATOR_C_CONST_PERCENTUAL
        dc3 = abs(c3) * INCERTEZA_FATOR_C_CONST_PERCENTUAL

        fator_c_val = round(func(espessura, c0, c1, c2, c3), 4)

        # Derivadas parciais de C = c0*e^3 + c1*e^2 + c2*e + c3
        partial_deriv_e = 3*c0*espessura**2 + 2*c1*espessura + c2
        partial_deriv_c0 = espessura**3
        partial_deriv_c1 = espessura**2
        partial_deriv_c2 = espessura
        partial_deriv_c3 = 1

        incerteza_fator_c = propagate_uncertainty(
            lambda: fator_c_val,
            [
                (partial_deriv_e, d_espessura_abs),
                (partial_deriv_c0, dc0),
                (partial_deriv_c1, dc1),
                (partial_deriv_c2, dc2),
                (partial_deriv_c3, dc3)
            ]
        )
        return fator_c_val, round(incerteza_fator_c, 4)

    except Exception: # Captura qualquer erro
        return "Entrada inválida para Fator C", 0.0

# Função para calcular o Ki
def calcular_ki(kv_val, alvo_filtro, mas_val, espessura_mama_val, d_mas_abs, d_espessura_abs):
    try:
        x_val = tabela_ki_global.get((alvo_filtro, int(kv_val)), 0)
        
        if x_val == 0:
            return "Combinação de alvo/filtro e Kv não encontrada na tabela de Ki.", 0.0

        divisor_val = (63 - espessura_mama_val)**2
        if divisor_val == 0:
            return "Erro: A espessura da mama é inválida para o cálculo de Ki (63 - espessura deve ser diferente de zero).", 0.0

        ki_val = round(((x_val * mas_val)*2500) / divisor_val, 2)

        # Derivadas parciais de Ki = (x * mAs * 2500) / (63 - e)^2
        # d_x é INCERTEZA_KI_X_PERCENTUAL * x_val (incerteza do valor 'x' da tabela)
        d_x_abs = x_val * INCERTEZA_KI_X_PERCENTUAL

        # Derivada em relação a x: (mAs * 2500) / (63 - e)^2
        partial_deriv_x = (mas_val * 2500) / divisor_val
        # Derivada em relação a mAs: (x * 2500) / (63 - e)^2
        partial_deriv_mas = (x_val * 2500) / divisor_val
        # Derivada em relação a e: (x * mAs * 2500 * 2) / (63 - e)^3
        partial_deriv_espessura = ((x_val * mas_val * 2500 * 2) / ((63 - espessura_mama_val)**3))

        incerteza_ki = propagate_uncertainty(
            lambda: ki_val,
            [
                (partial_deriv_x, d_x_abs),
                (partial_deriv_mas, d_mas_abs),
                (partial_deriv_espessura, d_espessura_abs)
            ]
        )
        return ki_val, round(incerteza_ki, 4)

    except Exception:
        return "Erro Ki", 0.0


# FUNÇÃO calcular_dgm
def calcular_dgm(ki_val, s_val, fator_g_val, fator_c_val, incerteza_ki, incerteza_s, incerteza_fator_g, incerteza_fator_c):
    try:
        dgm = ki_val * s_val * fator_g_val * fator_c_val
        
        # Derivadas parciais de DGM = Ki * s * Fg * Fc
        partial_deriv_ki = s_val * fator_g_val * fator_c_val
        partial_deriv_s = ki_val * fator_g_val * fator_c_val
        partial_deriv_fg = ki_val * s_val * fator_c_val
        partial_deriv_fc = ki_val * s_val * fator_g_val

        incerteza_dgm = propagate_uncertainty(
            lambda: dgm,
            [
                (partial_deriv_ki, incerteza_ki),
                (partial_deriv_s, incerteza_s),
                (partial_deriv_fg, incerteza_fator_g),
                (partial_deriv_fc, incerteza_fator_c)
            ]
        )

        return round(dgm, 2), round(incerteza_dgm, 4)
    except Exception:
        return "Erro DGM", 0.0

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
        "Glandularidade (%)", "Grupo Glandularidade", 
        "Valor s", 
        "CSR", "Incerteza CSR", 
        "Fator g", "Incerteza Fator g", 
        "Fator C", "Incerteza Fator C",
        "Ki", "Incerteza Ki",
        "DGM (mGy)", "Incerteza DGM (mGy)" 
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

    # --- Cálculo de Incertezas Absolutas das Entradas ---
    d_kv_abs = kv * INCERTEZA_KV_PERCENTUAL
    d_mas_abs = mas * INCERTEZA_MAS_PERCENTUAL
    d_espessura_abs = espessura_mama * INCERTEZA_ESPESSURA_PERCENTUAL

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
                glandularidade = "Erro"
            else:
                glandularidade = glandularidade_calc
                st.info(f"**Glandularidade:** {glandularidade:.1f}%")

    # --- Cálculo e Exibição de s ---
    with col2:
        s = alvo_filtro_options.get(alvo_filtro, "Inválido")
        incerteza_s = 0.0 # Assumida como zero
        if isinstance(s, str):
            st.error(f"Erro no valor de s: {s}")
            s_val = "Erro"
        else:
            st.info(f"**Valor de s:** {s}")
            s_val = s

    # --- Cálculo e Exibição de CSR e Fator g ---
    col3, col4 = st.columns(2)
    with col3:
        csr_val, incerteza_csr = calcular_csr(kv, alvo_filtro, d_kv_abs)
        if isinstance(csr_val, str):
            st.error(f"Erro no cálculo de CSR: {csr_val}")
            csr_val_to_record = "Erro"
            incerteza_csr_to_record = "Erro"
        else:
            st.info(f"**Valor de CSR:** {csr_val} ± {incerteza_csr}")
            csr_val_to_record = csr_val
            incerteza_csr_to_record = incerteza_csr

    with col4:
        fator_g_val, incerteza_fator_g = calcular_fator_g(csr_val_to_record, espessura_mama, d_espessura_abs)
        
        if isinstance(fator_g_val, str):
            st.error(f"Erro no cálculo do Fator g: {fator_g_val}")
            fator_g_val_to_record = "Erro"
            incerteza_fator_g_to_record = "Erro"
        else:
            st.info(f"**Valor do Fator g:** {fator_g_val} ± {incerteza_fator_g}")
            fator_g_val_to_record = fator_g_val
            incerteza_fator_g_to_record = incerteza_fator_g

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
        fator_c_val, incerteza_fator_c = calcular_fator_c(csr_val_to_record, espessura_mama, glandularidade, d_espessura_abs)
        
        if isinstance(fator_c_val, str):
            st.error(f"Erro no cálculo do Fator C: {fator_c_val}")
            fator_c_val_to_record = "Erro"
            incerteza_fator_c_to_record = "Erro"
        else:
            st.info(f"**Valor do Fator C:** {fator_c_val} ± {incerteza_fator_c}")
            fator_c_val_to_record = fator_c_val
            incerteza_fator_c_to_record = incerteza_fator_c

    with col6:
        ki_val, incerteza_ki = calcular_ki(kv, alvo_filtro, mas, espessura_mama, d_mas_abs, d_espessura_abs)
        
        if isinstance(ki_val, str):
            st.error(f"Erro no cálculo de Ki: {ki_val}")
            ki_val_to_record = "Erro"
            incerteza_ki_to_record = "Erro"
        else:
            st.info(f"**Valor de Ki:** {ki_val} ± {incerteza_ki}")
            ki_val_to_record = ki_val
            incerteza_ki_to_record = incerteza_ki

    # --- Cálculo e Exibição final da DGM e sua Incerteza ---
    st.markdown("---")
    dgm_val_to_record = "Erro"
    incerteza_dgm_val_to_record = "Erro"
    
    if all(isinstance(val, (int, float)) for val in [ki_val_to_record, s_val, fator_g_val_to_record, fator_c_val_to_record, 
                                                     incerteza_ki_to_record, incerteza_s, incerteza_fator_g_to_record, incerteza_fator_c_to_record]):
        
        dgm, incerteza_dgm = calcular_dgm(ki_val_to_record, s_val, fator_g_val_to_record, fator_c_val_to_record, 
                                        incerteza_ki_to_record, incerteza_s, incerteza_fator_g_to_record, incerteza_fator_c_to_record)
        
        if isinstance(dgm, str):
            st.error(f"Não foi possível calcular a DGM: {dgm}")
        else:
            st.success(f"**Valor da DGM:** {dgm} mGy ± {incerteza_dgm} mGy")
            dgm_val_to_record = dgm
            incerteza_dgm_val_to_record = incerteza_dgm
    else:
        st.error("Não foi possível calcular a DGM devido a erros nos valores anteriores ou incertezas inválidas.")

    # Armazenar resultados na sessão
    if dgm_val_to_record != "Erro":
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
            "CSR": csr_val_to_record,
            "Incerteza CSR": incerteza_csr_to_record, 
            "Fator g": fator_g_val_to_record,
            "Incerteza Fator g": incerteza_fator_g_to_record,
            "Fator C": fator_c_val_to_record,
            "Incerteza Fator C": incerteza_fator_c_to_record,
            "Ki": ki_val_to_record,
            "Incerteza Ki": incerteza_ki_to_record,
            "DGM (mGy)": dgm_val_to_record,
            "Incerteza DGM (mGy)": incerteza_dgm_val_to_record 
        }
        st.session_state.resultados_dgm = pd.concat([st.session_state.resultados_dgm, pd.DataFrame([nova_linha])], ignore_index=True)

# --- Exibição do Histórico e Botões ---
st.markdown("---")
st.subheader("Histórico de Cálculos:")

if not st.session_state.resultados_dgm.empty:
    st.dataframe(st.session_state.resultados_dgm, use_container_width=True)
    
    csv_data = to_csv(st.session_state.resultados_dgm)
    st.download_button(
        label="📥 Baixar Resultados como CSV",
        data=csv_data,
        file_name=f"resultados_dgm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )
    
    if st.button("Limpar Histórico"):
        st.session_state.resultados_dgm = pd.DataFrame(columns=[
            "Data/Hora", "Idade", "Espessura (cm)", "Alvo/Filtro", "Kv", "mAs",
            "Glandularidade (%)", "Grupo Glandularidade", 
            "Valor s", 
            "CSR", "Incerteza CSR", 
            "Fator g", "Incerteza Fator g", 
            "Fator C", "Incerteza Fator C",
            "Ki", "Incerteza Ki",
            "DGM (mGy)", "Incerteza DGM (mGy)" 
        ])
        st.experimental_rerun()
else:
    st.info("Nenhum cálculo realizado ainda. Os resultados aparecerão aqui.")

st.markdown("---")
st.markdown("Desenvolvido por você, com o auxílio de um modelo de linguagem.")
