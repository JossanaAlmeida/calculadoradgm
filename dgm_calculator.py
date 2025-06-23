import streamlit as st
import pandas as pd
from datetime import datetime
import io
import math # Mantido caso haja outras operações que o usem, embora não mais para incerteza

# Define as opções para o alvo/filtro
alvo_filtro_options = {
    'Mo/Mo': 1,
    'Mo/Rh': 1.017,
    'Rh/Rh': 1.061,
    'Rh/Al': 1.044,
    'W/Rh': 1.042
}

# --- DICIONÁRIOS GLOBAIS E CONSTANTES (VERSÃO SEM INCERTEZAS DE KI E FATOR C) ---

# Coeficientes para CSR
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

# Constantes e Incertezas das constantes do Fator G (da0, da1, da2, da3)
# Mantidas pois a incerteza do Fator G ainda será calculada com base nelas e na espessura
FATOR_G_CONSTANTS_UNCERTAINTIES = {
    0.30: {'a0': 0.6862414, 'da0': 0.0215771, 'a1': -0.1903851, 'da1': 0.0122059, 'a2': 0.0211549, 'da2': 0.0020598, 'a3': -0.0008170, 'da3': 0.0001055},
    0.35: {'a0': 0.7520924, 'da0': 0.0214658, 'a1': -0.2040045, 'da1': 0.0121429, 'a2': 0.0223514, 'da2': 0.0020492, 'a3': -0.0008553, 'da3': 0.0001050},
    0.40: {'a0': 0.8135159, 'da0': 0.0208152, 'a1': -0.2167391, 'da1': 0.0117749, 'a2': 0.0234949, 'da2': 0.0019871, 'a3': -0.0008925, 'da3': 0.0001018},
    0.45: {'a0': 0.8587792, 'da0': 0.02030096, 'a1': -0.2213542, 'da1': 0.01148395, 'a2': 0.0235061, 'da2': 0.00193800, 'a3': -0.0008817, 'da3': 0.00009929},
    0.50: {'a0': 0.8926865, 'da0': 0.0192286, 'a1': -0.2192870, 'da1': 0.0108773, 'a2': 0.0224164, 'da2': 0.0018356, 'a3': -0.0008171, 'da3': 0.0000940},
    0.55: {'a0': 0.9237367, 'da0': 0.0184259, 'a1': -0.2189931, 'da1': 0.0104233, 'a2': 0.0221241, 'da2': 0.0017590, 'a3': -0.0008050, 'da3': 0.0000901},
    0.60: {'a0': 0.9131422, 'da0': 0.0097610, 'a1': -0.1996713, 'da1': 0.0055217, 'a2': 0.0190965, 'da2': 0.0009318, 'a3': -0.0006696, 'da3': 0.0000477},
}


# Dicionário de fórmulas para Fator C
# O formato de dicionário de lambdas é mantido, mas não será usado para incerteza.
formulas_fator_c_details = {
    0.34: {1: lambda e, c0, c1, c2, c3: (c0 * e**3) - (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0004, 'c1': -0.0105, 'c2': 0.093, 'c3': 0.9449}},
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
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0008, 'c1': -0.0177, 'c2': 0.1349, 'c3': 0.853}},
        3: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0004, 'c1': -0.0105, 'c2': 0.093, 'c3': 1.077}},
        4: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': -0.0004, 'c1': 0.0093, 'c2': -0.0726, 'c3': 1.03}},
    },
    0.50: {
        1: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0004, 'c1': -0.0105, 'c2': 0.093, 'c3': 1.077}},
        2: {'func': lambda e, c0, c1, c2, c3: (c0 * e**3) + (c1 * e**2) + (c2 * e) + c3, 'consts': {'c0': 0.0008, 'c1': -0.0177, 'c2': 0.1349, 'c3': 0.853}},
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
def propagate_uncertainty(uncertainty_terms):
    """
    Calcula a incerteza propagada usando a fórmula da raiz quadrada da soma dos quadrados (RSS).
    Args:
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
        data = csr_coeffs.get(alvo_filtro)
        if not data:
            return "Alvo/filtro inválido", 0.0

        const_a = data['a']
        const_b = data['b']
        
        csr_val = round(const_a * kv_val + const_b, 2)

        # Derivada parcial de CSR em relação a Kv é 'const_a'
        partial_deriv_kv = const_a
        
        incerteza_csr = propagate_uncertainty(
            [(partial_deriv_kv, d_kv_abs)]
        )

        return csr_val, round(incerteza_csr, 4)
    except Exception:
        return "Erro CSR", 0.0


# FUNÇÃO calcular_fator_g - ESTA FOI REVERTIDA PARA A VERSÃO DA TABELA ORIGINAL
def calcular_fator_g(csr, espessura):
    try:
        csr = float(csr)
        espessura = int(espessura) # Mantido int porque a tabela espera isso.

        g_values = {
            0.30: [0.390, 0.274, 0.207, 0.183, 0.164, 0.135, 0.114, 0.098, 0.0859, 0.0763, 0.0687],
            0.35: [0.433, 0.309, 0.235, 0.208, 0.187, 0.154, 0.130, 0.112, 0.0981, 0.0873, 0.0783],
            0.40: [0.473, 0.342, 0.261, 0.232, 0.209, 0.172, 0.145, 0.126, 0.1106, 0.0986, 0.0887],
            0.45: [0.509, 0.374, 0.289, 0.258, 0.232, 0.192, 0.163, 0.140, 0.1233, 0.1096, 0.0988],
            0.50: [0.543, 0.406, 0.318, 0.285, 0.258, 0.214, 0.177, 0.154, 0.1357, 0.1207, 0.1088],
            0.55: [0.573, 0.437, 0.346, 0.311, 0.287, 0.236, 0.202, 0.175, 0.1543, 0.1375, 0.1240],
            0.60: [0.587, 0.466, 0.374, 0.339, 0.310, 0.261, 0.224, 0.195, 0.1723, 0.1540, 0.1385],
        }

        espessuras_cm_list = [2, 3, 4, 4.5, 5, 6, 7, 8, 9, 10, 11] # Lista de espessuras para indexação
        csr_proximo = min(g_values, key=lambda x: abs(x - csr))

        try:
            indice_espessura = espessuras_cm_list.index(espessura)
            return g_values[csr_proximo][indice_espessura]
        except ValueError:
            return "Espessura da mama inválida"
    except ValueError:
        return "Entrada inválida"

# FUNÇÃO DE GLANDULARIDADE (também revertida para a versão da tabela original)
def calcular_glandularidade(idade, espessura_mama):
    espessuras_cm_list = [2, 3, 4, 4.5, 5, 6, 7, 8, 9, 10, 11] # Lista de espessuras para indexação
    if 40 <= idade <= 49:
        porcentagens = [100, 82, 65, 49, 35, 24, 14, 8, 5, 5, 5]
    elif 50 <= idade <= 64:
        porcentagens = [100, 72, 50, 33, 21, 12, 7, 4, 3, 3, 3]
    else:
        return "Idade fora do intervalo considerado."

    try:
        indice_espessura = espessuras_cm_list.index(espessura_mama)
        return porcentagens[indice_espessura]
    except ValueError:
        return "Espessura da mama inválida."


# Função para calcular o fator C
def calcular_fator_c(csr, espessura, glandularidade): # Removido d_espessura_abs
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

        # Usa o dicionário original formulas_fator_c (agora com o nome globalizado)
        csr_aproximado = min(formulas_fator_c_details.keys(), key=lambda x: abs(x - csr))

        if csr_aproximado not in formulas_fator_c_details:
            return "CSR fora do intervalo suportado."

        formula_data = formulas_fator_c_details[csr_aproximado][grupo_val]
        func = formula_data['func']
        consts = formula_data['consts']

        c0, c1, c2, c3 = consts['c0'], consts['c1'], consts['c2'], consts['c3']
        
        fator_c_val = round(func(espessura, c0, c1, c2, c3), 4)

        return fator_c_val
    except Exception: # Retorna erro sem detalhes para esta versão
        return "Entrada inválida para Fator C"

# Função para calcular o Ki
def calcular_ki(kv, alvo_filtro, mas, espessura_mama): # Removido d_mas_abs, d_espessura_abs
    tabela_ki = {
        ('Mo/Mo', 26): 0.1357,
        ('Mo/Mo', 27): 0.1530,
        ('Mo/Rh', 29): 0.1540,
        ('Mo/Rh', 31): 0.1830,
    }
    x = tabela_ki.get((alvo_filtro, int(kv)), 0)
    
    if x == 0:
        return "Combinação de alvo/filtro e Kv não encontrada na tabela de Ki."
    
    divisor = (63 - espessura_mama)**2
    if divisor == 0:
        return "Erro: A espessura da mama é inválida para o cálculo de Ki (63 - espessura deve ser diferente de zero)."

    return round(((x * mas)*2500) / divisor, 2)


# FUNÇÃO calcular_dgm (sem incertezas)
def calcular_dgm(ki, s, fator_g, fator_c):
    try:
        dgm = ki * s * fator_g * fator_c
        return round(dgm, 2)
    except (ValueError, TypeError):
        return "Entrada inválida para o cálculo do DGM"

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
        "CSR", 
        "Fator g", 
        "Fator C", 
        "Ki", 
        "DGM (mGy)" 
    ])

# Sidebar para inputs
with st.sidebar:
    st.header("Dados de Entrada")
    idade = st.number_input('Idade:', min_value=1, max_value=120, value=45, help="Idade da paciente (usado para glandularidade automática)")
    
    # ATENÇÃO: Se as funções calcular_fator_g e calcular_glandularidade forem da versão de TABELA,
    # a espessura da mama TEM QUE SER um valor da lista [2, 3, 4, 4.5, 5, 6, 7, 8, 9, 10, 11].
    # Voltando para selectbox por isso.
    espessura_mama = st.selectbox('Espessura da Mama (cm):', options=[2, 3, 4, 4.5, 5, 6, 7, 8, 9, 10, 11], index=5, help="Espessura da mama comprimida em centímetros (selecione da lista)")
    
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

    # --- Incertezas Absolutas das Entradas (mantidas, mas não usadas na DGM final) ---
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
        if isinstance(s, str):
            st.error(f"Erro no valor de s: {s}")
            s_val = "Erro"
        else:
            st.info(f"**Valor de s:** {s}")
            s_val = s

    # --- Cálculo e Exibição de CSR e Fator g ---
    col3, col4 = st.columns(2)
    with col3:
        csr = calcular_csr(kv, alvo_filtro) # calculate_csr retorna APENAS o valor
        if isinstance(csr, str):
            st.error(f"Erro no cálculo de CSR: {csr}")
            csr_val_to_record = "Erro"
        else:
            st.info(f"**Valor de CSR:** {csr}")
            csr_val_to_record = csr

    with col4:
        fator_g = calcular_fator_g(csr_val_to_record, espessura_mama) # calculate_fator_g retorna APENAS o valor
        if isinstance(fator_g, str):
            st.error(f"Erro no cálculo do Fator g: {fator_g}")
            fator_g_val_to_record = "Erro"
        else:
            st.info(f"**Valor do Fator g:** {fator_g}")
            fator_g_val_to_record = fator_g

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
        fator_c = calcular_fator_c(csr_val_to_record, espessura_mama, glandularidade) # calculate_fator_c retorna APENAS o valor
        if isinstance(fator_c, str):
            st.error(f"Erro no cálculo do Fator C: {fator_c}")
            fator_c_val_to_record = "Erro"
        else:
            st.info(f"**Valor do Fator C:** {fator_c}")
            fator_c_val_to_record = fator_c

    with col6:
        ki = calcular_ki(kv, alvo_filtro, mas, espessura_mama) # calculate_ki retorna APENAS o valor
        if isinstance(ki, str):
            st.error(f"Erro no cálculo de Ki: {ki}")
            ki_val_to_record = "Erro"
        else:
            st.info(f"**Valor de Ki:** {ki}")
            ki_val_to_record = ki

    # --- Cálculo e Exibição final da DGM ---
    st.markdown("---")
    dgm_val_to_record = "Erro"
    incerteza_dgm_val_to_record = "N/A" # Incerteza não calculada nesta versão
    
    if all(isinstance(val, (int, float)) for val in [ki_val_to_record, s_val, fator_g_val_to_record, fator_c_val_to_record]):
        dgm = calcular_dgm(ki_val_to_record, s_val, fator_g_val_to_record, fator_c_val_to_record)
        if isinstance(dgm, str):
            st.error(f"Não foi possível calcular a DGM: {dgm}")
        else:
            st.success(f"**Valor da DGM:** {dgm} mGy")
            dgm_val_to_record = dgm
    else:
        st.error("Não foi possível calcular a DGM devido a erros nos valores anteriores.")

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
            "Fator g": fator_g_val_to_record,
            "Fator C": fator_c_val_to_record,
            "Ki": ki_val_to_record,
            "DGM (mGy)": dgm_val_to_record 
            # Colunas de incerteza não são adicionadas a esta versão do histórico
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
            "CSR", 
            "Fator g", 
            "Fator C", 
            "Ki", 
            "DGM (mGy)"
        ])
        st.experimental_rerun()
else:
    st.info("Nenhum cálculo realizado ainda. Os resultados aparecerão aqui.")

st.markdown("---")
st.markdown("Desenvolvido por você, com o auxílio de um modelo de linguagem.")
