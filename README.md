# Calcula GPS  🦅

Este projeto é uma ferramenta de automação construída para ler extratos do CNIS (Painel do Cidadão + Contribuição/Recolhimento) e gerar automaticamente os arquivos HTML de GPS (Guia da Previdência Social) prontos para importação no sistema SAL (Sistema de Acréscimos Legais) da Receita Federal.

⚠️ **DISCLAIMER OFICIAL E RESPONSABILIDADE DOS DADOS** ⚠️

Esta ferramenta **NÃO** é uma aplicação oficial do Governo Federal ou do INSS. É um projeto auxiliar construído de servidor para servidor, focado em agilidade e produtividade no serviço público.

**Atenção Servidor:** Ao lidar com dados sensíveis de cidadãos brasileiros (CPFs, NBs, Nomes, Informações Previdenciárias e Bancárias), o servidor público federal está sob o escopo rígido da **Lei Geral de Proteção de Dados (LGPD)** e dos normativos internos de segurança da informação do Governo.

**Este repositório e seus criadores não assumem qualquer responsabilidade pelo uso indevido da ferramenta.** O uso deste script não exime o servidor de sua responsabilidade legal e funcional. **Nenhum dado real de segurado (PDFs de CNIS, extratos, etc.) deve ser comitado, publicado ou transmitido** através de repositórios públicos, servidores externos ou modelos de IA não homologados.

Ao baixar e utilizar este código, o servidor assume **inteira e exclusiva responsabilidade** pela segurança dos dados processados em sua máquina local e pela conferência dos valores e códigos gerados antes de apresentá-los ao segurado.

## 🛡️ Segurança e Privacidade (Privacy-First)

A arquitetura do projeto foi desenhada para processamento **100% local**:

1. **Motor Local Python:** O script `process_cnis_v2.py` lê os PDFs e gera os HTMLs localmente na máquina do servidor. Nenhum dado de CNIS é enviado para a nuvem.
2. **Isolamento de Dados:** O arquivo `.gitignore` restringe severamente os arquivos que são versionados. A pasta `anexos/` (onde os PDFs dos segurados devem ser colocados) é sumariamente ignorada pelo Git.
3. **Regras de Negócio Injetadas:** As regras (CI vs Facultativo, LC123, FBR, etc.) estão centralizadas localmente, garantindo que o cruzamento de indicadores do CNIS obedeça estritamente à legislação previdenciária sem depender de APIs externas para a lógica central.

## 📁 Estrutura de Diretórios e Ocultamento

Os dados privados **NÃO** fazem parte deste repositório e nunca devem ser versionados.

- `process_cnis_v2.py`: Script principal de faturamento e regras de GPS.
- `.agents/rules/memory.md`: Documentação viva das regras de negócio do INSS aplicadas no código (Códigos de CI vs Facultativo, etc).
- `anexos/`: **[IGNORADO PELO GIT]** Repositório local secreto onde os PDFs (Painel Cidadão, Contribuição) devem ser colocados pelo servidor para processamento temporário.
- `*.html`: **[IGNORADO PELO GIT]** As guias geradas são ignoradas para evitar vazamento acidental de dados previdenciários.

Feito de servidor para servidor, focado em precisão matemática, segurança e privacidade no cumprimento legal.
