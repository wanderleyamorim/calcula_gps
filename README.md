# Calcula GPS 🦅

Este projeto é uma ferramenta de automação construída para ler extratos do CNIS (Painel do Cidadão + Contribuição/Recolhimento) e gerar automaticamente os arquivos HTML de GPS (Guia da Previdência Social) prontos para importação no sistema SAL (Sistema de Acréscimos Legais) da Receita Federal.

Utilizamos o **Gemini CLI** integrado diretamente ao **VS Code** (ou qualquer IDE) para orquestrar as regras de negócio de forma autônoma e inteligente.

⚠️ **DISCLAIMER OFICIAL E RESPONSABILIDADE DOS DADOS** ⚠️

Esta ferramenta **NÃO** é uma aplicação oficial do Governo Federal ou do INSS. É um projeto auxiliar construído de servidor para servidor, focado em agilidade e produtividade no serviço público.

**Atenção Servidor:** Ao lidar com dados sensíveis de cidadãos brasileiros (CPFs, NBs, Nomes, Informações Previdenciárias e Bancárias), o servidor público federal está sob o escopo rígido da **Lei Geral de Proteção de Dados (LGPD)** e dos normativos internos de segurança da informação do Governo.

**Este repositório e seus criadores não assumem qualquer responsabilidade pelo uso indevido da ferramenta.** O uso deste script não exime o servidor de sua responsabilidade legal e funcional. **Nenhum dado real de segurado (PDFs de CNIS, extratos, etc.) deve ser comitado, publicado ou transmitido** através de repositórios públicos, servidores externos ou modelos de IA não homologados.

## 🛡️ Segurança e Privacidade (Privacy-First)

A arquitetura do projeto foi desenhada para processamento **100% local**:

1. **Motor Local Python:** O script `process_cnis_v2.py` lê os PDFs e gera os HTMLs localmente na máquina do servidor. Nenhum dado de CNIS é enviado para a nuvem.
2. **Orquestração via Gemini CLI:** O projeto utiliza a estrutura `.gemini/` para automatizar tarefas via Agente Autônomo, garantindo que as regras de negócio (B41, B42, FBR, etc.) sejam aplicadas corretamente sem intervenção manual constante.
3. **Isolamento de Dados:** A pasta `anexos/` (onde os PDFs dos segurados devem ser colocados) é ignorada pelo Git para sua total segurança.

## 📁 Estrutura do Projeto (.gemini)

O projeto é potencializado pelo **Gemini CLI**, permitindo um workflow de "Agente Autônomo":

- `.gemini/hooks/`: Automatiza o carregamento de arquivos da pasta `anexos/`.
- `.gemini/skills/gps-agent/`: Skill inteligente que detém o conhecimento das regras previdenciárias.
- `.gemini/commands/`: Ponto de entrada simplificado via comando `/calcula`.
- `anexos/`: **[PRIVADO]** Local onde você coloca os PDFs para processamento.

## 🚀 Como Usar no VS Code

1. Abra o projeto no **VS Code**.
2. Abra o terminal integrado e inicie o **Gemini CLI** (`gemini`).
3. Coloque os PDFs em `anexos/`.
4. Basta falar o problema: *"B41, analise os erros"* ou *"B42, complemente 11% para 20%"*.

Feito de servidor para servidor, focado em precisão matemática, segurança e privacidade no cumprimento legal.
