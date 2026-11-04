-- Identidade no banco: roles base e a função que a app chama no início de cada transação.
-- Desenho do handoff do banco (seções 2 e 3). Não é aplicado pela app: rode como admin,
-- uma vez, numa transação. Aplicado e verificado no Supabase de testes (Postgres 17.11,
-- usuário postgres com CREATEROLE, sem superuser). Desfazer: db/identity_rollback.sql.
--
-- Requer Postgres 16+ por causa do `grant ... with inherit false, set true`.

create schema if not exists app;

-- quem conecta: não pode nada sozinho, só virar as roles que recebeu com SET
-- (a senha fica fora deste arquivo: ALTER ROLE app_login PASSWORD ... pelo cofre)
create role app_login login noinherit;

-- privilégios base, herdados por pessoas e pela identidade de sistema
create role app_usuarios nologin;
grant usage on schema public to app_usuarios;
grant select, insert, update, delete on all tables in schema public to app_usuarios;
grant usage, select on all sequences in schema public to app_usuarios;
-- "on all tables" só cobre as tabelas de agora; as futuras precisam do default privilege,
-- vinculado à role que cria os objetos (troque por FOR ROLE <migrator> se for outra)
alter default privileges in schema public
    grant select, insert, update, delete on tables to app_usuarios;
alter default privileges in schema public
    grant usage, select on sequences to app_usuarios;

-- listeners e jobs: age como sistema, declarado no código com use_identity(SYSTEM)
create role app_sistema nologin;
grant app_usuarios to app_sistema;
grant app_sistema to app_login with inherit false, set true;

-- a função NÃO é SECURITY DEFINER, como o handoff sugeria: o Postgres recusa, com
-- 'cannot set parameter "role" within security-definer function' (verificado no 17.11).
-- Quem limita o que a conexão pode virar é o grant ... set true.
create or replace function app.assumir_identidade(papel text) returns void
language plpgsql
as $$
begin
    -- o mesmo formato que a app aceita (core/identity.py, DB_ROLE_PATTERN)
    if papel !~ '^(u_[0-9a-z-]{1,64}|app_[a-z_]{1,32})$' then
        raise exception 'role inválida: %', papel;
    end if;
    execute format('set local role %I', papel);
end;
$$;

grant usage on schema app to app_login;
grant execute on function app.assumir_identidade(text) to app_login;

-- TEMPORÁRIO, enquanto a app conecta como postgres (até as migrations com Alembic).
-- No PG 16+, quem tem CREATEROLE sem ser superuser recebe as roles que cria só com ADMIN,
-- sem SET: sem estes grants, o SET ROLE da própria conexão da app falharia. Contraria a
-- seção 3 do handoff (a conexão já lê tudo antes de assumir identidade): sai junto com a
-- troca da conexão para app_login.
grant app_sistema to postgres with inherit false, set true;

-- Pessoa de teste, para o token de dev (AUTH_DEV_TOKENS="tok-alice=u_alice:Alice").
-- Em produção o nome é u_<object id do Entra>, criado pelo job de espelhamento.
create role u_alice nologin;
grant app_usuarios to u_alice;
grant u_alice to app_login with inherit false, set true;
grant u_alice to postgres with inherit false, set true;  -- temporário, como acima

-- Uma pessoa (o job de espelhamento do Entra faz isto para cada usuário):
--   create role "u_<object id>" nologin;
--   grant app_usuarios to "u_<object id>";
--   grant "u_<object id>" to app_login with inherit false, set true;
--
-- Teste manual, conectado como app_login:
--   begin;
--   select app.assumir_identidade('app_sistema');
--   select current_user, session_user;   -- app_sistema | app_login
--   commit;
