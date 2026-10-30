-- Job de espelhamento do Entra: cria a role u_<object id> no primeiro login de cada
-- pessoa. Sem isso, app.assumir_identidade(role) falha com "role ... does not exist" —
-- um erro que o advanced-alchemy (wrap_sqlalchemy_exception, StatementError) converte em
-- IntegrityError e a API devolve como 409, sem nenhuma relação com conflito de dado real.
--
-- Chamado pelo backend (core/entra.py, EntraTokenVerifier) logo depois de validar o
-- id_token, antes de qualquer transação de negócio. Idempotente: não faz nada se a role
-- já existe. Requer os mesmos privilégios de db/identity.sql (rode como o mesmo usuário).

create or replace function app.garantir_pessoa(papel text) returns void
language plpgsql
as $$
begin
    if papel !~ '^u_[0-9a-z-]{1,64}$' then
        raise exception 'role inválida: %', papel;
    end if;
    if not exists (select 1 from pg_roles where rolname = papel) then
        execute format('create role %I nologin', papel);
        execute format('grant app_usuarios to %I', papel);
        execute format('grant %I to app_login with inherit false, set true', papel);
        -- TEMPORÁRIO, enquanto a app conecta como postgres (mesma ressalva de identity.sql)
        execute format('grant %I to postgres with inherit false, set true', papel);
    end if;
end;
$$;

grant execute on function app.garantir_pessoa(text) to app_login;
