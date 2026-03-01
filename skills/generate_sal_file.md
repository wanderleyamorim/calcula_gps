---
name: generate_sal_file
description: Analisa CNIS (2 PDFs) via script Python e gera múltiplos arquivos HTML (por código GPS) para importação no SAL.
---

# Gerador de Arquivo SAL (Ajudante Salweb) - v3.0

O script `process_cnis_v2.py` é a **fonte única de verdade**. NÃO copie código aqui — apenas documente as regras.

## 1. Entradas Obrigatórias (2 PDFs)

| Arquivo                                 | Conteúdo                                                                                            |
| --------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `painelCidadao.pdf`                     | Extrato CNIS Cidadão — indicadores (`IREC-MEI`, `IREC-LC123`, `PREC-MENOR-MIN`, `PSC-MEN-SM-EC103`) |
| `contribuicaoRecolhimentoResultado.pdf` | Detalhes de pagamento — código GPS (`1007`, `1066`, etc.)                                           |

## 2. Cenários de Decisão

### Cenário A: DARF (Meu INSS)

- Competência **pós-reforma** (> 13/11/2019)
- E **< 5 anos** da data atual
- E problema é recolhimento abaixo do mínimo
- ⛔ NÃO gerar HTML → Gerar texto de orientação

### Cenário B: GPS (SAL)

- Competências **pré-reforma** OU **decadentes** (> 5 anos)
- OU complementações de alíquota pura (independe de decadência)
- ✅ Gerar HTML separado por código

## 3. Regras por Indicador/Código

| Indicador/Código                      | Ação             | Código GPS               | Valor (R$)                  |
| ------------------------------------- | ---------------- | ------------------------ | --------------------------- |
| `IREC-MEI`                            | MEI 5%→20%       | `1910`                   | SM × 15%                    |
| `IREC-LC123` (sem MEI)                | Validar ≥ 11% SM | `1295`                   | GPS **SÓ** se pago < 11% SM |
| `PREC-MENOR-MIN` / `PSC-MEN-SM-EC103` | Abaixo mínimo    | `1902` (decad.) / `1007` | (SM×20%) - pago             |
| CI `1007` com valor baixo             | Diferença        | `1902` (decad.) / `1007` | (SM×20%) - pago             |
| CI `1163` (11%)                       | Validar ≥ 11% SM | `1295`                   | GPS **SÓ** se pago < 11% SM |
| `1066` (MEI via código)               | MEI 5%→20%       | `1910`                   | SM × 15%                    |
| Facultativo `1406` (20%)              | Abaixo mín.      | `1406`                   | (SM×20%) - pago             |
| Facultativo `1473` (11%)              | Abaixo mín.      | `1473`                   | (SM×11%) - pago             |
| Facultativo `1929` (5% BR)            | Abaixo mín.      | `1929`                   | (SM×5%) - pago              |
| `1830` (FBR→11%)                      | 5%→11%           | `1830`                   | SC × 6%                     |

### Regras de Categoria (Pré-Reforma)

O script lê o **Tipo Filiado** do PDF:

- **Empregado / Doméstico / Avulso** + abaixo do mín pré-reforma → **Ignora** (tempo conta).
- **CI / Facultativo** + abaixo do mín pré-reforma → **Gera GPS**.

### Alertas Extemporâneos

Indicadores `PREM-EXT`, `IREC-INDPEND`, `IREC-GFIP` → Alerta pedindo comprovação documental.

## 4. Execução

```
py process_cnis_v2.py <painelCidadao.pdf> <contribuicaoRecolhimento.pdf>
```

Ou coloque os PDFs na pasta `anexos/` e rode sem argumentos.

## 5. Saída

- Arquivos `Gps_XXXX.html` separados por código (ex: `Gps_1910.html`, `Gps_1902.html`)
- Relatório de texto no console para competências Cenário A (DARF)

## 6. Tabela SM

A tabela de salário mínimo (1994-2026) está embutida no script com todas as transições por mês.
Verifique no script se o ano atual já está incluído. Se não, adicione.

**Última Atualização**: 13/02/2026 (v3.1 — Aposentadoria por Idade 11%, alertas extemporâneos, distinção Empregado/CI).
