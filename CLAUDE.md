# CLAUDE.md — contexto do projeto (fork BrunoNyland/modoboa)

Memória de projeto para o Claude Code. Lida automaticamente no início de cada
sessão. Mantém o contexto e as decisões já tomadas para não serem
re-descobertas/re-litigadas.

## O que é

Fork pessoal do **Modoboa** (plataforma de e-mail em Django) rodando em
produção em `mail.sintraffms.com` (~10 usuários, **PostgreSQL 18** desde
14/10/2026, uWSGI, Dovecot, nginx, layout do `modoboa-installer` em
`/srv/modoboa/`). O foco do trabalho neste fork tem sido **performance** e
**DX do frontend**.

**Projeto próprio, não acompanha mais o upstream** (decisão de 14-15/10/2026):
nada de merge/sync com `modoboa/modoboa` nem `modoboa-installer`. Mudanças do
upstream que valham a pena entram por cherry-pick ou reescrita, uma a uma.
Só PostgreSQL é suportado e testado (MySQL saiu do CI).

## Stack

- **Backend:** Django 6.1 (Python 3.12+, produção em 3.14), Django REST Framework 3.18, `oauth2_provider` (OIDC), Redis
  (cache + RQ), per-app "parameters registry" (`modoboa/parameters/tools.py`).
- **Frontend** (`frontend/`): Vue 3 + Vuetify 4, **Vite 8 (Rolldown)**,
  **Module Federation** (`@module-federation/vite`), `vue3-gettext`, Pinia,
  vue-router, axios, auth via `oidc-client-ts`.
- **Deploy do frontend:** o build vai para `modoboa/frontend_dist/`; o comando
  `load_initial_data` cria symlinks de `{BASE_DIR}/frontend/` para cada entrada
  do `frontend_dist` (exceto `config.json`); o nginx serve direto.

## Desenvolver o frontend SEM backend (principal p/ trabalho local)

Ver `frontend/README.md` e `frontend/DEV_SEM_BACKEND.md`. Resumo:

```bash
cd frontend && yarn install && yarn dev:mock   # cross-env VITE_MOCK_API=true vite
```

- App sobe **logada** (SuperAdmin fake), API interceptada pelo **MSW**, em
  **HTTP** (o `vite.config.js` desliga o `basicSsl`/https no modo mock, senão o
  cert autoassinado quebra o registro do service worker).
- Mocks em `frontend/src/mocks/`: `fixtures.js` (dados), `handlers.js`
  (endpoints; tem um **catch-all** que loga `[mock] sem fixture: ...` no
  console), `browser.js` (worker).
- Tudo atrás de `VITE_MOCK_API` (import dinâmico) → **msw não entra no bundle de
  produção**. O bypass do OIDC está em `src/stores/auth.store.js`
  (`validateAccess`/`login`/`$reset`), checando `import.meta.env.VITE_MOCK_API`
  **ou** o global `globalThis.__MODOBOA_MOCK_API__` setado no `main.js` (o env
  não é injetado de forma confiável nos módulos expostos via Module Federation).
- `useGlobalConfig` mora em `src/config.js` (não em `main.js`) para evitar ciclo
  `store ↔ main`.
- **Storybook** (componentes isolados): scaffold em `.storybook/`. Falta
  instalar localmente: `yarn add -D storybook@^10 @storybook/vue3-vite@^10 && yarn storybook`.

## Decisões / trabalho já feito (NÃO re-litigar)

- **Cache do LocalConfig à prova de migrate** (`core/models.py` +
  `parameters/tools.py`): os defaults do registry são carregados sob demanda via
  `Registry.ensure_defaults()`. Cache fica ligado por padrão (timeout 300);
  **não** precisa mais de `MODOBOA_LOCALCONFIG_CACHE_TIMEOUT = 0`.
- **Ícones MDI em SVG** (`@mdi/js`, `vuetify/iconsets/mdi-svg`, mapa em
  `src/plugins/icons.js`) — não voltar para a webfont.
- **Roboto auto-hospedado** (`@fontsource/roboto`, latin + latin-ext, pesos
  300/400/500/700) — sem Google Fonts externo.
- **Assets imutáveis:** o plugin `relocateMfBootstrap` no `vite.config.js`
  dá **hash de conteúdo** aos `mf-entry-bootstrap-*.js` → todo `/assets/`
  é content-addressed. No nginx, `location ^~ /assets/` é `immutable`;
  `index.html` e `/remoteEntry.js` ficam no-cache (revalidam). `remoteEntry.js`
  é unhashed **de propósito** (contrato estável do Module Federation).
- **Dovecot `auth_cache`** (ops, no servidor): TTL 1h. Cortou o `AUTHENTICATE`
  de ~320ms → ~80ms (o custo era a introspection do token / PBKDF2 do
  client-secret).
- **Pool de conexões IMAP** (`webmail/lib/imap_pool.py`): reusa a conexão IMAP
  autenticada por usuário/worker. Atrás da flag **`WEBMAIL_IMAP_POOL`** (ligada
  em produção). Depende do uWSGI ser **só-processos, sem threads** (sem locks).
  Webmail ficou ~85% mais rápido (~500ms → ~73ms).

## Build / release / deploy

- **`release.yml`** (workflow): em `release: published` ou tag `v*`, builda
  frontend + compila `.mo` + `python -m build` → anexa o **wheel** na Release.
  A tag/Release tem que apontar para o commit do fix (o build usa o ref da tag).
- **Versionamento:** `setuptools_scm`; versões locais `2.9.1+sintraN`.
- **Atualizar o servidor:** script `modoboa-update.sh` (detecta versão, baixa o
  wheel da última release, instala, roda `migrate`/`collectstatic`/
  `load_initial_data`, reinicia o uWSGI).
- **Gotcha:** o `index.html` precisa ser **symlink** (o `load_initial_data`
  recria). Se virar arquivo real, serve HTML velho apontando p/ assets errados.

## Convenções

- **Antes de implementar qualquer proposta do Bruno, apresentar primeiro as
  desvantagens / trade-offs / riscos** (custo, manutenção, segurança, UX) e só
  seguir após o ok. Ser honesto quando o ganho for cosmético ou marginal —
  recomendar não fazer quando não compensar.
- **CI:** `modoboa.yml` (matriz Python) tem `paths-ignore: frontend/**` →
  mudanças só-frontend não rodam os testes Python, só o `frontend.yml` (`build`).
- **Gerenciador:** **yarn** (clássico, com `yarn.lock`). Não versionar
  `package-lock.json` (npm). O release usa `yarn install --frozen-lockfile` →
  não adicione deps ao `package.json` sem atualizar o `yarn.lock` no mesmo commit.
- **Nunca versionar capturas de rede (`*.har`)** — contêm tokens/cookies.
- **Flags de dev** (`VITE_MOCK_API`, `WEBMAIL_IMAP_TIMING`) devem ser
  importadas/usadas de forma que o build de produção fique intacto.
- **Testes:** backend `cd test_project && DB=sqlite python manage.py test <app>`;
  frontend `yarn test` (vitest).
- **Testes na VPS de produção: nunca contra o Redis do e-mail.** A suíte usa o
  Redis no DB 0 (`REDIS_PORT`, padrão 6379) e apaga/reescreve contadores do
  policyd e cotas. Suba um Redis descartável
  (`redis-server --port 6391 --save "" --daemonize yes`) e rode com
  `REDIS_PORT=6391`.
- **Não rode a suíte como root fora de um contêiner.** `test_dkim_key_creation`
  conta que gravar em `/I_DONT_EXIST` falhe; como root a gravação funciona, cria
  a pasta na raiz do sistema e o teste passa a falhar nas execuções seguintes.
- Os testes do policyd sobem o daemon em `POLICYD_TEST_PORT` (padrão 19999).
  Antes usavam a 9999, a mesma do policyd de produção: o de teste não subia e
  os testes conversavam com o policyd real (falhas "de ambiente" que eram isso).
- Fora do CI, 3 testes do amavis (`test_mark_as_ham`, `test_mark_as_spam`,
  `test_manual_learning_as_user`) falham sem o `sa-learn`/spamd configurado;
  não é regressão.
- **Commits:** trailer `Co-Authored-By: Claude ...` + `Claude-Session: ...`.
  PRs criados como **draft**; mergeados após CI verde.
- **Idioma de commits/PRs:** títulos e mensagens sempre em **inglês**.
- **Conteúdo de commits/PRs:** sempre detalhar o que está sendo feito (o quê
  e por quê). Se for fix de bug ou melhoria de performance, incluir também
  **como replicar/testar** (passos concretos, comandos, viewport, etc.).
- Não incluir identificadores internos de modelo em commits/PRs/código.
- **Comandos de servidor/ops para o Bruno rodar via SSH:** sempre entregar
  numa única linha, encadeados com `&&` (não em blocos separados/multi-step).
