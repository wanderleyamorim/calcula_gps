# Calcula GPS 🦅 (v5.0)

Este projeto é uma ferramenta de automação construída para ler extratos do CNIS (Painel do Cidadão + Contribuição/Recolhimento) e gerar automaticamente os arquivos HTML de GPS (Guia da Previdência Social) prontos para importação no sistema SAL (Sistema de Acréscimos Legais) da Receita Federal.

Utilizamos o **Gemini CLI** integrado diretamente ao **VS Code** para orquestrar 21 especialidades previdenciárias de forma autônoma e precisa.

⚠️ **DISCLAIMER OFICIAL E RESPONSABILIDADE DOS DADOS** ⚠️

Esta ferramenta **NÃO** é uma aplicação oficial do Governo Federal ou do INSS. É um projeto auxiliar construído de servidor para servidor, focado em agilidade e produtividade no serviço público.

**Atenção Servidor:** Ao lidar com dados sensíveis de cidadãos brasileiros, você está sob o escopo rígido da **LGPD**. **Nenhum dado real de segurado (PDFs, CPFs) deve ser comitado ou publicado.** A pasta `anexos/` é ignorada pelo Git por padrão.

## 🏗️ Arquitetura Modular (Privacy-First)

A versão 5.0 introduz uma separação total entre a extração de dados e as regras de negócio:

1.  **Motor Central (`engine_inss.py`):** Script Python que extrai dados dos PDFs e fornece um JSON limpo.
2.  **21 Skills Especializadas:** Cada regra legal (B41, B42, CI, Rural, Facultativo, etc.) possui sua própria Skill no Gemini CLI, garantindo assertividade matemática e legal.
3.  **Orquestrador (`/calcula`):** Comando central que identifica o seu pedido e aciona o especialista correto.

## 📁 Estrutura do Projeto (.gemini)

- `.gemini/skills/`: Contém as 21 ferramentas especializadas (ex: `skill-ci-20-1007`, `skill-facultativo-upgrade-1686`).
- `.gemini/commands/`: Ponto de entrada via comando `/calcula`.
- `engine_inss.py`: O novo motor de extração de dados.
- `MANUAL.md`: Guia completo de todos os comandos e códigos disponíveis.
- `anexos/`: **[PRIVADO]** Local onde você coloca os PDFs para processamento.

## 🚀 Como Usar no VS Code

1.  Coloque os PDFs em `anexos/`.
2.  Inicie o **Gemini CLI**.
3.  Use o comando `/calcula` seguido do problema:
    - *"/calcula B42 para 20%"*
    - *"/calcula complementar facultativo 1473"*
    - *"/calcula períodos decadentes acima de 5 anos"*

Feito de servidor para servidor, focado em precisão matemática, segurança e privacidade no cumprimento legal.
