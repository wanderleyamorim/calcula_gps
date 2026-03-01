---
description: Workflow Principal - Processar CNIS para HTML (Multi-arquivo)
---

# Workflow: Processar CNIS para GPS/DARF

// turbo-all

1. **Preparação**
   - Verificar se Python está instalado: `py --version`
   - Solicitar ao usuário os 2 PDFs: `painelCidadao.pdf` e `contribuicaoRecolhimentoResultado.pdf`
   - Salvar os PDFs na pasta `anexos/`

2. **Processamento**
   - Garantir que `process_cnis_v2.py` existe na raiz do workspace.
   - Executar: `py process_cnis_v2.py`
   - O script automaticamente encontra os PDFs em `anexos/`.

3. **Entrega**
   - Identificar os arquivos gerados (ex: `Gps_1910.html`, `Gps_1902.html`, `Gps_1295.html`).
   - Informar ao usuário quais arquivos importar na extensão Ajudante Salweb.
   - Exibir o Relatório DARF (Cenário A) caso o script aponte competências pós-reforma.
   - Exibir **ALERTAS EXTEMPORÂNEOS** caso existam indicadores de pendência.
