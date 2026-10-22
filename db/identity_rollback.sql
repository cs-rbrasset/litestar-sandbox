-- Desfaz o db/identity.sql. Só para bancos de teste: em produção, desprovisionar é REVOKE,
-- nunca DROP ROLE (handoff, seção 3): o drop perde a capacidade de resolver valores
-- históricos de current_user na trilha de auditoria.

drop function if exists app.assumir_identidade(text);
drop schema if exists app;

alter default privileges in schema public
    revoke select, insert, update, delete on tables from app_usuarios;
alter default privileges in schema public
    revoke usage, select on sequences from app_usuarios;

-- remove os grants que as roles receberam, para o DROP ROLE ser aceito
drop owned by u_alice, app_sistema, app_usuarios, app_login;

drop role if exists u_alice;
drop role if exists app_sistema;
drop role if exists app_usuarios;
drop role if exists app_login;
