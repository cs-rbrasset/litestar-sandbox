# 5. Autenticação e identidade

Este capítulo descreve o padrão usado com **Entra ID (Azure AD)** como IdP. Se outro repo usar outro provedor, a estrutura (front fala direto com o IdP, backend é resource-server puro) se mantém — só troca o provedor. **[AJUSTAR]**

## Front é cliente público, backend nunca participa do login

O front-end é um SPA registrado como **cliente público** no IdP (MSAL.js, fluxo PKCE, sem client secret, sem estado de sessão guardado no servidor). Ele fala direto com o Entra pra obter o token — o backend nunca vê usuário/senha, nunca participa do fluxo OAuth em si.

O backend é **só resource server**: recebe `Authorization: Bearer <token>`, valida contra o JWKS do tenant. Não emite token, não tem endpoint de login.

## Qual token e qual escopo

A credencial enviada ao backend é um **access_token** com escopo próprio da aplicação, não o token genérico do Microsoft Graph. Isso exige, no App Registration do Entra:

1. Uma entrada "Expose an API" com um scope próprio (ex.: `access_as_user`) — exige admin consent.
2. O front pede esse scope especificamente (`LOGIN_SCOPES = ["api://<client_id>/access_as_user"]`).
3. Mesmo pedindo um escopo com prefixo `api://`, o `aud` (audience) dentro do token continua sendo o **client_id puro**, sem o prefixo — é esse valor que o backend espera bater.

## Setup no Entra (resumo operacional)

- App registration tipo **SPA**: pode reaproveitar um App registration já existente de outro propósito, mas adicionando uma plataforma **"Single-page application"** separada — não editar uma plataforma "Web" já existente pra virar SPA.
- Redirect URI apontando pra origem do front (ex. `http://localhost:5173` em dev).
- "Expose an API" com o scope da aplicação, com admin consent concedido.

## Variáveis de ambiente

- Backend: `ENTRA_TENANT_ID`, `ENTRA_API_AUDIENCE` (= client_id, sem o prefixo `api://`).
- Front: `ENTRA_CLIENT_ID`, `ENTRA_TENANT_ID` (em `.env.local`, nunca commitado).

## Verificador composto

Sem `ENTRA_TENANT_ID` setado no backend, o verificador só aceita tokens fixos de desenvolvimento (uma lista de tokens de teste, tipicamente via env var). Com `ENTRA_TENANT_ID` setado, os dois convivem — um verificador composto tenta validação Entra e cai pra tokens de dev se aplicável. Isso permite dev local sem depender do Entra, e testes automatizados que não precisam de rede nenhuma.

## Espelhamento de identidade no banco (role por pessoa)

Autorização no nível de linha é feita com **role de banco por pessoa**, não com uma tabela de permissões própria. No primeiro login de cada pessoa, o verificador do Entra:

1. Deriva um identificador estável a partir do `oid` do token (ex.: `u_<oid em minúsculas>` — um padrão fixo e validável, nunca montado livremente a partir de outro campo do token).
2. Garante (idempotente) que existe uma role de banco com esse nome, via uma function/procedure no banco (ex. `app.garantir_pessoa`) chamada a partir do código que valida o token.

Esse padrão de identificador (`DB_ROLE_PATTERN` ou equivalente) é a única forma aceita de nomear uma role — nunca construído livremente a partir de texto vindo do usuário, em nenhum lugar do código.

## Identidade em código fora de request

Qualquer código que abre uma sessão de banco fora do ciclo de uma request HTTP (listener de evento, worker de job assíncrono) **precisa assumir identidade explicitamente** antes de abrir transação, se o banco usa um mecanismo de "assumir identidade" obrigatório (ex. uma flag tipo `DB_ASSUME_IDENTITY=true` que faz uma transação sem identidade falhar no Postgres). Sem isso declarado, ambientes de teste com SQLite simplesmente desligam esse mecanismo (não há equivalente de role por conexão lá).

## No nível de teste

Testes de API usam uma fixture de cliente que já manda o token de teste automaticamente. Pra testar especificamente o caso de "sem token" ou "token inválido", o teste precisa criar um client separado, sem esse header — não reusar a fixture padrão achando que "basta não passar token", porque a fixture já injeta um.
