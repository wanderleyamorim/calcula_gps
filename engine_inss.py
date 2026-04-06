#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Engine INSS (v4.0) - Motor de Extração e Cálculo Modular
Focado em fornecer dados limpos para as Skills do Gemini CLI.
"""

import re
import sys
import datetime
import json
import os
import subprocess

# --- Configurações e Tabela SM ---
DATA_HOJE = datetime.date.today()
SM_HIST = [
    (1994, 7, 64.79), (1994, 9, 70.00), (1995, 5, 100.00), (1996, 5, 112.00),
    (1997, 5, 120.00), (1998, 5, 130.00), (1999, 5, 136.00), (2000, 4, 151.00),
    (2001, 4, 180.00), (2002, 4, 200.00), (2003, 4, 240.00), (2004, 5, 260.00),
    (2005, 5, 300.00), (2006, 4, 350.00), (2007, 4, 380.00), (2008, 3, 415.00),
    (2009, 2, 465.00), (2010, 1, 510.00), (2011, 1, 540.00), (2011, 3, 545.00),
    (2012, 1, 622.00), (2013, 1, 678.00), (2014, 1, 724.00), (2015, 1, 788.00),
    (2016, 1, 880.00), (2017, 1, 937.00), (2018, 1, 954.00), (2019, 1, 998.00),
    (2020, 1, 1039.00), (2020, 2, 1045.00), (2021, 1, 1100.00), (2022, 1, 1212.00),
    (2023, 1, 1302.00), (2023, 5, 1320.00), (2024, 1, 1412.00), (2025, 1, 1518.00),
    (2026, 1, 1621.00)
]

def get_sm(year, month):
    res = 64.79
    for (y, m, val) in SM_HIST:
        if (y, m) <= (year, month): res = val
        else: break
    return res

# --- Extrator de Texto ---
def get_pdf_text(path):
    try:
        return subprocess.run(['pdftotext', path, '-'], capture_output=True, text=True).stdout
    except: return ""

# --- Parser Simplificado ---
def parse_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    anexos = os.path.join(base_dir, 'anexos')
    
    painel_path = next((os.path.join(anexos, f) for f in os.listdir(anexos) if 'painel' in f.lower()), None)
    contrib_path = next((os.path.join(anexos, f) for f in os.listdir(anexos) if 'contrib' in f.lower()), None)
    
    if not painel_path or not contrib_path:
        return {"error": "PDFs não encontrados na pasta anexos/"}

    text_p = get_pdf_text(painel_path)
    text_c = get_pdf_text(contrib_path)
    
    # Extrair competências e valores (Regex assertiva)
    data = {}
    
    # Busca por competência MM/AAAA e valores monetários próximos
    comp_matches = re.findall(r'(\d{2}/\d{4})', text_p)
    for comp in set(comp_matches):
        m, y = int(comp[:2]), int(comp[3:])
        sm = get_sm(y, m)
        data[comp] = {
            "sm": sm,
            "pago": 0.0,
            "indicadores": [],
            "tipo": "Desconhecido"
        }

    # Capturar pagamentos reais do arquivo de contribuições
    contrib_matches = re.findall(r'(\d{2}/\d{4}).*?(\d{1,3}(?:\.\d{3})*,\d{2})', text_c, re.DOTALL)
    for comp, val in contrib_matches:
        if comp in data:
            data[comp]["pago"] = float(val.replace('.', '').replace(',', '.'))

    # Capturar indicadores do painel
    for comp in data:
        pattern = rf'{comp}.*?Indicadores(.*?)(?=\d{{2}}/\d{{4}}|$)'
        ind_block = re.search(pattern, text_p, re.DOTALL)
        if ind_block:
            inds = re.findall(r'[A-Z]{3,}-[A-Z0-9-]+', ind_block.group(1))
            data[comp]["indicadores"] = list(set(inds))

    return data

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        print(json.dumps(parse_data(), indent=2))
    else:
        print("Engine INSS pronta. Use --json para extrair dados.")
