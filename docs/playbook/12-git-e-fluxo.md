# 12. Git e fluxo de trabalho

## Commits

- **Conventional Commits em português**, corpo em tópicos explicando o **porquê**, não o quê (o diff já mostra o quê).
- Um assunto por commit — não misture refactor com feature nova no mesmo commit.
- Nunca commitar `.env` nem qualquer credencial.

## Working tree com mudança alheia

Se a working tree tem mudanças de uma tarefa que não foi discutida na sessão atual (código de outro agente, outra sessão, um WIP alheio):

- **Não commite** — nem pra "limpar", nem pra "aproveitar que já está ali".
- Sinalize o que achou, separado do que é seu.
- Se precisar mexer no mesmo arquivo que essa mudança alheia, **reconstrua a versão intermediária**: stage só a sua parte, commit, restaura o resto em seguida — em vez de misturar os dois num commit só.

## Branches e modo de trabalho do agente de IA

Regras de até onde um agente de IA pode ir sozinho variam por branch — ver capítulo 13 pros detalhes. Isso é uma política do repo (vive no `AGENTS.md`), não uma regra de Git em si, mas o fluxo de branch deveria refletir essa política: branch "modo tutor" não deveria receber commit de implementação feito por agente sem revisão humana explícita.
