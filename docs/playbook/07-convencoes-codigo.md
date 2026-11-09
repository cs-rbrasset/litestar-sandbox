# 7. Convenções de código (backend)

## Schemas e validação

- Schemas de request/response usam `msgspec.Struct`, não Pydantic nem dataclass puro.
- A validação de **formato** (regex, tamanho, tipo) fica na borda HTTP, no schema.
- Em **query e path params**, restrição vai em `Parameter(...)` do Litestar — `msgspec.Meta` é **ignorado fora do body**. Colocar `Meta` num query param não dá erro, só não faz nada; é um erro silencioso fácil de escrever sem perceber.

## Dependency injection

Aliases de DI seguem o padrão:

```python
MeuServico: TypeAlias = NamedDependency[SkipValidation[ServicoReal]]
```

**Nunca** use a sintaxe nova de alias do Python (`type X = ...`, PEP 695) aqui — ela quebra `SkipValidation` dentro do DI do Litestar. O lint que reclamaria disso (`UP040`, de ruff) fica deliberadamente ignorado nesses casos — não "corrigir" removendo o `# noqa: UP040`.

## Services e repositories

- Services herdam de `SQLAlchemyAsyncRepositoryService`.
- Pra usar `with_for_update` (lock de linha), use `self.repository.get(...)` diretamente — o `get` exposto pelo service **não aceita** esse parâmetro. Tentar passar `with_for_update` pro `.get()` do service falha ou é ignorado; o caminho certo é descer um nível pro repository.

## Código fora do ciclo de request

Listener de evento e worker de job assíncrono (ver capítulo 4) **abrem a própria sessão** com a mesma config usada pelo plugin de banco da API, fazem commit manualmente, e são **idempotentes** — rodar duas vezes com o mesmo input não deve duplicar efeito. Isso importa especialmente pra listener de evento, que pode ser re-entregue em cenário de falha/retry dependendo de como o barramento de evento é implementado.

## Datas

Datas de negócio (data de uma operação, data de referência de um relatório) são `datetime.date`, nunca `datetime.datetime`. Misturar os dois tipos no mesmo campo/coluna é fonte de bug sutil de fuso horário e comparação.

## Regra geral de estilo

Sem comentário explicando o quê o código faz (nome bem escolhido já faz isso). Comentário só quando a razão (o "porquê") não é óbvia pela leitura — uma invariante escondida, um workaround de bug específico, algo que surpreenderia quem lê depois.
