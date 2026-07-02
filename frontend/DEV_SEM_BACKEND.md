# Desenvolver o frontend sem backend

Duas formas de mexer na interface sem subir Django/Dovecot.

---

## 1. App completo com API mockada (MSW) — para páginas/layouts

Roda a aplicação inteira (`yarn dev`) com a API interceptada por dados falsos e
o login OIDC pulado. Você navega as páginas reais sem backend.

```bash
cd frontend
yarn install      # se ainda não instalou
yarn dev:mock     # = VITE_MOCK_API=true vite
```

Abra a URL que o Vite imprime (ex.: http://localhost:3000/). A app entra
"logada" como um SuperAdmin fake.

**Como funciona (tudo atrás de `VITE_MOCK_API`, zero efeito em produção):**

- `src/mocks/` — handlers e dados de exemplo do [MSW](https://mswjs.io).
  - `fixtures.js` — os dados falsos (usuário, mailboxes, e-mails, domínios…).
  - `handlers.js` — quais endpoints respondem o quê. Um **catch-all** devolve
    lista vazia (`{count:0, results:[]}`) e avisa no console quando uma view
    bate num endpoint ainda sem fixture.
  - `browser.js` — registra o service worker.
- `src/main.js` — só inicia o MSW quando `VITE_MOCK_API` está ligado (import
  dinâmico → o msw **não** entra no bundle de produção).
- `src/stores/auth.store.js` — `validateAccess()` pula o OIDC no modo mock.

**Para mexer numa view específica:** abra o console, veja qual endpoint o
catch-all reclamou (`[mock] sem fixture: GET /api/v2/...`), e adicione um
handler em `handlers.js` devolvendo o shape que a view espera (use os dados de
`fixtures.js` como base).

---

## 2. Storybook — para componentes isolados

> ⚠️ **Scaffold não verificado.** O ambiente onde isto foi gerado não conseguiu
> baixar o Storybook (rede). Os arquivos de config estão prontos em
> `.storybook/`, mas **falta instalar as dependências** e dar o primeiro
> `yarn storybook` (pode precisar de um pequeno ajuste no `viteFinal`).

```bash
cd frontend
yarn add -D storybook@^10 @storybook/vue3-vite@^10
yarn storybook        # abre em http://localhost:6006
```

- `.storybook/main.js` — config; remove os plugins de Module Federation do
  `vite.config.js` (não fazem sentido para componentes isolados).
- `.storybook/preview.js` — instala Vuetify + i18n + Pinia + um router em
  memória, e envolve cada história num `<v-app>`.
- `.storybook/Welcome.stories.js` — história de exemplo (botões + tema).

**Criar história de um componente** (co-locada em `src/`):

```js
// src/components/tools/ColorField.stories.js
import ColorField from '@/components/tools/ColorField.vue'

export default { title: 'Tools/ColorField', component: ColorField }
export const Default = { args: { modelValue: '#046BF8' } }
```

Se o primeiro `yarn storybook` reclamar de algum plugin do Vite (ex.: o vue
plugin duplicado), ajuste o `viteFinal` em `.storybook/main.js`.
