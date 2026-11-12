# 4. Eventos e jobs assíncronos

Duas coisas diferentes, que este capítulo separa de propósito:

| Preciso de… | Use |
|---|---|
| rodar trabalho fora do ciclo da request (importação, relatório, qualquer coisa que passe de alguns segundos) | **porta de jobs** — `core/jobs.py` |
| avisar outro módulo que algo aconteceu, dentro do app | **evento** — `core/events.py` |

Antes essas duas coisas eram a mesma: o controller publicava um evento só pra que um listener chamasse o orquestrador. Isso mudou — ver "O que mudou e por quê", no fim do capítulo.

## A porta de jobs (`core/jobs.py`)

`core/jobs.py` é **o único lugar do app que importa `prefect`**. Nenhum módulo conhece o orquestrador: o contrato `nenhum módulo importa prefect (só core.jobs)` no import-linter garante isso. (A ferramenta de publicação, `backend/api/implantar.py`, também importa — mas ela não é app: roda na máquina de quem publica.)

A porta expõe exatamente isto, e nada além:

| Nome | Para quê |
|---|---|
| `@job(nome, nome_execucao=None)` | declara uma função `async` como **job** — a unidade que se dispara e se consulta |
| `@etapa(tentativas=0, intervalo_s=0, nao_repetir=())` | declara um **passo** do job, com retry próprio |
| `await enfileirar(job, **params) -> str` | dispara o job e devolve o id da execução **na hora** |
| `await status(id) -> EstadoJob` | consulta (`estado`, `concluido`, `resultado`) |
| `async with sessao_de_job() as sessao` | sessão de banco dentro do job |
| `id_execucao_atual() -> str` | id da execução corrente, de dentro do job |
| `servir(pacote="modules")` | dev: o `worker.py` vive aqui |
| `descobrir()`, `nome_no_entrypoint()`, `NOME_DEPLOYMENT` | publicação: usados por `fluxos.py` e `implantar.py` |

Mais `EstadoJob`, `OrquestradorIndisponivelError` (e a filha `JobNaoPublicadoError`) e `ExecucaoNaoEncontradaError` — os módulos tratam esses, nunca `httpx.ConnectError` nem exceção do orquestrador.

## O fluxo HTTP

```
controller  →  service  →  core.jobs.enfileirar  →  deployment "<job>/padrao"  →  run
```

O controller devolve 202 com o id da execução; o trabalho acontece fora da API. **Não existe evento nesse caminho** e não existe `asyncio.Future` esperando nada.

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

`JobNaoPublicadoError` (o deployment não existe no servidor) herda de `OrquestradorIndisponivelError`: pra quem pede, dá no mesmo — 503.

Consultar status continua sendo leitura pura: vai direto em `core.jobs.status`, sem evento no meio.

## Job e etapa

O job (`@job`, um *flow* do Prefect) orquestra; as etapas (`@etapa`, *tasks*) fazem o trabalho com efeito colateral. **Quem repete é a etapa, nunca o job.**

```python
# modules/<modulo>/tasks.py
from core.jobs import etapa, job, sessao_de_job

@etapa(tentativas=3, intervalo_s=60, nao_repetir=ERROS_DE_DOMINIO)
async def baixar(gateway, documento, fundo_cnpj, data) -> list[ArquivoBruto]: ...

@etapa(tentativas=5, intervalo_s=5)
async def guardar(coleta, arquivos) -> str: ...

@etapa(tentativas=3, intervalo_s=10, nao_repetir=ERROS_DE_DOMINIO)
async def gravar_carteira(carteira, prefixo, coletado_em) -> None:
    async with sessao_de_job() as sessao:
        await registrar_carteira(sessao, carteira, prefixo, coletado_em)
        await sessao.commit()

@job("custodiante-importar-carteira")
async def importar_carteira(codigo: str, fundo_cnpj: str, data: datetime.date) -> str:
    arquivos = await baixar(...)
    prefixo = await guardar(...)
    await gravar_carteira(parse(arquivos), prefixo, coletado_em)   # parse: função pura
    return prefixo
```

Por que a divisão: se o job inteiro repetisse, uma falha em `guardar` (storage piscou) ou em `gravar_carteira` (banco caiu) **refaria a coleta** — outra chamada ao custodiante, outro scraping, outro bruto no storage. Com retry por etapa, repete-se só o passo que falhou, com o que os anteriores produziram ainda em memória. Os testes `test_falha_ao_guardar_o_bruto_nao_baixa_de_novo` e `test_falha_ao_gravar_nao_baixa_nem_guarda_de_novo` travam isso.

Regras:

- **Uma etapa por efeito colateral** (rede, storage, banco). Função pura (parse) não é etapa: não tem o que repetir.
- **`nao_repetir` recebe tipos de exceção**, não uma classe-base do `core`. O domínio não herda nada da infraestrutura: ele só aponta as próprias exceções. Retry é pra falha transitória; erro de domínio não melhora repetindo.
- **Intervalo conforme o que falha**: portal fora do ar volta em minutos; storage e banco, em segundos.
- **Etapa repetida tem que ser idempotente** — gravação é upsert por chave de negócio (capítulo 11).
- **Parâmetros do job são tipos simples e serializáveis**: viajam pelo orquestrador e são validados num processo à parte. Parâmetros de etapa podem ser objetos: ficam em memória, dentro da mesma execução, e **não são persistidos** (o bruto já mora onde deve).
- **A sessão vem de `sessao_de_job()`**, nunca de um config aberto à mão.
- **O retorno do job é persistido**: quem lê é a API (`status`), não o processo que o produziu.

Limite assumido: se o processo do job morrer no meio (container derrubado), os arquivos em memória se perdem e a próxima execução coleta de novo. Persistir o resultado de `baixar` evitaria isso ao custo de duplicar o bruto no storage do orquestrador — não compensa.

## Onde o job roda

Todo job é publicado como um **deployment** chamado `<nome do job>/padrao`, e é por esse nome que `enfileirar` o dispara — em dev e em produção, sem saber em qual está.

### Dev: `backend/api/worker.py`

```
uv run --env-file ../../.env python worker.py
```

`core.jobs.servir()` descobre os jobs em `modules/*/tasks.py`, registra os deployments no server local (`prefect server start`) e executa os runs no próprio processo. Job novo não exige tocar no worker. **O worker precisa subir pelo menos uma vez** antes de a API disparar um job novo — senão o deployment não existe (`JobNaoPublicadoError`).

`--env-file` é obrigatório: ao contrário de `litestar run`, um `python` solto não carrega o `.env` sozinho.

### Produção: servidor Prefect da RBR, via `rbr-prefect`

Cada run sobe num **container** do work pool `default`, que **clona o repositório** no commit publicado e carrega o job. Três peças:

| Peça | Papel |
|---|---|
| `Dockerfile.jobs` (raiz) | imagem com Python 3.14 + dependências de terceiros, **sem código nosso** (as imagens padrão do `rbr-prefect` são 3.12). Refazer só quando o `uv.lock` muda |
| `backend/api/fluxos.py` | o entrypoint. O clone é carregado da raiz do repositório, e o Prefect só põe no `sys.path` a pasta do entrypoint — por isso ele mora em `backend/api/` (e acrescenta `database/src`). Expõe cada job descoberto como atributo |
| `backend/api/implantar.py` | publica um deployment por job com `rbr_prefect.DefaultDeploy`: imagem nossa, entrypoint `backend/api/fluxos.py:<job>`, clone **fixado no commit**, ambiente só com referências |

Ordem de uma publicação — **a ordem importa**:

1. Commit no `main`, com push (o `rbr-prefect` recusa `main` sujo ou sem push).
2. Se o `uv.lock` mudou: `docker build -f Dockerfile.jobs -t 10.214.20.79:5000/litestar-sandbox-jobs:<tag> .` e push.
3. `cd backend/api && JOBS_IMAGEM=<imagem> uv run python implantar.py` (sem terminal: `--rbr-non-interactive`).
4. Deploy da API — por último, porque ela só sabe chamar deployments que já existem com os parâmetros que ela manda.

Por que fixar o commit: sozinho, o `rbr-prefect` clona o HEAD do branch **na hora de cada run**. Sem fixar, um push mudaria o que roda em produção sem publicar nada, e a API ficaria fora de sincronia com os jobs. Mudar a assinatura de um job segue a regra de contrato público: acrescentar parâmetro com default é compatível; remover ou renomear exige publicar os jobs **antes** da API.

O ambiente do container **não leva valor nenhum**: credencial vira bloco `Secret` e configuração vira variável do Prefect (`implantar.SEGREDOS` / `implantar.VARIAVEIS`), resolvidos pelo worker na hora do run. Valor literal ficaria gravado no deployment e visível na UI. Custodiante novo = acrescentar o par `CUSTODIANTE_<CODIGO>_URL`/`_TOKEN` lá e criar o bloco e a variável no servidor.

O retorno do job vai pro **result storage remoto** (variável `litestar_sandbox_bloco_de_resultados` → `PREFECT_RESULTS_DEFAULT_STORAGE_BLOCK`): o container morre no fim do run, e a API precisa ler o resultado depois. A API também precisa de `PREFECT_RESULTS_DEFAULT_STORAGE_BLOCK` e de alcançar `prefect-eve.rbr.local` (`PREFECT_API_URL`, auth e a CA da RBR).

> **O job não tem app Litestar.** Logo, **job não publica evento** — `publish()` precisa do app. Se um job precisa de outro módulo, chama o `public.py` dele direto.

### Sessão e engine no job

`sessao_de_job()` resolve, dentro da porta, a lacuna que a documentação do orquestrador não cobre: não existe hook de startup/shutdown pro processo que executa o job, então o ciclo de vida da engine precisa morar em algum lugar explícito.

A regra implementada é **uma engine por execução do job** (não por etapa nem por item processado), com `dispose()` garantido no fim — as etapas rodam no contexto do job, e chamar `sessao_de_job()` várias vezes na mesma execução reusa a mesma engine. Isso mata, por construção, o vazamento clássico de abrir engine dentro de um laço.

Com um container por run, cada execução abre as próprias conexões: em pico de importação, o total é runs × `pool_size`. Antes de aumentar a concorrência, ponha o pooler do Supabase (modo transaction) na `DATABASE_URL` dos jobs.

Código fora de request não tem identidade implícita: `sessao_de_job()` já age como identidade de sistema, de propósito (ver capítulo 5).

### Onde o resultado pesado é guardado

Arquivo gerado (PDF, etc.) não fica no banco nem no disco do container — vai pro object storage (`core/storage.py`, ver capítulo 14), com credencial de serviço separada da de banco. O job devolve só o caminho do objeto; quem pede o arquivo recebe uma signed URL curta, nunca uma URL pública permanente.

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

- **Convenções num lugar só.** Retry, nome da execução, sessão de banco e ciclo de vida da engine eram repetidos em cada `tasks.py`; agora são argumentos de `@job`/`@etapa` e o comportamento de `sessao_de_job()`.
- **Módulo sem dependência do orquestrador.** Antes o listener importava `prefect`; hoje nenhum módulo importa, e isso é verificável (contrato do import-linter), não combinado.
- **Menos peça por caminho.** O evento + future existia só pra esconder o orquestrador do controller. A porta faz isso com uma chamada, e some um `asyncio.Future` que precisava ser resolvido **e** rejeitado à mão — se o listener não resolvesse o future, quem publicou ficava esperando até o timeout.
- **Troca de orquestrador vira reescrita de um arquivo**, não varredura nos módulos.

**Depois, de job único pra job + etapas.** O primeiro desenho da porta tinha o job como uma *task* avulsa (`.delay()` + task worker), com retry no job inteiro: uma falha ao gravar o bruto ou o banco refazia a coleta no custodiante. Agora o job é um *flow* publicado como deployment, e o retry é por etapa. O mesmo deployment serve o dev (`worker.py`) e a produção (servidor da RBR, via `rbr-prefect`).

**O custo, declarado**: a porta vaza o vocabulário de orquestração (fila, execução, retry). Isso é inevitável — e a mitigação é expor **só o que é usado**. Método novo em `core/jobs.py` entra quando um módulo precisar dele, nunca "porque o orquestrador tem".

## Regra de ouro

Nenhum arquivo de `modules/` importa `prefect`. Se a vontade bater, a peça que falta é um nome novo em `core/jobs.py` — e ele entra lá, não no módulo.
