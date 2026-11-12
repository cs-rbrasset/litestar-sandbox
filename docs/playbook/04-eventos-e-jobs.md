# 4. Eventos e jobs assíncronos

Duas coisas diferentes, que este capítulo separa de propósito:

| Preciso de… | Use |
|---|---|
| rodar trabalho fora do ciclo da request (importação, relatório, qualquer coisa que passe de alguns segundos) | **porta de jobs** — `core/jobs.py` |
| avisar outro módulo que algo aconteceu, dentro do app | **evento** — `core/events.py` |

Antes essas duas coisas eram a mesma: o controller publicava um evento só pra que um listener chamasse o orquestrador. Isso mudou — ver "O que mudou e por quê", no fim do capítulo.

## A porta de jobs (`core/jobs.py`)

`core/jobs.py` é **o único lugar do backend que importa `prefect`**. Nenhum módulo conhece o orquestrador: o contrato `nenhum módulo importa prefect (só core.jobs)` no import-linter garante isso.

A porta expõe exatamente isto, e nada além:

| Nome | Para quê |
|---|---|
| `@job(nome, nome_execucao=None, tentativas=0, intervalo_s=0, nao_repetir=())` | declara uma função `async` como job |
| `await enfileirar(job, **params) -> str` | põe na fila e devolve o id da execução **na hora** |
| `await status(id) -> EstadoJob` | consulta (`estado`, `concluido`, `resultado`) |
| `async with sessao_de_job() as sessao` | sessão de banco dentro do worker |
| `id_execucao_atual() -> str` | id da execução corrente, de dentro do job |
| `servir(pacote="modules")` | o worker vive aqui |

Mais `EstadoJob`, `OrquestradorIndisponivelError` e `ExecucaoNaoEncontradaError` — os módulos tratam esses, nunca `httpx.ConnectError` nem exceção do orquestrador.

## O fluxo HTTP

```
controller  →  service  →  core.jobs.enfileirar  →  (fila)  →  worker
```

O controller devolve 202 com o id da execução; o trabalho acontece no worker. **Não existe evento nesse caminho** e não existe `asyncio.Future` esperando nada.

```python
# controllers.py
@post("/importacoes", status_code=202)
async def solicitar(self, data: ImportacaoRequest, servico: ImportacaoServiceDep) -> ExecucaoHandle:
    try:
        id_execucao = await servico.solicitar_importacao(...)
    except OrquestradorIndisponivelError as erro:
        raise ServiceUnavailableException(detail="orquestrador de jobs indisponível") from erro
    return ExecucaoHandle(id_execucao=id_execucao)
```

Consultar status continua sendo leitura pura: vai direto em `core.jobs.status`, sem evento no meio.

## Declarando um job

```python
# modules/<modulo>/tasks.py
from core.jobs import job, sessao_de_job

@job(
    "custodiante-importar-carteira",
    tentativas=3,
    intervalo_s=60,
    nao_repetir=(LayoutNaoReconhecidoError, CarteiraInvalidaError),
)
async def importar_carteira(codigo: str, fundo_cnpj: str, data: datetime.date) -> str:
    ...
    async with sessao_de_job() as sessao:
        await registrar_carteira(sessao, canonica, prefixo, coletado_em)
        await sessao.commit()
    return prefixo
```

Três regras, todas visíveis nesse trecho:

- **`nao_repetir` recebe tipos de exceção**, não uma classe-base do `core`. O domínio não herda nada da infraestrutura: ele só aponta as próprias exceções. Retry serve pra falha de coleta (rede, serviço fora do ar); erro de domínio não melhora repetindo.
- **Parâmetros são tipos simples e serializáveis.** O orquestrador resolve as anotações num processo à parte, onde os tipos do módulo de origem podem não existir.
- **A sessão vem de `sessao_de_job()`**, nunca de um config aberto à mão.

## O worker (`backend/api/worker.py`)

```
uv run --env-file ../../.env python worker.py
```

O `worker.py` fica **ao lado do `app.py`** e é a outra metade do backend. Ele não cita módulo nenhum: `core.jobs.servir()` descobre os jobs em `modules/*/tasks.py`, do mesmo jeito que o autowire descobre os controllers. Job novo não exige tocar no worker.

`--env-file` é obrigatório: ao contrário de `litestar run`, um `python` solto não carrega o `.env` sozinho.

> **O worker não tem app Litestar.** Logo, **job não publica evento** — `publish()` precisa do app. Se um job precisa de outro módulo, chama o `public.py` dele direto.

### Sessão e engine no worker

`sessao_de_job()` resolve, dentro da porta, a lacuna que a documentação do orquestrador não cobre: não existe hook de startup/shutdown pro task worker, então o ciclo de vida da engine precisa morar em algum lugar explícito.

A regra implementada é **uma engine por execução do job** (não por item processado), com `dispose()` garantido no fim — chamar `sessao_de_job()` várias vezes na mesma execução reusa a mesma engine. Isso mata, por construção, o vazamento clássico de abrir engine dentro de um laço.

Quando o volume crescer, a mudança é trocar isso por um lifespan no worker (`asyncio.run(main())` abrindo a engine antes de `await aserve(...)`, uma engine por processo) — **dentro de `core/jobs.py`**, sem tocar em módulo nenhum. É o ganho de ter a porta.

Código fora de request não tem identidade implícita: `sessao_de_job()` já age como identidade de sistema, de propósito (ver capítulo 5).

### Onde o resultado pesado é guardado

Arquivo gerado (PDF, etc.) não fica no banco nem no disco do worker — vai pro object storage (`core/storage.py`, ver capítulo 14), com credencial de serviço separada da de banco. O job devolve só o caminho do objeto; quem pede o arquivo recebe uma signed URL curta, nunca uma URL pública permanente.

O orquestrador guarda o estado da execução sozinho: **não existe tabela de "jobs" na aplicação, nem dispatcher próprio**. Reinventar isso seria duplicar o que ele já faz.

## Eventos: comunicação entre módulos

Evento é para **um módulo avisar outro, dentro do app**, sem que um importe o outro:

- O mecanismo fica no `core` (`core/events.py: publish()`).
- A **definição tipada do evento e o listener ficam no módulo dono** — quem publica só conhece o nome e o payload.
- Listener roda fora do request: abre a própria sessão, declara identidade, faz commit à mão e é idempotente.

Exemplo em uso: `boletas` publica `TRADE_SETTLED` (definido em `boletas/public.py`) e `posicoes/listeners.py` reage.

Evento **não** é mecanismo de disparo de job. Se a vontade é "publicar um evento pra alguém chamar o orquestrador", o caminho certo é `core.jobs.enfileirar`.

## O que mudou e por quê

**Antes**: o controller publicava um evento com um `asyncio.Future` embutido e esperava nele; o listener do módulo chamava `.delay()` e resolvia o future com o id da execução.

**Agora**: o controller chama o service, que chama `core.jobs.enfileirar`.

Por quê:

- **Convenções num lugar só.** Retry, nome da execução, sessão de banco e ciclo de vida da engine eram repetidos em cada `tasks.py`; agora são argumentos de `@job` e o comportamento de `sessao_de_job()`.
- **Módulo sem dependência do orquestrador.** Antes o listener importava `prefect`; hoje nenhum módulo importa, e isso é verificável (contrato do import-linter), não combinado.
- **Menos peça por caminho.** O evento + future existia só pra esconder o orquestrador do controller. A porta faz isso com uma chamada, e some um `asyncio.Future` que precisava ser resolvido **e** rejeitado à mão — se o listener não resolvesse o future, quem publicou ficava esperando até o timeout.
- **Troca de orquestrador vira reescrita de um arquivo**, não varredura nos módulos.

**O custo, declarado**: a porta vaza o vocabulário de orquestração (fila, execução, retry). Isso é inevitável — e a mitigação é expor **só o que é usado**. Método novo em `core/jobs.py` entra quando um módulo precisar dele, nunca "porque o orquestrador tem".

## Regra de ouro

Nenhum arquivo de `modules/` importa `prefect`. Se a vontade bater, a peça que falta é um nome novo em `core/jobs.py` — e ele entra lá, não no módulo.
