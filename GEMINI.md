# Calcula GPS — Memória do Projeto (Versão Agente Autônomo)

**INSS - Ferramenta de Cálculo de GPS** | **Última atualização:** 2026-04-02 (Abril/2026 Update)

---

## 🏗️ Arquitetura de Agente Autônomo (.gemini/)

Este projeto foi reestruturado para funcionar como um **Agente Inteligente**. Não usamos mais comandos limitados por tipo de benefício. Em vez disso, a IA decide o melhor caminho.

```
.gemini/
├── hooks/              # Automatização de Contexto
│   └── check-anexos.sh # Hook: Alimenta a IA com novos PDFs automaticamente.
│
├── skills/             # Inteligência do Agente
│   └── gps-agent/      # Agente GPS: Conhece todas as regras (B41, B42, FBR, MEI, LC123).
│
├── commands/           # Atalho de Entrada
│   └── calcula.toml    # /calcula - Ponto de entrada para qualquer análise.
│
└── settings.json       # Configuração de Hooks e Skills.
```

---

## 🚀 Como Usar (Workflow Moderno)

1. **Coloque os PDFs**: Salve os novos PDFs do segurado na pasta `anexos/`.
2. **Fale o que Precisa**: Basta iniciar a conversa com o problema, por exemplo:
   - *"B41, veja os erros e gere os html"*
   - *"B42, calcule de 11 para 20%"*
   - *"FBR não validado, calcule tudo de 5 para 11%"*
3. **IA Autônoma**: O hook `BeforeAgent` já terá informado à IA quais arquivos estão lá. A IA usará a skill `gps-agent` para processar o script, analisar os logs e gerar as guias corretas sem que você precise guiar o passo a passo.

---

## 📋 Regras de Inteligência (Agente GPS)

O **Agente GPS** é treinado para:
- Diferenciar **Idade (B41)** de **Tempo (B42)**.
- Identificar erros de **extemporâneas** e **abaixo do mínimo**.
- Resolver **PREC-FBR** (5% -> 11%) automaticamente.
- Calcular complementos de **MEI** e **LC123** quando necessário.
- Sugerir ajustes no **Meu INSS** para períodos pós-reforma não decadentes.

---

*Para recarregar o sistema após mudanças: `/commands reload` e `/skills reload`.*
