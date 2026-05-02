# PM Companion MVP

Aplicação local para apoiar PMs/POs na análise de artefatos de projeto, com extração de texto, identificação de itens de gestão e geração de alertas por regras simples.

## Stack
- Backend: FastAPI + SQLAlchemy + SQLite
- Frontend: HTML/CSS/JS puro
- Execução local, sem IA e sem serviços externos pagos

## Instalação
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Execução
```bash
uvicorn backend.main:app --reload
```

Abra no navegador:
- http://127.0.0.1:8000/

## Fluxo de teste manual ponta a ponta

### 1) Criar arquivos de teste
Crie três arquivos locais com os conteúdos abaixo.

#### `meeting_notes.txt`
```text
Na reunião foi decidido que a retentativa automática deverá ser invisível ao cliente.
Ficou pendente definir o limite máximo de tentativas.
Existe risco de duplicação de reserva caso a locadora confirme mais de uma tentativa.
Próximo passo: validar com o time técnico se usaremos fila ou orquestrador.
Responsável: Rafael.
```

#### `risk_register.md`
```md
# Risk Register
## Risco: Duplicação de reserva
Impacto alto. Pode gerar cobrança indevida e problemas operacionais.
## Risco: Cancelamento por falha de pagamento
Se o fluxo demorar demais, a reserva pode ser cancelada por timeout.
```

#### `project_plan.md`
```md
# Plano do Projeto
A solução terá quatro tentativas automáticas.
O processo deve funcionar para PP, PD e híbrido.
Status atual: em análise técnica.
Ainda falta definir:
- limite de tempo total;
- comportamento perto da data de retirada;
- logs operacionais;
- dashboard de acompanhamento.
```

### 2) Executar fluxo
1. Abrir `http://127.0.0.1:8000/`.
2. Criar um projeto na seção **Projetos**.
3. Selecionar o projeto recém-criado.
4. Fazer upload dos 3 arquivos (`meeting_notes.txt`, `risk_register.md`, `project_plan.md`).
5. Clicar em **Processar projeto**.

### 3) Validar resultado esperado
- `documents` devem aparecer com status `processed` (exceto se algum arquivo estiver corrompido).
- `pm_items` deve conter itens dos tipos `risk`, `action`, `decision` e `open_question` para os textos de teste.
- alertas devem ser gerados (por exemplo, ações sem prazo/responsável e riscos sem mitigação explícita).
- dashboard deve mostrar contadores de documentos, itens e alertas.
- relatório executivo deve conter: nome do projeto, documentos analisados, riscos, ações, decisões e alertas.


## Regras de extração de itens PM (sem IA)
- Extração por palavras-chave para `action`, `risk`, `decision`, `dependency` e `open_question`.
- Linhas de contexto como `Responsável: ...`, `Owner: ...`, `Dono: ...`, `Com: ...` e `A cargo de ...` são associadas à **action imediatamente anterior** quando aplicável.
- Reconhecimento simples de prazo: `Prazo: dd/mm/aaaa`, `Data limite: dd/mm/aaaa`, `Até dd/mm/aaaa` e `Due date: aaaa-mm-dd`.
- Severidade textual: `high` (alto/alta/crítico/crítica/grave), `medium` (médio/média/moderado) e `low` (baixo/baixa).
- Há deduplicação básica para evitar itens consecutivos muito parecidos.

## Regras de alertas (sem IA)
- `action_missing_owner`: action sem owner.
- `action_missing_due_date`: action sem prazo.
- `risk_missing_owner`: risco sem owner.
- `risk_without_mitigation`: risco sem mitigação clara.
- `dependency_missing_owner`: dependência sem owner.
- `open_question_missing_owner`: pergunta em aberto sem owner.
- `decision_without_action`: decisão sem action relacionada por similaridade simples de termos.
- `document_processing_error`: documento com erro de processamento.
- `document_stale`: documento possivelmente desatualizado (>30 dias).

Observação: ao reprocessar o projeto, os alertas antigos do projeto são limpos e os alertas atuais são recriados para evitar duplicidade.

## Endpoints disponíveis
- `GET /health`
- `POST /projects`
- `GET /projects`
- `GET /projects/{project_id}`
- `POST /projects/{project_id}/upload`
- `POST /projects/{project_id}/process`
- `GET /projects/{project_id}/documents`
- `GET /projects/{project_id}/items`
- `GET /projects/{project_id}/alerts`
- `GET /projects/{project_id}/dashboard`
- `GET /projects/{project_id}/report`

## Estrutura
```text
backend/
frontend/
data/uploads/
data/pm_companion.db
```


## Fluxo de demo (3 minutos)
1. Suba a aplicação: `uvicorn backend.main:app --reload`.
2. Abra `http://127.0.0.1:8000/`.
3. Crie um projeto na seção **Projetos** e selecione-o.
4. Faça upload dos arquivos de teste na seção **Upload**.
5. Clique em **Processar projeto**.
6. Mostre o **Dashboard** (contadores), o **Radar de atenção** (alertas por severidade), os **Itens encontrados** (com filtro por tipo) e gere o **Relatório executivo**.
7. Use **Copiar relatório** para demonstrar compartilhamento rápido do output.

Sequência sugerida para apresentação: **criar projeto → subir documentos → processar → ver radar → gerar relatório**.
