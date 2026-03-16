#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Processador CNIS -> GPS/DARF  (v3.0)
====================================
Lê dois PDFs (painelCidadao + contribuicaoRecolhimentoResultado),
cruza indicadores e códigos de pagamento por competência,
aplica regras de negócio (Cenário A / B) e gera:
  - Arquivos HTML separados por código GPS (para extensão Ajudante Salweb)
  - Relatório DARF (texto) para competências Pós-Reforma < 5 anos
"""

import re
import sys
import datetime
import io
import os

# ===========================================================================
# CONFIG
# ===========================================================================
DATA_HOJE = datetime.date.today()
DATA_REFORMA = datetime.date(2019, 11, 13)
DATA_DECADENCIA_5Y = DATA_HOJE.replace(year=DATA_HOJE.year - 5)

# ===========================================================================
# TABELA HISTÓRICA SALÁRIO MÍNIMO (1994-2025)
# Formato: lista de (ano, mês_início_vigência, valor)
# Ordenada cronologicamente.  get_minimo() busca o valor vigente.
# ===========================================================================
SALARIO_MINIMO_HIST = [
    (1994,  7,   64.79),
    (1994,  9,   70.00),
    (1995,  5,  100.00),
    (1996,  5,  112.00),
    (1997,  5,  120.00),
    (1998,  5,  130.00),
    (1999,  5,  136.00),
    (2000,  4,  151.00),
    (2001,  4,  180.00),
    (2002,  4,  200.00),
    (2003,  4,  240.00),
    (2004,  5,  260.00),
    (2005,  5,  300.00),
    (2006,  4,  350.00),
    (2007,  4,  380.00),
    (2008,  3,  415.00),
    (2009,  2,  465.00),
    (2010,  1,  510.00),
    (2011,  1,  540.00),
    (2011,  3,  545.00),
    (2012,  1,  622.00),
    (2013,  1,  678.00),
    (2014,  1,  724.00),
    (2015,  1,  788.00),
    (2016,  1,  880.00),
    (2017,  1,  937.00),
    (2018,  1,  954.00),
    (2019,  1,  998.00),
    (2020,  1, 1039.00),
    (2020,  2, 1045.00),
    (2021,  1, 1100.00),
    (2022,  1, 1212.00),
    (2023,  1, 1302.00),
    (2023,  5, 1320.00),
    (2024,  1, 1412.00),
    (2025,  1, 1518.00),
    (2026,  1, 1621.00)
]

# Valores anteriores a jul/1994 (pre-Real) — fallback
_SM_ANTES_PLANO_REAL = 64.79


def get_minimo(comp_date):
    """Retorna o salário mínimo vigente para a competência (date)."""
    y, m = comp_date.year, comp_date.month
    resultado = _SM_ANTES_PLANO_REAL
    for (ano, mes_vig, valor) in SALARIO_MINIMO_HIST:
        if (ano, mes_vig) <= (y, m):
            resultado = valor
        else:
            break
    return resultado


# ===========================================================================
# TEMPLATES HTML  (formato exigido pela extensão Ajudante Salweb)
# ===========================================================================
HTML_HEADER = """<table xmlns="http://www.w3.org/1999/xhtml" id="tabela">
    <thead>
        <tr>
            <th>Competência</th>
            <th>Código</th>
            <th>Valor</th>
            <th>Excluir</th>
        </tr>
    </thead>
    <tbody id="corpotabela">"""

HTML_ROW = """        <tr>
            <td>{competencia}</td>
            <td>{codigo}</td>
            <td width="150px">
                <div contenteditable="true">{valor}</div>
            </td>
            <td id="excludeRow">X</td>
        </tr>"""

HTML_FOOTER = """    </tbody>
</table>"""


# ===========================================================================
# UTILIDADES
# ===========================================================================
def parse_val(s):
    """Converte string monetária BR (ex: '1.412,00') em float."""
    return float(s.replace('.', '').replace(',', '.'))


def fmt_val(f):
    """Formata float para string BR com vírgula (ex: '211,80')."""
    return f"{f:.2f}".replace('.', ',')


# ===========================================================================
# PARSER DO PDF — EXTRAÇÃO DE TEXTO
# ===========================================================================
def extrair_texto_pdf(caminho_pdf):
    """Extrai texto de todas as páginas do PDF usando PyMuPDF (fitz)."""
    import fitz
    doc = fitz.open(caminho_pdf)
    texto_completo = ""
    for pagina in doc:
        texto_completo += pagina.get_text() + "\n"
    doc.close()
    return texto_completo


# ===========================================================================
# PARSER DO PAINEL CIDADÃO (painelCidadao.pdf)
# Extrai: competência -> {contribuicao, sal_contrib, indicadores[]}
# ===========================================================================
_RE_COMP = re.compile(r'^(\d{2}/\d{4})$')
_RE_VALOR = re.compile(r'^(\d{1,3}(?:\.\d{3})*,\d{2})$')
_RE_DATA_PGTO = re.compile(r'^\d{2}/\d{2}/\d{4}$')
_INDICADORES_CONHECIDOS = {
    'IREC-MEI', 'IREC-LC123', 'IREC-INDPEND',
    'IREC-FBR',        # FBR validado (5% suficiente p/ Apos. Idade)
    'IREC-FBR-DEF',    # FBR DEFINITIVAMENTE validado (também ok, não gera GPS)
    'IREC-FBR-IND',    # FBR INDEVIDO/indeferido -> gera 1830 (5%->11%)
    'PREC-MENOR-MIN', 'PSC-MEN-SM-EC103',
    'PREC-FBR',        # PREC-FBR genérico (reservado caso apareça)
    'PREM-EXT', 'IREM-INDPEND',
}


def parse_painel_cidadao(texto):
    """
    Parseia o texto do painelCidadão.
    Retorna dict: { 'MM/AAAA': { 'contribuicao': float, 'sal_contrib': float,
                                   'indicadores': set(), 'tipo_filiado': str } }
    Múltiplas entradas da mesma competência são mescladas (indicadores acumulados).
    """
    resultados = {}
    linhas = texto.split('\n')
    linhas = [l.strip() for l in linhas if l.strip()]

    # Detectar seções de Contribuições (não Remunerações)
    em_contribuicoes = False
    ultimo_tipo_filiado = "Indefinido" # Armazena o tipo de filiado atual do bloco

    i = 0
    while i < len(linhas):
        linha = linhas[i]

        # Detectar Tipo Filiado
        if linha.startswith('Tipo Filiado'):
             # A estrutura do PDF é uma tabela:
             #   "Tipo Filiado Vínculo" (header)
             #   "Data Início" / "Data Fim" / seq / NIT / "RECOLHIMENTO" / "Facultativo" / datas
             # Precisamos varrer as próximas linhas para encontrar o tipo real.
             _tipos_conhecidos = {
                 'Facultativo': 'Facultativo',
                 'Contribuinte Individual': 'CI',
                 'Empregado': 'Empregado',
                 'Doméstico': 'Doméstico',
                 'Avulso': 'Avulso',
             }
             # Procurar tipo nas próximas linhas (max 10)
             for look in range(1, min(11, len(linhas) - i)):
                 prox = linhas[i + look].strip()
                 for key, val in _tipos_conhecidos.items():
                     if key in prox:
                         ultimo_tipo_filiado = val
                         break
                 else:
                     continue
                 break  # Encontrou tipo -> parar
             
             # Sai do modo contribuições temporariamente até confirmar o próximo bloco
             em_contribuicoes = False
             i += 1
             continue

        # Detectar início de seção "Contribuições"
        if linha.startswith('Contribui') and i + 1 < len(linhas) and 'Compet' in linhas[i + 1]:
            em_contribuicoes = True
            i += 1
            continue

        # Detectar saída de seção contribuições
        if linha.startswith('Remunera') or linha.startswith('Rela') or 'Seq.' in linha:
            if 'Contribui' not in linha:
                em_contribuicoes = False

        # Detectar quando entramos numa seção de "Relações Previdenciárias" que contém info do vínculo
        # Tipo Filiado Vínculo aparece antes das contribuições de cada vínculo
        if 'Tipo Filiado' in linha:
            em_contribuicoes = False
            i += 1
            continue

        # Cabeçalhos de coluna — pular
        if linha in ('Compet.', 'Contribuição', 'Indicadores', 'Salário Contrib.',
                      'Data Pgto.', 'Competência', 'Competência'):
            i += 1
            continue

        if not em_contribuicoes:
            # Reativar se encontramos cabeçalho de contribuições
            if 'Compet.' in linha and i + 1 < len(linhas):
                prox = linhas[i + 1] if i + 1 < len(linhas) else ''
                if 'Contribui' in prox or _RE_COMP.match(prox):
                    em_contribuicoes = True
            i += 1
            continue

        # Tentar ler uma entrada de contribuição
        if _RE_COMP.match(linha):
            comp = linha
            indicadores = set()
            contribuicao = None
            sal_contrib = None

            # Olhar as próximas linhas para coletar dados desta competência
            j = i + 1
            valores_encontrados = []
            while j < len(linhas) and j < i + 8:
                lj = linhas[j]

                # Se encontrei outra competência, para
                if _RE_COMP.match(lj) and len(valores_encontrados) >= 1:
                    break

                # Se é um indicador
                if lj in _INDICADORES_CONHECIDOS or lj.startswith('IREC-') or lj.startswith('PREC-') or lj.startswith('PSC-') or lj.startswith('PREM-') or lj.startswith('IREM-'):
                    indicadores.add(lj)
                    j += 1
                    continue

                # Se é um valor monetário
                if _RE_VALOR.match(lj):
                    valores_encontrados.append(parse_val(lj))
                    j += 1
                    continue

                # Se é uma data de pagamento
                if _RE_DATA_PGTO.match(lj):
                    j += 1
                    continue

                # Cabeçalho repetido ou texto do INSS
                if lj.startswith('O INSS') or lj.startswith('Página') or 'Compet.' in lj:
                    j += 1
                    continue

                # Outro texto — pode ser header da próx página
                if any(x in lj for x in ['INSS', 'CNIS', 'Extrato', 'Nit:', 'Nome:', 'CPF:', 'Identifica']):
                    j += 1
                    continue

                # Se cheguei aqui e a linha parece ser uma competência nova
                if _RE_COMP.match(lj):
                    break

                j += 1

            # Atribuir valores: primeiro = contribuição, segundo = salário de contrib
            if len(valores_encontrados) >= 2:
                contribuicao = valores_encontrados[0]
                sal_contrib = valores_encontrados[1]
            elif len(valores_encontrados) == 1:
                contribuicao = valores_encontrados[0]

            # Guardar resultado (mesclar se já existe)
            if comp in resultados:
                if contribuicao is not None:
                    resultados[comp]['contribuicao'] = contribuicao
                if sal_contrib is not None:
                    resultados[comp]['sal_contrib'] = sal_contrib
                resultados[comp]['indicadores'].update(indicadores)
            else:
                resultados[comp] = {
                    'contribuicao': contribuicao,
                    'sal_contrib': sal_contrib,
                    'indicadores': indicadores,
                    'tipo_filiado': ultimo_tipo_filiado,
                }

            i = j
            continue

        i += 1

    # --- Pós-processamento: indicadores órfãos após quebra de página ---
    # o PDF de 2 colunas pode separar indicadores (IREC-FBR) da competência
    # quando há mudança de página. Aqui, re-parseia o texto procurando
    # indicadores "soltos" que aparecem entre um footer/header de página 
    # e a próxima competência, e os associa às últimas competências vistas.
    last_comps = []  # últimas competências vistas
    in_page_break = False
    i = 0
    while i < len(linhas):
        lj = linhas[i]
        if _RE_COMP.match(lj):
            if in_page_break:
                in_page_break = False
            last_comps.append(lj)
            # Manter apenas as últimas 2 (2 colunas PDF)
            if len(last_comps) > 2:
                last_comps = last_comps[-2:]
        elif lj.startswith('O INSS poderáa') or lj.startswith('O INSS poder') or lj.startswith('Página') or (len(lj) > 10 and '/' in lj and ':' in lj and lj[0:2].isdigit() and not _RE_COMP.match(lj)):
            # Footer/page break detectado ("O INSS poderá...", "Página X de Y", "14/02/2026 07:13:08")
            in_page_break = True
        elif in_page_break:
            # Estamos dentro de um page break; checar se é indicador órfão
            is_indicator = (lj.startswith('IREC-') or lj.startswith('PREC-') or 
                           lj.startswith('PSC-') or lj.startswith('PREM-') or 
                           lj.startswith('IREM-') or lj in _INDICADORES_CONHECIDOS)
            if is_indicator and last_comps:
                comp_alvo = last_comps.pop(0)  # FIFO: primeiro da lista
                if comp_alvo in resultados:
                    resultados[comp_alvo]['indicadores'].add(lj)
            # Outros textos de header (INSS, CNIS, nomes, etc.) — apenas ignorar
        i += 1

    return resultados


# ===========================================================================
# PARSER DO CONTRIBUIÇÃO/RECOLHIMENTO (contribuicaoRecolhimentoResultado.pdf)
# Extrai: competência -> {valor_contribuicao, valor_autenticado, codigo_pagamento}
# ===========================================================================
_CODIGOS_GPS = {
    # CI
    '1007', '1120', '1163', '1236', '1244', '1287', '1295', '1805', '1902', '1910',
    # Facultativo
    '1406', '1473', '1686', '1821', '1830', '1929', '1945',
    # MEI
    '1066',
}


def parse_contribuicao_recolhimento(texto):
    """
    Parseia o texto do contribuicaoRecolhimentoResultado.
    Retorna dict: { 'MM/AAAA': { 'valor_contrib': float, 'valor_autenticado': float,
                                   'codigo': str } }
    Se houver múltiplas entradas para a mesma competência, a última prevalece
    (ou poderia ser mesclada dependendo do caso).
    """
    resultados = {}
    linhas = texto.split('\n')
    linhas = [l.strip() for l in linhas if l.strip()]

    i = 0
    while i < len(linhas):
        linha = linhas[i]

        # Procurar competências
        if _RE_COMP.match(linha):
            comp = linha
            valores = []
            codigo = None

            # Ler as próximas linhas
            j = i + 1
            while j < len(linhas) and j < i + 10:
                lj = linhas[j]

                # Valor monetário
                if _RE_VALOR.match(lj):
                    valores.append(parse_val(lj))
                    j += 1
                    continue

                # Código de pagamento
                if lj in _CODIGOS_GPS:
                    codigo = lj
                    j += 1
                    continue

                # Data (pagamento/autenticação)
                if _RE_DATA_PGTO.match(lj):
                    j += 1
                    continue

                # Outra competência = fim deste bloco
                if _RE_COMP.match(lj):
                    break

                # Banco, Agência, UF, Acerto, cabeçalhos
                if lj in ('Acerto',) or len(lj) <= 8:
                    j += 1
                    continue

                # Headers de página
                if any(x in lj for x in ['Compet', 'Data de', 'Valor de', 'Valor Autenticado',
                                          'Código de', 'Pagamento', 'Banco', 'Agência', 'UF']):
                    j += 1
                    continue

                j += 1

            if codigo:
                # Geralmente: valor_contrib, competência, data_auth, valor_auth, codigo
                # Mas a ordem pode variar. Pegar primeiro e último valor antes do código.
                valor_contrib = valores[0] if len(valores) >= 1 else None
                valor_autenticado = valores[-1] if len(valores) >= 2 else valor_contrib

                if comp not in resultados:
                    resultados[comp] = {
                        'valor_contrib': valor_contrib,
                        'valor_autenticado': valor_autenticado,
                        'codigo': codigo,
                    }
                # Se já existe, podemos ter múltiplas GPS para mesma competência
                # (ex: pagamento parcial + complemento). Manter a primeira.

            i = j if j > i + 1 else i + 1
            continue

        i += 1

    return resultados


# ===========================================================================
# MOTOR DE PROCESSAMENTO — REGRAS DE NEGÓCIO
# ===========================================================================
def processar(dados_painel, dados_contrib):
    """
    Cruza dados dos dois PDFs e aplica regras de negócio.
    Retorna: (rows_by_code, text_report)
      rows_by_code: { 'codigo': [html_row, ...] }
      text_report: [linhas de texto para DARF]
    """
    rows_by_code = {}
    text_report = []
    warnings_extemporaneos = []  # Lista para alertas de extemporâneos

    # Unificar todas as competências
    todas_comps = set(dados_painel.keys()) | set(dados_contrib.keys())

    for comp_str in sorted(todas_comps, key=lambda c: (int(c[3:]), int(c[:2]))):
        m, y = int(comp_str[:2]), int(comp_str[3:])
        comp_date = datetime.date(y, m, 1)

        painel = dados_painel.get(comp_str, {})
        contrib = dados_contrib.get(comp_str, {})

        indicadores = painel.get('indicadores', set())
        contribuicao = painel.get('contribuicao') or contrib.get('valor_contrib')
        sal_contrib = painel.get('sal_contrib')
        tipo_filiado = painel.get('tipo_filiado', 'Indefinido')
        codigo_original = contrib.get('codigo')

        if not indicadores and not codigo_original:
            continue  # Sem dados suficientes

        # Verificação de Extemporâneos / Pendências
        # Verificação de Extemporâneos / Pendências
        # PREC-FBR é regra de negócio (FBR não validado -> GPS 1830), NÃO alerta extemporâneo.
        # Por isso está excluído desta lista de alertas.
        indicadores_alerta_prefixes = {'PREM-EXT', 'IREC-INDPEND', 'IREC-GFIP', 'PREC-FACULTCONC'}
        encontrados = set()
        for ind in indicadores:
            for alerta in indicadores_alerta_prefixes:
                if ind.startswith(alerta):
                    encontrados.add(ind)
        
        if encontrados:
            warnings_extemporaneos.append(
                f"- {comp_str}: Contém indicadores de pendência/extemporâneo: {', '.join(encontrados)}. "
                f"Verificar se o vínculo foi comprovado."
            )

        sm = get_minimo(comp_date)
        is_post_reforma = comp_date > DATA_REFORMA
        is_decadente = comp_date < DATA_DECADENCIA_5Y

        final_code = None
        final_value = None
        motivo = ""

        # ---------------------------------------------------------------
        # REGRA 1: IREC-MEI (MEI 5%) -> Complementar para 20%
        # ---------------------------------------------------------------
        if 'IREC-MEI' in indicadores:
            final_code = '1910'
            final_value = round(sm * 0.15, 2)  # 20% - 5% = 15%
            motivo = f"MEI 5%->20% (SM {fmt_val(sm)} × 15%)"

        # ---------------------------------------------------------------
        # REGRA 2: IREC-LC123 (11% Simplificado, SEM ser MEI)
        #          -> Aposentadoria por Idade (5% ou 11%):
        #            - Se FBR VALIDADO (IREC-FBR): 5% é suficiente -> NÃO gera GPS
        #            - Se FBR NÃO VALIDADO (PREC-FBR): complementar 5%->11% -> GPS 1830
        #            - Se LC123 puro (sem FBR): validar >= 11% Sal. Min.
        #              Abaixo do mín: Fac. -> código original (1929/1473/1406), CI -> 1295
        # ---------------------------------------------------------------
        elif 'IREC-LC123' in indicadores or 'IREC-FBR-IND' in indicadores or any(ind.startswith('PREC-FBR') for ind in indicadores):
            # IREC-LC123 = simplificado (11% ou FBR 5%)
            # IREC-FBR-IND = FBR indevido/indeferido         -> gera GPS 1830
            # IREC-FBR-DEF = FBR DEFINITIVAMENTE validado    -> NÃO gera GPS (ok)
            # PREC-FBR     = genérico (caso apareça no PDF) -> gera GPS 1830

            # FBR validado: IREC-FBR puro OU IREC-FBR-DEF (definitivo)
            has_irec_fbr = 'IREC-FBR' in indicadores or 'IREC-FBR-DEF' in indicadores
            # FBR NÃO validado: somente IREC-FBR-IND ou PREC-FBR genérico
            has_fbr_nao_validado = any(
                ind == 'IREC-FBR-IND' or ind.startswith('PREC-FBR')
                for ind in indicadores
            )

            if has_irec_fbr and not has_fbr_nao_validado:
                # FBR validado: 5% é suficiente para aposentadoria por idade
                # Verificar se ao menos pagou 5% do SM
                valor_minimo_5 = round(sm * 0.05, 2)
                val_pago = contribuicao if contribuicao else 0
                if val_pago >= (valor_minimo_5 - 0.05):
                    continue  # OK, FBR validado e 5% pago -> mês conta
                # Se pagou menos que 5%, algo está errado — gerar GPS com código ORIGINAL
                diff = round(valor_minimo_5 - val_pago, 2)
                if tipo_filiado == 'Facultativo':
                    # Facultativo: sempre código original (ex: 1929 p/ FBR)
                    final_code = codigo_original or '1929'
                else:
                    final_code = '1295'
                final_value = diff
                motivo = f"FBR validado mas abaixo 5% (Devido {fmt_val(valor_minimo_5)} - Pago {fmt_val(val_pago)})"

            elif has_fbr_nao_validado:
                # FBR NÃO validado -> SEMPRE gerar GPS 1830 (5%->11%) = SM × 6%
                # Regra: para Aposentadoria por Idade, 5% não basta se FBR não é validado.
                # O segurado precisa complementar até 11% do SM.
                # Se também pagou abaixo de 5%, gerar GPS 1929 ADICIONAL para o déficit.

                val_pago = contribuicao if contribuicao else 0
                valor_minimo_5 = round(sm * 0.05, 2)

                # 1) GPS 1830: SEMPRE — complemento fixo de 5% para 11% = SM × 6%
                valor_1830 = round(sm * 0.06, 2)
                if '1830' not in rows_by_code:
                    rows_by_code['1830'] = []
                rows_by_code['1830'].append(HTML_ROW.format(
                    competencia=comp_str,
                    codigo='1830',
                    valor=fmt_val(valor_1830),
                ))

                # 2) GPS 1929: SOMENTE se pagou ABAIXO de 5% do SM (déficit no pagamento base)
                if val_pago < (valor_minimo_5 - 0.05):
                    diff_5 = round(valor_minimo_5 - val_pago, 2)
                    code_deficit = '1929'
                    if code_deficit not in rows_by_code:
                        rows_by_code[code_deficit] = []
                    rows_by_code[code_deficit].append(HTML_ROW.format(
                        competencia=comp_str,
                        codigo=code_deficit,
                        valor=fmt_val(diff_5),
                    ))

                continue  # Já adicionamos as rows diretamente, pular lógica final

            else:
                # LC123 puro sem FBR -> validar >= 11% do SM
                valor_minimo_11 = round(sm * 0.11, 2)
                val_pago = contribuicao if contribuicao else 0

                # Tolerância de centavos
                if val_pago >= (valor_minimo_11 - 0.05):
                    continue

                diff = round(valor_minimo_11 - val_pago, 2)
                # Abaixo do mínimo: Facultativo -> código original (1473, 1406, etc.)
                # CI -> 1295 (CI LC123 Compl.)
                # OBS: 1686 NÃO é para déficit — é para upgrade 11%->20% (9% faltantes)
                if tipo_filiado == 'Facultativo':
                    final_code = codigo_original or '1473'
                else:
                    final_code = '1295'
                final_value = diff
                motivo = f"LC123 abaixo 11% do Mínimo (Devido {fmt_val(valor_minimo_11)} - Pago {fmt_val(val_pago)})"

        # ---------------------------------------------------------------
        # REGRA 3: PREC-MENOR-MIN / PSC-MEN-SM-EC103 (Abaixo do mínimo)
        # ---------------------------------------------------------------
        elif 'PREC-MENOR-MIN' in indicadores or 'PSC-MEN-SM-EC103' in indicadores:
            # Alíquota conforme código de pagamento do segurado
            if codigo_original == '1929':
                aliquota_devida = 0.05   # FBR 5%
            elif codigo_original in ('1473', '1163'):
                aliquota_devida = 0.11   # LC123 / CI 11%
            else:
                aliquota_devida = 0.20   # Padrão 20% (1007, 1406, etc.)

            valor_devido = round(sm * aliquota_devida, 2)
            val_pago = contribuicao if contribuicao else 0
            diff = round(valor_devido - val_pago, 2)

            if diff <= 0.05:
                continue  # Diferença desprezível

            if is_post_reforma and not is_decadente:
                # CENÁRIO A: DARF / Meu INSS
                text_report.append(
                    f"- {comp_str}: Pago R$ {fmt_val(val_pago)}, "
                    f"Devido R$ {fmt_val(valor_devido)} (SM {fmt_val(sm)} x {int(aliquota_devida*100)}%). "
                    f"-> Ajustar no Meu INSS."
                )
                continue
            else:
                # CENÁRIO B: GPS (Pré-Reforma)
                
                # SE FOR EMPREGADO / DOMÉSTICO / AVULSO:
                # A responsabilidade é do empregador. O segurado NÃO paga complemento.
                # O tempo CONTA (exceto se houver fraude, mas a falta de pagamento não penaliza o empregado).
                if tipo_filiado in ('Empregado', 'Doméstico', 'Avulso'):
                     # Pode-se logar um aviso, mas NÃO gerar GPS.
                     # text_report.append(f"Aviso: {comp_str} (Empregado) abaixo do mínimo. Tempo conta normal.")
                     continue

                # SE FOR CI / FACULTATIVO:
                # Precisa complementar.
                # Facultativo: SEMPRE código original (1406/1473/1929), prescrito ou não
                # CI: 1902 se decadente, 1007 se não
                if tipo_filiado == 'Facultativo':
                    final_code = codigo_original or '1406'
                elif is_decadente:
                    final_code = '1902'
                else:
                    final_code = '1007'
                final_value = diff
                motivo = f"Abaixo do mín ({tipo_filiado}). (Devido {fmt_val(valor_devido)} - Pago {fmt_val(val_pago)})"

        # ---------------------------------------------------------------
        # REGRA 4: CI (código 1007) com valor pago < 20% do SM
        #          Sem indicador específico — usa código do contribuição
        # ---------------------------------------------------------------
        elif codigo_original == '1007':
            valor_devido_20 = round(sm * 0.20, 2)
            val_pago = contribuicao if contribuicao else 0

            if val_pago >= (valor_devido_20 - 0.05):
                continue  # OK

            diff = round(valor_devido_20 - val_pago, 2)

            if is_post_reforma and not is_decadente:
                text_report.append(
                    f"- {comp_str}: CI pago R$ {fmt_val(val_pago)}, "
                    f"Devido R$ {fmt_val(valor_devido_20)} (SM {fmt_val(sm)}). "
                    f"-> Ajustar no Meu INSS."
                )
                continue
            else:
                final_code = '1902' if is_decadente else '1007'
                final_value = diff
                motivo = f"CI abaixo 20% (Devido {fmt_val(valor_devido_20)} - Pago {fmt_val(val_pago)})"

        # ---------------------------------------------------------------
        # REGRA 5: CI 11% (código 1163) -> Aposentadoria Idade: Validar >= 11%
        # ---------------------------------------------------------------
        elif codigo_original == '1163':
            valor_minimo_11 = round(sm * 0.11, 2)
            val_pago = contribuicao if contribuicao else 0

            if val_pago >= (valor_minimo_11 - 0.05):
                continue
            
            diff = round(valor_minimo_11 - val_pago, 2)
            final_code = '1295'
            final_value = diff
            motivo = f"CI 11% abaixo do Mínimo (Devido {fmt_val(valor_minimo_11)} - Pago {fmt_val(val_pago)})"

        # ---------------------------------------------------------------
        # REGRA 6: MEI via código (1066) sem indicador no painel
        # ---------------------------------------------------------------
        elif codigo_original == '1066':
            final_code = '1910'
            final_value = round(sm * 0.15, 2)
            motivo = f"MEI 5%->20% via código (SM {fmt_val(sm)} × 15%)"

        # ---------------------------------------------------------------
        # REGRA 7: Facultativo (1406, 1473, 1929)
        # ---------------------------------------------------------------
        elif codigo_original in ('1406', '1473', '1929'):
            # Se for 1473 ou 1929 (Baixa Renda), a alíquota base é 11% (ou 5% para baixa renda, mas 1473 é 11%).
            # Se for 1406, é 20%.
            
            if codigo_original == '1473':
                aliquota_esperada = 0.11
            elif codigo_original == '1929':
                # Facultativo Baixa Renda é 5%. Mas se estiver validando para aposentadoria por idade, 
                # 5% conta.
                # Se a intenção for apenas validar o recolhimento mínimo:
                aliquota_esperada = 0.05
            else:
                aliquota_esperada = 0.20

            valor_devido = round(sm * aliquota_esperada, 2)
            val_pago = contribuicao if contribuicao else 0

            if val_pago >= (valor_devido - 0.05):
                continue

            diff = round(valor_devido - val_pago, 2)
            final_code = codigo_original
            final_value = diff
            motivo = f"Facultativo ({int(aliquota_esperada*100)}%) abaixo mín."

        # ---------------------------------------------------------------
        # REGRA 8: FBR 1929->11% (código 1830)
        # ---------------------------------------------------------------
        elif codigo_original == '1830':
            final_code = '1830'
            final_value = round(sm * 0.06, 2)  # Complemento fixo: SM × 6%
            motivo = f"FBR 5%->11% (SM {fmt_val(sm)} x 6%)"

        # ---------------------------------------------------------------
        # Nenhuma regra aplicável
        # ---------------------------------------------------------------
        else:
            continue

        # --- Cenário A/B para complementações (1910, 1295, 1830, Fac.) ---
        # Complementações NÃO têm trava de Cenário A. Vão sempre para GPS.
        # (Conforme Seção 4 do prompt: "Complementações de alíquota pura,
        #  que não sejam meramente para atingir o mínimo" -> GPS)

        if final_code and final_value is not None and final_value > 0:
            if final_code not in rows_by_code:
                rows_by_code[final_code] = []

            rows_by_code[final_code].append(HTML_ROW.format(
                competencia=comp_str,
                codigo=final_code,
                valor=fmt_val(final_value),
            ))

    return rows_by_code, text_report, warnings_extemporaneos


# ===========================================================================
# GERAÇÃO DE SAÍDA
# ===========================================================================
def gerar_saida(rows_by_code, text_report, warnings_extemporaneos, output_dir='.'):
    """Gera arquivos HTML e exibe relatório DARF e alertas."""

    print("\n" + "=" * 60)
    print("  RESULTADO DO PROCESSAMENTO")
    print("=" * 60)

    if rows_by_code:
        print("\n--- ARQUIVOS GPS GERADOS ---")
        for code in sorted(rows_by_code.keys()):
            rows = rows_by_code[code]
            filename = os.path.join(output_dir, f"Gps_{code}.html").replace('\\', '/')
            content = HTML_HEADER + '\n' + '\n'.join(rows) + '\n' + HTML_FOOTER
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  [OK] {filename} ({len(rows)} competencias)")
    else:
        print("\n  [--] Nenhum arquivo GPS gerado.")

    if text_report:
        print("\n--- RELATORIO DARF (MEU INSS) ---")
        print("[!!] As competencias abaixo sao Pos-Reforma e < 5 anos.")
        print("     Devem ser ajustadas via Meu INSS, NAO por GPS manual.\n")
        for line in text_report:
            print(f"  {line}")
        print()
        print('  -> Orientacao ao segurado:')
        try:
            meses = ', '.join(line.split(':')[0].replace('- ', '') for line in text_report)
        except:
             meses = "as competencias acima"
        print(f'    "Acesse o Meu INSS -> Ajustes para Alcance do Salario Minimo.')
        print(f'     Selecione as competencias pendentes e gere a guia (DARF)."')
    else:
        print("\n  [--] Nenhuma competencia para ajuste via DARF/Meu INSS.")

    if warnings_extemporaneos:
        print("\n" + "!" * 60)
        print(" ALERTA: COMPETENCIAS EXTEMPORANEAS / PENDENTES")
        print("!" * 60)
        print(" As seguintes competencias possuem indicadores que podem exigir")
        print(" comprovacao documental (holerites, CTPS) alem do pagamento:")
        print("")
        for w in warnings_extemporaneos:
            print(f"  {w}")
        print("!" * 60)

    print("\n" + "=" * 60)


# ===========================================================================
# MAIN
# ===========================================================================
def main():
    """
    Uso:
      py process_cnis_v2.py <painelCidadao.pdf> <contribuicaoRecolhimento.pdf>

    Ou, se os arquivos estiverem na pasta 'anexos/':
      py process_cnis_v2.py
    """
    # Determinar caminhos dos PDFs
    if len(sys.argv) >= 3:
        painel_path = sys.argv[1]
        contrib_path = sys.argv[2]
    else:
        # Buscar na pasta anexos/ por padrão
        base_dir = os.path.dirname(os.path.abspath(__file__))
        anexos_dir = os.path.join(base_dir, 'anexos')

        painel_path = None
        contrib_path = None

        if os.path.isdir(anexos_dir):
            for f in os.listdir(anexos_dir):
                fl = f.lower()
                if 'painel' in fl and fl.endswith('.pdf'):
                    painel_path = os.path.join(anexos_dir, f)
                elif 'contribui' in fl and fl.endswith('.pdf'):
                    contrib_path = os.path.join(anexos_dir, f)

        if not painel_path or not contrib_path:
            print("Uso: py process_cnis_v2.py <painelCidadao.pdf> <contribuicaoRecolhimento.pdf>")
            print("Ou coloque os PDFs na pasta 'anexos/'.")
            sys.exit(1)

    print(f"[PDF] Painel Cidadao:  {painel_path}")
    print(f"[PDF] Contribuicao:    {contrib_path}")
    print(f"[DAT] Data de hoje:    {DATA_HOJE.strftime('%d/%m/%Y')}")
    print(f"[DAT] Limite 5 anos:   {DATA_DECADENCIA_5Y.strftime('%d/%m/%Y')}")

    # Extrair texto dos PDFs
    texto_painel = extrair_texto_pdf(painel_path)
    texto_contrib = extrair_texto_pdf(contrib_path)

    # Parsear
    dados_painel = parse_painel_cidadao(texto_painel)
    dados_contrib = parse_contribuicao_recolhimento(texto_contrib)

    print(f"\n[INF] Competencias no Painel:      {len(dados_painel)}")
    print(f"[INF] Competencias no Contribuicao: {len(dados_contrib)}")

    # Processar regras de negócio
    output_dir = os.path.dirname(os.path.abspath(__file__))
    rows_by_code, text_report, warnings_extemporaneos = processar(dados_painel, dados_contrib)

    # Gerar saída
    gerar_saida(rows_by_code, text_report, warnings_extemporaneos, output_dir)


if __name__ == '__main__':
    main()
