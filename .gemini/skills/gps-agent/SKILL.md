---
name: gps-agent
description: Agente autônomo para processamento de extratos CNIS e geração de guias GPS do INSS. Identifica automaticamente cenários (B41, B42, FBR, MEI, LC123) e decide as regras de cálculo.
---

# Agente GPS - INSS

Este agente orquestra o cálculo de guias de GPS do INSS baseado nos PDFs de extratos do CNIS encontrados na pasta `anexos/`.

## 🧠 Inteligência e Tomada de Decisão

Este agente NÃO deve ser limitado por comandos específicos. Ele deve:
1. **Identificar os Arquivos:** Verificar o conteúdo da pasta `anexos/`.
2. **Executar o Cálculo:** Rodar o script `process_cnis_v2.py` para obter o log inicial.
3. **Analisar Erros e Peculiaridades:**
    - Erros de competência extemporânea.
    - Indicadores críticos (IREC-MEI, IREC-LC123, PREC-FBR, PREC-MENOR-MIN).
    - Diferenciar entre cenários de Aposentadoria por Idade (B41) e Tempo de Contribuição (B42) se o usuário mencionar ou se os dados sugerirem.
4. **Decidir a Regra de Cálculo:**
    - **B41:** Aceita alíquotas de 5% e 11%. Só gera complemento se houver déficit.
    - **B42:** NÃO aceita alíquotas de 11%. Deve-se gerar complemento de 9% (Código 1686/1295) ou conforme legislação.
    - **FBR (Facultativo Baixa Renda):** Se não validado (PREC-FBR), gerar complemento 5% para 11% (Código 1830).
    - **MEI:** Se 5% é insuficiente, complementar para 20% (Código 1910).
5. **Gerar e Validar:** Confirmar a criação dos arquivos `Gps_XXXX.html` e resumir o que foi feito para o servidor.

## 📋 Tabela de Códigos e Regras

| Situação | Alíquota | Código GPS | Regra |
| :--- | :--- | :--- | :--- |
| **MEI** | 5% → 20% | `1910` | Complemento 15% |
| **LC123 / CI 11%** | 11% | `1295` | Complemento se abaixo do SM |
| **B42 Upgrade** | 11% → 20% | `1686`/`1295` | B42 exige alíquota cheia |
| **FBR não validado** | 5% → 11% | `1830` | PREC-FBR exige upgrade |
| **Decadente (> 5 anos)** | 20% SM | `1902` | CI sem contribuição |

## 🚀 Workflow do Agente

1. Liste os arquivos em `anexos/`.
2. Execute o script principal: `!{python3 process_cnis_v2.py}`.
3. Analise o output detalhadamente.
4. Se o usuário disser "B42", procure por alíquotas de 11% e gere as orientações ou guias extras (se o script ainda não suportar o código 1686 automaticamente).
5. Explique resumidamente o que foi calculado e quais guias estão prontas para importação no SAL.
