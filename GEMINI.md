# Projeto Calcula GPS - Arquitetura de 21 Especialistas (v5.0)

Este projeto foi reestruturado para máxima eficácia, utilizando 21 Skills independentes baseadas em prompts rigorosamente testados.

## 🏗️ Estrutura
- **Motor Central (`engine_inss.py`):** Fornece dados JSON limpos dos PDFs em `anexos/`.
- **Skills (21 ferramentas):** Cada uma possui a instrução integral do seu respectivo cenário (B41, B42, CI, Rural, Facultativo, etc) e a tabela SM completa.
- **Roteador (`/calcula`):** Identifica a intenção do usuário e chama a skill exata.

## 🚀 Como Funciona
1. O usuário relata o problema (ex: "Complementar CI 1163 urbano").
2. O comando `/calcula` ativa a `skill-ci-11-1163`.
3. A skill lê os dados via `engine_inss.py --json`.
4. A IA aplica a regra específica daquela skill e gera o HTML final.

## 📜 Categorias de Skills
- **Cenários Gerais:** B41, B42, Pós-Reforma.
- **Facultativos:** 1406, 1473, 1929 e Upgrades (1686, 1830, 1945, 1821).
- **CI Urbano:** 1007, 1120, 1163, 1295, 1910 (MEI), 1902 (Decadência).
- **CI Rural:** 1287, 1236, 1244, 1805.

---
*Última atualização: 06/04/2026*
