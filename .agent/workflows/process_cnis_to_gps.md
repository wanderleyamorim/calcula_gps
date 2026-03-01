---
description: Workflow completo para processar CNIS e gerar GPS/DARF
---

# Workflow: Processar CNIS para GPS/DARF (Completo)

// turbo-all

1. **Obter Dados**
   - Solicitar ao usuário os 2 PDFs:
     - `painelCidadao.pdf` (Extrato CNIS com indicadores)
     - `contribuicaoRecolhimentoResultado.pdf` (Detalhes de pagamento com códigos GPS)
   - Salvar na pasta `anexos/`.

2. **Processar**
   - Executar: `py process_cnis_v2.py`
   - O script cruza os dados dos 2 PDFs e aplica as regras de negócio automaticamente.
   - Resumo no console:
     - Cenário B (GPS): Arquivos `Gps_XXXX.html` gerados.
     - Cenário A (DARF): Relatório de texto exibido.

3. **Entregar ao Usuário**
   - Listar arquivos HTML gerados e orientar importação na extensão Ajudante Salweb.
   - Se houver competências DARF, copiar o texto de orientação para o usuário.
   - Se houver **ALERTAS EXTEMPORÂNEOS**, informar que é necessário comprovação documental.

4. **Conclusão**
   - Avisar "Processo concluído".
   - Perguntar se deseja processar outro CNIS.
