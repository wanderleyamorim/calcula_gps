#!/bin/bash
# Hook de pré-sessão do Gemini CLI para o projeto Calcula GPS
# Identifica novos arquivos na pasta anexos/ e informa ao contexto.

ANEXOS_DIR="$GEMINI_PROJECT_DIR/anexos"
if [ ! -d "$ANEXOS_DIR" ]; then
  exit 0
fi

# Lista arquivos com data de modificação e tamanho
FILES=$(ls -lh "$ANEXOS_DIR"/*.pdf 2>/dev/null)

if [ -z "$FILES" ]; then
  CONTEXT="A pasta 'anexos/' está vazia. Informe ao usuário que ele deve colocar os novos PDFs do CNIS lá antes de começar."
else
  CONTEXT="Novos arquivos detectados na pasta 'anexos/':\n$FILES\n\nEstes são os PDFs que o usuário quer que você processe hoje. Use a skill 'gps-agent' para analisá-los assim que o usuário der o comando."
fi

# Retorna JSON conforme especificação do Gemini CLI
echo "{\"hookSpecificOutput\": {\"additionalContext\": \"$CONTEXT\"}}"
