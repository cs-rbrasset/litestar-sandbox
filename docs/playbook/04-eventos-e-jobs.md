# 4. Eventos e jobs assíncronos

## Por que eventos em vez de chamada direta

Se um controller do módulo A precisasse chamar um serviço do módulo B diretamente pra disparar um efeito colateral (gerar relatório, notificar, etc.), isso seria mais um acoplamento direto entre módulos — e ainda acoplaria o módulo A à tecnologia de execução (fila, orquestrador) escolhida pro trabalho pesado.

A solução: o controller publica um evento (`core/events.py: publish()`), e quem reage é um `listener.py` **dentro do próprio módulo dono do trabalho**. Só o listener conhece a tecnologia de execução por trás (no caso deste padrão, Prefect). O resto do sistema só conhece o nome do evento.

## Padrão de resposta síncrona a partir de um evento assíncrono

Quando o chamador precisa de algo de volta na hora (ex.: um ID de execução pra poder consultar status depois), o evento carrega um `asyncio.Future` embutido. O controller publica e espera nesse future; o listener resolve o future depois de disparar o trabalho de verdade (ex.: `.delay()` numa task do Prefect).

Isso evita um controller importar o client do orquestrador — a única coisa que sabe que existe um Prefect por trás é o listener.

## Consulta de status: não precisa de evento

Ler status de uma execução já disparada é leitura pura, sem efeito colateral — pode ir direto na API do orquestrador (ex.: `get_client().read_task_run()`), sem passar por evento. A regra de "publica evento" é especificamente pra **disparar** trabalho, não pra consultar o que já está rodando.

## Jobs longos (Prefect self-hosted)

Trabalho que não cabe no ciclo de vida de uma request HTTP (relatório em PDF sobre várias datas, qualquer processamento que passe de alguns segundos) vira uma *background task* via `.delay()`.

- Servidor: `prefect server start`.
- Worker: processo separado rodando `python -m <modulo>.tasks`, que sobe a task com `.serve()`.
- **Sem deployment, sem flow registrado, sem work pool** — só a task e o worker que a serve. É a configuração mínima do Prefect, não a arquitetura completa dele.
- `PREFECT_API_URL` no `.env`, default apontando pro server local.
- O Prefect guarda o estado da execução sozinho — **não existe tabela própria de "jobs" no banco da aplicação, nem dispatcher customizado**. Reinventar isso seria duplicar o que o orquestrador já faz.

### Isolamento de processo

A task roda em processo separado do processo web principal. Ela não herda a sessão de banco do request — abre a própria sessão com a config de banco (mesma forma que um listener abriria), porque não há request nenhuma por trás dela.

Se o repo usa `DB_ASSUME_IDENTITY` ou equivalente (ver capítulo 5), código fora de request **precisa declarar identidade explicitamente** antes de abrir transação — não existe usuário implícito vindo de header nenhum aqui.

### Onde o resultado do job pesado é guardado

Arquivo gerado (PDF, etc.) não fica no banco da aplicação nem no disco do worker — vai pra um object storage externo (ex.: Supabase Storage, ou equivalente do provedor escolhido) **[AJUSTAR]**, usando uma credencial de serviço separada da credencial de banco. O resultado que a task devolve é só o caminho/chave do objeto; quem pede o arquivo recebe uma signed URL de validade curta, não o arquivo em si nem uma URL pública permanente.

## Regra de ouro

Controller **nunca** importa a task nem o client do orquestrador diretamente. Se um agente de IA (ou um dev) sentir vontade de fazer `from modules.x.tasks import minha_task` dentro de um `controllers.py`, é sinal de que o padrão de evento → listener está sendo pulado.
