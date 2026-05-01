# PM Companion MVP

Aplicação local para apoiar PMs/POs na análise de artefatos de projeto, com extração de texto, identificação de itens de gestão e geração de alertas por regras simples.

## Stack
- Backend: FastAPI + SQLAlchemy + SQLite
- Frontend: HTML/CSS/JS puro
- Execução local, sem IA e sem serviços externos pagos

## Como instalar
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Como rodar
```bash
uvicorn backend.main:app --reload
```

Abra no navegador:
- http://127.0.0.1:8000/

## Estrutura
```text
backend/
frontend/
data/uploads/
data/pm_companion.db
```

## Fluxo de teste rápido
1. Crie um projeto na seção "Projetos".
2. Faça upload de arquivos suportados: `.txt`, `.md`, `.csv`, `.xlsx`, `.docx`, `.pdf`.
3. Clique em **Processar projeto**.
4. Confira dashboard, alertas, itens e relatório executivo.

## Dados de teste sugeridos
Crie os arquivos abaixo e envie no upload.

### `meeting_notes.txt`
```text
Na reunião foi decidido que a retentativa automática deverá ser invisível ao cliente.
Ficou pendente definir o limite máximo de tentativas.
Existe risco de duplicação de reserva caso a locadora confirme mais de uma tentativa.
Próximo passo: validar com o time técnico se usaremos fila ou orquestrador.
Responsável: Rafael.
```

### `risk_register.md`
```md
# Risk Register
## Risco: Duplicação de reserva
Impacto alto. Pode gerar cobrança indevida e problemas operacionais.
## Risco: Cancelamento por falha de pagamento
Se o fluxo demorar demais, a reserva pode ser cancelada por timeout.
```

### `project_plan.md`
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

## Endpoints
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
