# 📖 MANUAL DO USUÁRIO - Agente GPS INSS (v5.0)

Este projeto utiliza uma arquitetura de **21 Skills Independentes** e um **Motor de Extração Central** para garantir 100% de assertividade nos cálculos de GPS.

## 🚀 Como Iniciar um Cálculo
Basta utilizar o comando `/calcula` seguido do seu problema. O sistema identificará automaticamente qual das 21 ferramentas usar.

**Exemplos:**
- `/calcula B42 para 20%`
- `/calcula complementar facultativo 1473`
- `/calcula MEI código 1910`
- `/calcula períodos decadentes acima de 5 anos`

---

## 🛠️ Comandos e Fluxo de Trabalho
1.  **Coloque os PDFs:** Salve o "Painel do Cidadão" e a "Relação de Contribuições" na pasta `anexos/`.
2.  **Execute o Comando:** Use o `/calcula`.
3.  **Resultado:** O sistema gerará a tabela HTML formatada para o **Ajudante Salweb**.

---

## 🧭 Lista de Especialidades (Skills)

### 1. Cenários Gerais
- **Validação 11% (B41):** Focado em aposentadoria por idade e acerto de FBR (1830).
- **Upgrade 20% (B42):** Focado em aposentadoria por tempo.
- **Pós-Reforma (DARF):** Orienta ajustes via Meu INSS para meses após 11/2019.

### 2. Facultativos
- **Plano Normal (1406):** Complementação de 20%.
- **Plano Simplificado (1473):** Complementação de 11%.
- **Baixa Renda (1929):** Complementação de 5%.
- **Upgrades:** 1686 (11->20%), 1830 (5->11%), 1945 (5->20%).

### 3. Contribuinte Individual (CI) Urbano
- **Plano Normal (1007):** 20%.
- **Dedução 45% (1120):** Prestadores de serviço a empresas.
- **Simplificado (1163):** 11%.
- **MEI (1910):** Complemento de 15%.
- **Decadência (1902):** Períodos acima de 5 anos.

### 4. Contribuinte Individual (CI) Rural
- **Normal Rural (1287):** 20%.
- **Simplificado Rural (1236):** 11%.
- **Upgrade Rural (1244):** 11% para 20%.
- **Dedução Rural (1805):** 45% de dedução.

---

## ⚠️ Regras de Ouro do Sistema
- **Concomitância:** O sistema ignora meses que já possuem um vínculo regular suficiente.
- **Tabelas de SM:** Todos os agentes possuem a tabela histórica de 1994 a 2026 embutida.
- **Formatação:** A saída será sempre uma tabela HTML com `id="tabela"`, pronta para a extensão de importação.

---
*Dúvidas? Basta perguntar ao Agente GPS!*
