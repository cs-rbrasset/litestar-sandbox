# backend/api

API do litestar-sandbox. Monólito modular flat: `core/` (config, banco, auth, utilitários
compartilhados) e `modules/` (um diretório por módulo de negócio — `ativos`, `boletas`,
`posicoes`, `notas`). Sem pacote wrapper: os imports internos são `from core.X import Y` /
`from modules.boletas.X import Y`, direto.

Ver `AGENTS.md` na raiz do repositório para comandos, arquitetura e convenções.
