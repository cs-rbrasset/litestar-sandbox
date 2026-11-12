# 15. Decisões em aberto

O que ainda **não** está decidido. Nada aqui é "o agente resolve": são decisões de produto, de negócio ou jurídicas, e um palpite plausível escrito em código vira regra sem dono.

Enquanto um item estiver aqui, o código correspondente carrega um `[AJUSTAR]` apontando pra cá.

| # | Em aberto | Por que não dá pra decidir sozinho | Quem decide |
|---|---|---|---|
| 1 | **Regras de validação da carteira** | A regra intuitiva "soma das posições = PL" **está errada**: o PL inclui caixa, provisões, valores a pagar e a receber. Hoje a validação é só estrutural (CNPJ, posição repetida, carteira vazia). | quem entende de carteira de fundos |
| 2 | **Riqueza do modelo canônico por classe de ativo** | O XML ANBIMA separa títulos públicos, privados, compromissadas, cotas, derivativos e provisões, cada um com campos próprios (indexador, taxa, vencimento, contraparte). O canônico atual tem o mínimo comum. | produto + quem consome a carteira |
| 3 | **Identificação de ativos e de-para por custodiante** | Hoje mora no cadastro de ativos do crédito. Provavelmente vira um módulo `ativos`, mas isso muda quem é dono do de-para. | produto |
| 4 | **Consultas que atravessam as futuras fronteiras** | Ex.: saldo devedor juntando carteira, ativos e PU. Ou passa por `public.py`, ou é uma exceção explícita e documentada — nunca um import direto "só dessa vez". | arquitetura |
| 5 | **Agendamento das importações diárias** | O playbook diz "sem deployment" (capítulo 4). Importação diária precisa de gatilho recorrente: cron externo chamando a rota, agendamento do orquestrador, ou outra coisa. Decidir muda o que se instala. | arquitetura + infra |
| 6 | **Disponibilidade parcial e atraso dos custodiantes** | "Ainda não publicou" **não é** falha: não deveria encher o log de erro nem gastar retry. Falta definir como isso se representa (estado próprio? janela de tolerância por custodiante?). | operações + produto |
| 7 | **Conciliação carteira × extrato** | Qual módulo faz. É o primeiro caso que olha os dois lados ao mesmo tempo, então ou nasce um terceiro módulo, ou um deles consome o `public.py` do outro. | produto + arquitetura |
| 8 | **Termos de uso para scraping de portais** | Antes de ligar qualquer gateway de scraping num portal real, confirmar que os termos do custodiante permitem acesso automatizado. | jurídico |

## Em aberto na estrutura (capítulo 3)

| # | Em aberto | Situação |
|---|---|---|
| 9 | **Módulos no plural ou no singular** | O playbook usa plural (`ativos`, `boletas`); os módulos de integração nasceram no singular (`custodiante`, `carteira`, `extrato`). |
| 10 | **Idioma por camada** | Convivem identificadores em inglês e em português. A proposta é domínio em português, vocabulário técnico em inglês — falta decidir e aplicar. |
| 11 | **Localização dos testes** | Árvore paralela (hoje) ou dentro do módulo (facilita extrair o módulo depois). |
| 12 | **Qual object storage** | A porta (`core/storage.py`) é agnóstica e tem adaptador compatível com S3; falta escolher o provedor e o prazo de retenção (com compliance). |
| 13 | **Tabelas × JSONB** para posições e lançamentos | Hoje tabela. Pode mudar se o canônico crescer muito por classe de ativo (item 2). |

## Como sair daqui

Item resolvido vira, **no mesmo commit**: a mudança no código, a remoção do `[AJUSTAR]` correspondente e a linha deste capítulo virando regra no capítulo certo. Decisão que fica só na cabeça de quem decidiu volta pra cá em três meses.
