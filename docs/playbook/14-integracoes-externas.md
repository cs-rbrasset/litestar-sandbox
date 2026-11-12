# 14. Integrações externas

Como entra, neste padrão, dado que vem de fora: de um custodiante, de um portal, de um parceiro. O exemplo de referência é o módulo `custodiante`, mas a forma vale pra qualquer fonte externa.

## As três fronteiras

| Módulo | Dono de quê |
|---|---|
| `custodiante` | a integração com cada custodiante: buscar os arquivos, guardar o bruto, traduzir para o canônico e entregar. Contém gateways, parsers, registro, brutos e os jobs de importação. |
| `carteira` | o conceito carteira: modelo canônico, validação, persistência, consulta e processamentos posteriores. |
| `extrato` | o mesmo papel, para extrato. |

**Direção, sem exceção**: `custodiante` → `carteira.public` e `extrato.public`. Nunca o inverso. `carteira` e `extrato` **não sabem que custodiantes existem** — o que elas guardam da origem é uma referência opaca.

Outra fonte de carteira que aparecer depois (upload manual, parceiro novo) entrega o **mesmo canônico** para `carteira.public` e guarda o **próprio bruto**. Nenhuma linha de `carteira` muda por causa disso.

## Gateway e parser: a separação que paga a conta

```
modules/custodiante/
├── enums.py           # CodigoCustodiante, TipoDocumento
├── protocols.py       # ArquivoBruto, GatewayCustodiante, ParseCarteira/ParseExtrato, Adaptador
├── registro.py        # CodigoCustodiante → Adaptador
├── brutos.py          # Coleta, guardar_brutos, ler_brutos (usa core.storage)
├── tasks.py           # jobs: importar_*, reprocessar_*
├── services.py        # solicitar_importacao → core.jobs.enfileirar
├── controllers.py     # POST /custodiantes/importacoes, GET status
├── gateways/          # I/O; um por custodiante
│   ├── _navegador.py  # sessão de navegador compartilhada (scraping)
│   └── <custodiante>.py
└── parsers/           # puros; um por custodiante
    ├── erros.py       # LayoutNaoReconhecidoError
    ├── anbima_xml.py  # base comum do XML ANBIMA
    └── <custodiante>.py
```

**Gateway** é só I/O. Implementa o `Protocol` `GatewayCustodiante`:

```python
async def baixar_carteira(self, fundo_cnpj: str, data: datetime.date) -> list[ArquivoBruto]
async def baixar_extrato(self, fundo_cnpj: str, data: datetime.date) -> list[ArquivoBruto]
```

`ArquivoBruto` é `(nome, conteudo: bytes, formato)`. O gateway **nunca interpreta o conteúdo** — não abre o XML, não valida campo, não sabe o que é uma posição.

O nome é "gateway", e não "repository", de propósito: repository devolve objeto de domínio; isto devolve bytes.

**Parser** é função pura, `Sequence[ArquivoBruto] → canônico`. Sem classe e sem `Protocol` próprio (não tem estado nem comportamento a injetar), só aliases de tipo: `ParseCarteira`, `ParseExtrato`.

**`Adaptador(gateway, parse_carteira | None, parse_extrato | None)`** junta os dois. `None` significa que aquele custodiante **não fornece** aquele documento — e isso é um erro de domínio, não uma falha a repetir.

**O parser é determinístico.** Nada de `now()` lá dentro: a hora da coleta é metadado da coleta, não do documento, e viaja em separado até a gravação. É o que faz reprocessar um bruto antigo preservar a precedência original em vez de parecer uma coleta nova.

Scraping é só mais um gateway: mesma interface, mesma regra. Entrega HTML em vez de XML, e a sessão de navegador fica em `gateways/_navegador.py` porque subir navegador é caro demais pra cada gateway abrir o seu.

## Os dois fluxos — e as etapas que nunca se fundem

**Importação:**

```
baixar (gateway) → guardar bruto → parsear → registrar (carteira.public / extrato.public)
```

**Reprocessamento:**

```
ler bruto do storage → parsear → registrar
```

Reprocessar serve pra corrigir bug de parser ou extrair campo novo do histórico **sem chamar o custodiante de novo**.

Regras, as três:

1. **Baixar e parsear são sempre duas chamadas separadas**, orquestradas pelo job. Um gateway que "já devolve a carteira pronta" mata o reprocessamento.
2. **O bruto é salvo antes do parse.** Se o parse quebrar, o arquivo que quebrou está guardado — é exatamente ele que se reprocessa depois.
3. **Retry só para falha de coleta.** Erro de domínio (layout não reconhecido, validação, documento indisponível) entra em `nao_repetir`: o arquivo é o mesmo, repetir não muda nada.

## O arquivo bruto

O bruto **pertence ao `custodiante`**: é o registro do que o custodiante mandou, não uma carteira.

Layout no object storage:

```
custodiante/{codigo}/{documento}/{cnpj}/{data}/{coletado_em}_{hash}/
    manifesto.json          # arquivos, sha256, coletado_em
    <arquivos como vieram>
    falhas/                 # HTML e screenshot quando a coleta quebra (scraping)
```

- **Nunca sobrescrever.** Cada coleta tem prefixo próprio (hora + hash do conteúdo): duas coletas do mesmo dia coexistem; uma coleta repetida com conteúdo idêntico cai no mesmo prefixo.
- O código do custodiante vem cedo no caminho de propósito: reprocessar recebe só o prefixo e lê de lá qual parser usar.
- O `manifesto.json` carrega o `coletado_em` original — é o que o reprocessamento usa pra gravar com a precedência certa.
- **`carteira`/`extrato` guardam só `referencia_origem`** (esse prefixo), como string opaca. Não leem o bruto e não têm FK.
- Falha de scraping grava HTML e screenshot em `{prefixo}/falhas/` — sem isso não há como saber depois o que o portal mostrou.

## A porta de storage (`core/storage.py`)

Quatro operações, e nada mais: `put`, `get`, `list`, `url_assinada`. A porta vaza o vocabulário de object storage de propósito, mas só o que é usado.

- Credencial de serviço própria, **separada da do banco**, e que nunca chega ao front.
- **Bucket privado**; acesso a objeto só por URL assinada de validade curta.
- Adaptadores: o provedor em uso, um em memória (testes) e **[AJUSTAR: qual object storage]** com implementação compatível com S3 (dev local com MinIO).
- **[AJUSTAR: prazo de retenção com compliance]** — e aplicar como regra de ciclo de vida do bucket, não como rotina de limpeza no código.

## Persistência e idempotência

- **Upsert por chave de negócio** com `INSERT ... ON CONFLICT`. Nunca "busca e depois insere": o job pode rodar duas vezes (retry, reprocessamento) e o resultado tem que ser o mesmo.
- **Precedência**: só sobrescreve quando a coleta nova é mais recente que a gravada (`coletado_em`). A exceção é o reprocessamento **forçado explicitamente** — o único jeito de uma releitura antiga vencer uma gravação mais nova.
- Posições e lançamentos são tabelas (`PosicaoCarteira`, `LancamentoExtrato`), com FK permitida **só dentro da mesma área**. **[AJUSTAR: confirmar tabelas × JSONB]** conforme o canônico ficar mais rico por classe de ativo.

## Custodiante novo: o que exatamente se cria

1. Um valor em `CodigoCustodiante`.
2. Um gateway em `gateways/<codigo>.py`.
3. Um parser em `parsers/<codigo>.py` (reaproveitando a base, quando houver — `anbima_xml.py`).
4. Uma **fixture de arquivo real** no teste do parser, e o teste.
5. **Uma linha no `registro.py`**.
6. As credenciais no `.env`, uma entrada por custodiante — nunca uma credencial compartilhada.

Nada mais no sistema precisa saber que ele existe.
