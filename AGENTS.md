# AGENTS.md — Regras de trabalho do repositório

## Contexto do projeto
1. Este projeto é um MVP local chamado **PM Companion**.
2. Priorizar simplicidade, clareza e separação de responsabilidades.

## Restrições de escopo (obrigatórias)
3. Não adicionar IA generativa, RAG, vector database, autenticação ou integrações externas sem pedido explícito.
4. Manter backend em **Python + FastAPI**.
5. Manter banco em **SQLite + SQLAlchemy**.
6. Manter frontend em **HTML/CSS/JS puro**.
7. Não introduzir frameworks frontend como React, Vue ou Angular nesta fase.

## Compatibilidade e evolução
8. Toda nova feature deve preservar os endpoints existentes.
9. Toda função relevante deve ter tratamento básico de erro.
10. Não quebrar uploads existentes.
11. Qualquer extração de item PM deve manter vínculo com documento e projeto.
12. Alertas devem ser rastreáveis até item ou documento de origem sempre que possível.

## Documentação e qualidade
13. Se fizer alteração no schema do banco, explicar no README.
14. Sempre atualizar o README quando mudar instalação, execução ou uso.
15. Antes de concluir uma task, rodar uma validação básica do projeto.
