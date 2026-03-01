---
trigger: always_on
---

# AGENTS.md — Memória Central do Projeto DARF e GPS

> **ATENÇÃO AGENTE:** Este documento contém **TUDO O QUE FUNCIONA** neste projeto. Siga-o cegamente.
> Se você "voltar amanhã", leia isto primeiro.

---

## 1. O Objetivo

Gerar arquivos HTML para a extensão **"Ajudante Salweb"** a partir de extratos do CNIS.

- **Entrada**: 2 PDFs (`painelCidadao.pdf` + `contribuicaoRecolhimentoResultado.pdf`).
- **Saída**: Arquivos `Gps_XXXX.html` (para importar no SAL) ou texto de orientação DARF.

---

## 2. A "Bíblia" do Processamento

### Script Mestre: `process_cnis_v2.py`

Este script foi reescrito (v3.0) e é a única fonte de verdade.

- **Onde está**: Na raiz do workspace.
- **Como rodar**: Coloque os 2 PDFs na pasta `anexos/` e execute:
  ```bash
  py process_cnis_v2.py
  ```
- **O que ele faz**:
  1. Lê os 2 PDFs (cruza indicadores do Painel com códigos da Contribuição).
  2. Aplica a Tabela SM histórica **correta** (1994-2026).
  3. Identifica o **Tipo Filiado** (Empregado, CI, Facultativo) de cada bloco.
  4. Gera HTMLs separados por código (`Gps_1910.html`, etc.).
  5. Avisa se houver casos de DARF (Cenário A).
  6. Alerta sobre competências **extemporâneas** (`PREM-EXT`, `IREC-INDPEND`).

### Workflow (Passo a Passo)

1. **Receber PDFs**: O usuário manda `painelCidadao.pdf` e `contribuicaoRecolhimentoResultado.pdf`.
2. **Salvar**: Sempre salve na pasta `anexos/` (crie se não existir).
3. **Executar**: Rode `py process_cnis_v2.py`.
4. **Entregar**:
   - Diga quais arquivos `.html` foram gerados.
   - Se o script der aviso de "Cenário A", mostre o texto para o usuário copiar.

---

## 3. Regras de Negócio (Já estão no script, mas saiba delas)

### Cenário A: DARF (Meu INSS)

- **Quando**: Pós-Reforma (> 13/11/2019) **E** menos de 5 anos da data de hoje.
- **Ação**: ⛔ NÃO gerar HTML. Instruir ajuste via Meu INSS.

### Cenário B: GPS (SAL)

- **Quando**: Pré-Reforma **OU** Decadente (> 5 anos) **OU** Complementação pura.
- **Ação**: ✅ Gerar HTML.

### Tabela OFICIAL de Códigos GPS — Contribuinte Individual (CI)

| Código | Descrição                              | Uso no Script                          |
| ------ | -------------------------------------- | -------------------------------------- |
| `1007` | CI Recolhimento Mensal (20%)           | Complemento abaixo do mín (não decad.) |
| `1120` | CI com Dedução 45%                     | _(não implementado)_                   |
| `1163` | CI Opção 11% (LC 123/2006)             | Validar ≥ 11% SM → compl. via `1295`   |
| `1236` | CI Optante LC 123 Mensal Rural         | _(não implementado)_                   |
| `1244` | CI Optante LC 123 Rural Complementação | _(não implementado)_                   |
| `1287` | CI Mensal Rural                        | _(não implementado)_                   |
| `1295` | **CI Optante LC 123 Mensal Compl** ⚠️  | Complemento LC123 **SÓ para CI**       |
| `1805` | CI com Direito a Dedução Mensal Rural  | _(não implementado)_                   |
| `1902` | Diferenças de Valores de Contribuições | Complemento decadente (genérico)       |
| `1910` | MEI Complementação Mensal              | MEI 5%→20% (SM × 15%)                  |

### Tabela OFICIAL de Códigos GPS — Facultativo

| Código | Descrição                                    | Uso no Script                                    |
| ------ | -------------------------------------------- | ------------------------------------------------ |
| Código | Descrição                                    | Uso no Script                                    |
| ------ | -------------------------------------------- | ------------------------------------------------ |
| `1406` | Facultativo Mensal (20%)                     | Complemento abaixo do mín (não decad.)           |
| `1473` | Facultativo Opção 11% (LC 123/2006)          | _(código pagamento, não de compl.)_              |
| `1686` | **Facultativo Optante LC 123 Compl** ⚠️      | Complemento LC123 **SÓ para Facult.**            |
| `1821` | Facultativo Exercente Mandato Eletivo Compl. | _(não implementado)_                             |
| `1830` | Facultativo Baixa Renda Compl. PSPS (5%→11%) | FBR não validado → SM × 6%                       |
| `1929` | Facultativo Baixa Renda Recolhimento Mensal  | Complemento déficit abaixo 5%                    |
| `1945` | Facultativo Baixa Renda Complemento          | _(não impl.)_ FBR 5%→20% p/ Apos. Tempo (SM×15%) |

### Regra-chave: NÃO misturar códigos CI ↔ Facultativo

> ⚠️ **NUNCA** usar código `1295` para Facultativo (usar `1686`).
> **NUNCA** usar código `1007` para Facultativo (usar `1406`).
> O script usa `tipo_filiado` (parseado do Painel Cidadão) para decidir.

### Regra CRÍTICA: Complementação abaixo do mínimo para Facultativo

> ⚠️ **Para Facultativo abaixo do mínimo**, o código GPS de complementação é **SEMPRE o código original** de pagamento (1929, 1473, 1406), independente de estar prescrito (>5 anos) ou não.
> **`1902`** (Diferenças) é **SÓ para CI** decadente.
> **`1686`** **NÃO** é para déficit — é **SÓ** para upgrade de plano (1473→1406, ou seja, 11%→20%, complementar os 9% faltantes).

### Resumo de Cálculos (Aposentadoria por Idade — 11%)

| Situação                      | CI     | Facultativo | Cálculo                   |
| ----------------------------- | ------ | ----------- | ------------------------- |
| **MEI (5% → 20%)**            | `1910` | —           | `SM × 15%`                |
| **LC123 abaixo 11% do SM**    | `1295` | `1686`      | `(SM × 11%) - Valor Pago` |
| **Abaixo do Mínimo (20%)**    | `1007` | `1406`      | `(SM × 20%) - Valor Pago` |
| **Decadente (> 5 anos)**      | `1902` | `1902`      | `(SM × 20%) - Valor Pago` |
| **FBR não validado (5%→11%)** | —      | `1830`      | `SM × 6%`                 |
| **FBR déficit (< 5%)**        | —      | `1929`      | `(SM × 5%) - Valor Pago`  |

### Regra FBR (Facultativo Baixa Renda) — CRÍTICA

| Indicador    | Significado             | Ação para Apos. por Idade                                                                              |
| ------------ | ----------------------- | ------------------------------------------------------------------------------------------------------ |
| **IREC-FBR** | FBR **validado** ✅     | 5% é suficiente → **NÃO gera GPS**                                                                     |
| **PREC-FBR** | FBR **NÃO validado** ❌ | Complementar 5%→11% → **GPS 1830** (SM×6%). Se também pagou <5%, gera **GPS 1929** adicional (déficit) |

### Regras de Categoria (Pré-Reforma + Abaixo do Mín)

| Tipo Filiado                       | Abaixo do Mín Pré-Reforma? | Ação                                         |
| ---------------------------------- | -------------------------- | -------------------------------------------- |
| **Empregado / Doméstico / Avulso** | **Ignora**                 | Tempo conta (responsabilidade do empregador) |
| **CI / Facultativo**               | **Gera GPS**               | Complemento obrigatório                      |

### Alertas Extemporâneos / Pendências

Quando encontra `PREM-EXT`, `IREC-INDPEND`, `IREC-GFIP`, `PREC-FBR` ou `PREC-FACULTCONC`, o script exibe um **ALERTA** pedindo comprovação documental.

### Parser: Indicadores Órfãos em Quebra de Página

O PDF tem **2 colunas**. Quando há quebra de página, indicadores como `IREC-FBR` podem ficar "soltos" na próxima página, separados de sua competência. O parser faz um **pós-processamento** que detecta footers e re-associa indicadores órfãos às últimas competências.

### Parser: Tipo Filiado

O campo "Tipo Filiado" no PDF é uma tabela onde o valor (ex: "Facultativo") aparece ~6 linhas abaixo do header. O parser varre até 10 linhas à frente procurando tipos conhecidos (Empregado, CI, Facultativo, Doméstico, Avulso).

---

## 4. Estrutura de Arquivos

- `/process_cnis_v2.py`: O cérebro. **Único script de processamento.** Não mexa na lógica de SM sem certeza.
- `/anexos/`: Onde os PDFs do usuário devem ficar.
- `/skills/generate_sal_file.md`: Documentação para agentes (referência).
- `/.agent/workflows/`: Workflows para automação rápida (`/init` roda o processo).
- `/.agents/rules/memory.md`: Este arquivo — regras globais carregadas automaticamente.

---

**Última Atualização**: 01/03/2026 (Tabelas de códigos corrigidas: CI ↔ Facultativo separados; 1295→1686 e 1007→1406 para Facultativo; regras documentadas em memory.md).
