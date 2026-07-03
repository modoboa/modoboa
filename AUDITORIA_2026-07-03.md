# Auditoria Modoboa — 21 Jul 2026

Varredura completa do repo (`modoboa/` + `frontend/src/`) em busca de bugs de
lógica, segurança e performance. Achados verificados diretamente no código
(`file:line`), mais severos primeiro.

Status: **revisado em 21 Jul 2026** — 16 achados pendentes / 3 achados já corrigidos no código (#3, #16, #17). Separar em PRs sugeridos no final.

---

## 🔴 Críticos / High — lógica

### 1. Reply/Forward apaga rascunho errado (UID de rascunho = UID da msg original)

- **Arquivo:** `frontend/src/components/webmail/ComposeEmailForm.vue:323`
- **Backend impactado:** `modoboa/webmail/serializers.py:308-309`
- **Bug:**
  - `ComposeEmailForm.vue:323`:
    ```js
    const draftMailid = ref(route.query.mailid || null)
    ```
    Em `ReplyEmailView`/`ForwardEmailView`, `route.query.mailid` é o UID da
    mensagem **original** (em INBOX/etc.), não de um Draft.
  - `serializers.py:308-309`:
    ```python
    if "mailid" in validated_data:
        imapc.delete_mail(drafts_folder, validated_data["mailid"])
    ```
    Emite `STORE +FLAGS \Deleted; EXPUNGE` em `Drafts` com o UID da msg original.
    Se Drafts tiver um draft cujo UID coincide com o da msg original (o espaço
    de UIDs é por-mailbox), ele é **destruído silenciosamente** no primeiro
    autosave (3s após qualquer tecla) de uma resposta.
  - Confirmação da origem do `mailid` em `EmailContent.vue:428/435`:
    ```js
    router.push({ name: 'ReplyEmailView', query: { mailbox: props.mailbox, mailid: props.mailid } })
    ```
    `props.mailbox` aqui é a mailbox da mensagem original, não `Drafts`.
- **Impacto:** perda silenciosa de drafts do usuário sem qualquer aviso.
- **Fix sugerido:** inicializar só quando já estiver editando um draft:
  ```js
  const draftMailid = ref(
    route.query.mailbox === constants.DRAFTS_FOLDER ? route.query.mailid : null
  )
  ```

### 2. Swipe-delete comete contra a mailbox *atual*, não a da origem do swipe

- **Arquivo:** `frontend/src/components/webmail/EmailList.vue:665-674`
- **Bug:**
  - `commitDelete` (l.672):
    ```js
    api.deleteSelection(currentMailbox.value, [entry.imapid]).then(...)
    ```
    onde `currentMailbox = computed(() => route.query.mailbox || 'INBOX')`
    (l.485-487), i.e. **a mailbox corrente no momento do commit**, não quando o
    swipe disparou.
  - O watcher de `props.mailbox` (l.958-965) só chama `reloadListing()` — **não
    dá flush** em `pendingDeletes` nem captura a mailbox de origem:
    ```js
    watch(() => props.mailbox, () => {
      search.value = ''
      reloadListing()
    })
    ```
  - Cenário: swipe-deleta msg em INBOX → troca para Trash dentro de 5s →
    `commitDelete` dispara contra Trash com UID do INBOX. O backend
    (`webmail/viewsets.py:231-237`) interpreta `delete` em Trash como
    **EXPUNGE permanente** → mensagem destruída sem recovery e sem Undo.
- **Impacto:** perda permanente de e-mail do usuário (não vai para Trash,
  expurga direto).
- **Fix sugerido:**
  - Em `swipeDelete` (l.688): `const entry = { mailbox: currentMailbox.value, imapid, row, index }`
  - Em `commitDelete`: `api.deleteSelection(entry.mailbox, [entry.imapid])`
  - No watcher de `props.mailbox`: `pendingDeletes.value.slice().forEach(commitDelete)`
    antes de `reloadListing()`.

---

## 🔴 High — segurança

### 3. [CORRIGIDO] `UserAccountViewSet` sem `permission_classes` → AllowAny por default

> [!NOTE]
> **Status:** **Já corrigido no código.** `permission_classes = (permissions.IsAuthenticated, lib_viewsets.HasMailbox)` já está presente em `modoboa/admin/api/v2/viewsets.py`.

- **Arquivo:** `modoboa/admin/api/v2/viewsets.py:326`
- **Bug:**
  ```python
  class UserAccountViewSet(GetThrottleViewsetMixin, viewsets.ViewSet):
      """Viewset for current user operations."""

      @action(methods=["get", "post"], detail=False)
      def forward(self, request, **kwargs):
          mb = request.user.mailbox
          ...
  ```
  Sem `permission_classes`. Verificado: **não existe**
  `DEFAULT_PERMISSION_CLASSES` em `modoboa/test_settings.py`, nem nos settings
  de produção (`test_project/test_project/settings.py`), nem nos templates em
  `modoboa/core/commands/templates/settings.py.tpl`. O único hit no repo está
  em `doc-ng/installation/upgrade.md:2106`. Logo DRF usa `AllowAny`.
  - A action `forward` (l.330) дереferencia `request.user.mailbox` → cliente
    anônimo causa 500 e furava o `IsAuthenticated` que **todos** os viewsets
    irmãos impõem.
- **Impacto:** bypass de auth na action `forward`; potencial enum/info via
  erro do 500.
- **Fix sugerido:**
  ```python
  class UserAccountViewSet(GetThrottleViewsetMixin, viewsets.ViewSet):
      permission_classes = (permissions.IsAuthenticated, lib_viewsets.HasMailbox)
  ```

---

## 🟡 Medium

### 4. `persistDraft` sem single-flight → autosave + "Salvar" manual duplicam draft

- **Arquivo:** `frontend/src/components/webmail/ComposeEmailForm.vue:529-556`
- **Bug:**
  - `autosaving.value`/`working.value` só guardam `autosave`/`saveDraft`
    (l.570-575, l.558-565). **Não guardam `persistDraft`**:
    ```js
    const persistDraft = async () => {
      if (!route.query.uid) return
      const snapshot = draftSnapshot()
      if (snapshot === lastSavedSnapshot) return
      autosaving.value = true
      try {
        const body = prepareMessage()
        const resp = await api.saveComposeSession(route.query.uid, body)
        if (resp?.data?.mailid) draftMailid.value = resp.data.mailid
        lastSavedSnapshot = snapshot
      } ...
    }
    ```
  - Enquanto autosave está in-flight, `saveDraft()` (manual) chama
    `persistDraft()` novamente **com o mesmo `draftMailid`**. O backend
    (`serializers.py:308-310`) faz delete-then-push: o 2º save perde a ref ao
    original → **2 drafts** resultam.
- **Fix sugerido:** `if (autosaving.value) return` no topo de `persistDraft`
  (ou single-flight via Promise compartilhada).

### 5. SSRF em `check_connection` (IMAP migration)

- **Arquivo:** `modoboa/imap_migration/api/v2/viewsets.py:47-59`
- **Bug:** qualquer DomainAdmin/Reseller força o servidor a abrir
  `imaplib.IMAP4[_SSL](host, port)` para host:port arbitrário do cliente —
  port-scan / fingerprinting de serviços internos a partir de conta de tenant
  confiável.
- **Fix sugerido:** resolver host e rejeitarloopback/private/link-local antes
  de conectar (ex. via `ipaddress.ip_address(...).is_private`).

### 6. Chaves RSA OIDC privadas commitadas no repo

- **Arquivos:** `test_project/test_project/settings.py:211-225` e
  `test_project/oidc_key` (PEM 4096-bit completo)
- **Bug:** apesar do comentário `# DEV ONLY`, deploys que reaproveitam
  `test_project` settings ou esquecem `OIDC_RSA_PRIVATE_KEY` do env assinam
  tokens OIDC com chave **publicamente conhecida** → forja de token.
- **Fix sugerido:**
  - Remover os arquivos do repo (git history também, se possível).
  - `modoboa/core/utils.py:62` **já gera** chave quando o env var está ausente.
  - CI já recebe `${{ vars.OIDC_RSA_PRIVATE_KEY }}`
    (`.github/workflows/modoboa.yml:150`) — basta garantir que produção leia
    do env, não de settings hardcoded.

---

## 🟡 N+1 de performance (verificados)

### 7. `DomainViewSet.list` — ~10+ queries/Redis por domínio na página

- **Arquivos:** `modoboa/admin/api/v2/viewsets.py:62` (sem annotate/prefetch) +
  `modoboa/admin/models/domain.py`.
- **Queries por domínio (verificadas):**
  | Linha | Propriedade | Query |
  | --- | --- | --- |
  | 99 | `mailbox_count` | `self.mailbox_set.count()` |
  | 94/102 | `mbalias_count`/`domainalias_count` | `self.<rel>.count()` |
  | 113 | `opened_alarms_count` | `self.alarms.opened().count()` |
  | 152-181 | `dns_global_status` | 5x `dnsrecord_set.filter(type=…).first()` + `mxrecord_set.has_valids()` + `dnsblresult_set` |
  | 215 | `allocated_quota_in_percent` | `self.mailbox_set.aggregate(Sum('quota'))` |
  | mixins.py:16 | `sent_messages` | Redis round-trip por domínio |
- **Fix sugerido:**
  ```python
  .annotate(
      mailbox_count=Count('mailbox', distinct=True),
      mbalias_count=Count('alias', distinct=True, filter=Q(alias__internal=False)),
      ...
  )
  .prefetch_related('dnsrecord_set', 'mxrecord_set', 'dnsblresult_set', 'alarms')
  ```
  + cache por linha de `dns_global_status`/`sent_messages`.

### 8. `AccountViewSet.list` — sem `select_related('mailbox','mailbox__domain')`

- **Arquivos:** `modoboa/admin/api/v2/viewsets.py:203` (v2) e
  `modoboa/admin/api/v1/viewsets.py:120` (v1).
- **Queries por conta (verificadas):**
  - `AccountSerializer.get_role` (`api/v1/serializers.py:285`) →
    `account.role` (`core/models.py:272`) → `self.groups.all()[0]` (query/linha).
  - `MailboxSerializer` aninhado requer `account.mailbox` sem
    `select_related('mailbox')`.
  - v1 `MailboxSerializer.quota_usage` → `mb.get_quota_in_percent()` →
    `Quota.objects.get(username=...)` por mailbox.
  - v2 `AccountSerializer.aliases = source='mailbox.alias_addresses'`
    (`mailbox.py:159`) → query + `alias` JOIN extra.
  - `AccountSerializer.get_domains` (`serializers.py:289`) →
    `Domain.objects.get_for_admin(account)...values_list(...)` por conta.
- **Fix sugerido:**
  ```python
  .select_related('mailbox', 'mailbox__domain')
  .prefetch_related(
      'groups', 'mailbox__aliasrecipient_set__alias', 'userobjectlimit_set'
  )
  ```
  + bulk `Quota` em 1 query (filtrar por usernames da página).

---

## 🟢 Low / extras

### 9. `IdentityViewSet.list` sem paginação + pós-filtro Python
- `admin/api/v2/viewsets.py:246` + `admin/lib.py:80` (carrega todas as
  identidades e filtra `type` em Python).
- Fix: adicionar `pagination_class` + annotation
  `recipients_count=Count('aliasrecipient')` + `prefetch_related('aliasrecipient_set')`
  + trocar pós-filtro Python por filtro DB (`internal=False`).

### 10. `amavis/sql_connector.py:157` — `messages_count` materializa quarentena
- `len(self.messages)` avalia **todas** as rows só p/ contar. Fix: usar
  `self.messages.count()` (SELECT COUNT separado) e deixar o `fetch()`
  re-aplicar `LIMIT/OFFSET` na mesma filter.

### 11. `admin/api/v2/viewsets.py:142,256` (`export`) — CSV inteiro em memória
- `for domain in queryset: result += domain.to_csv_rows()` acumula lista sem
  streaming. Fix: `StreamingHttpResponse` com generator.

### 12. `dmarc/lib.py:331,345` — itera `all_records` 2x
- `ips = (r.source_ip for r in all_records)` depois `for record in all_records:`
  → 2 SELECTs idênticos. Fix: `records = list(all_records)` uma vez e reutilizar.

### 13. `admin/handlers.py:97` — `mailbox_deleted_handler` é N+1
- Loop deleta cada `AliasRecipient` individualmente e por alias chama
  `alias.aliasrecipient_set.exists()` antes de `alias.delete()` (2N+1).
- Fix:
  ```python
  AliasRecipient.objects.filter(...).delete()  # bulk
  Alias.objects.filter(aliasrecipient__isnull=True, address__in=[...]).delete()
  ```

### 14. `EmailList.vue:966-975` — select-all nunca fica indeterminate
```js
watch(() => webmailStore.selection, () => {
  if (!webmailStore.selection.length) selectAll.value = false
  else selectAll.value = true   // ← 1 selecionado ⇒ box 100% marcada
})
```
- Fix: `selectAll.value = store.emails.length > 0 &&
  webmailStore.selection.length === store.emails.length` (ou usar
  `indeterminate` no `v-checkbox`).

### 15. `EmailContent.vue:378-418` — ações sem `.catch`/`finally`
- `deleteEmail`/`restoreEmail`/`markEmailAsJunk`/`markEmailAsNotJunk`: setam
  `working=true` e só `.then` resetam. Em rejeição o botão fica travado em
  loading e `emit('deleted')` nunca dispara.
- Fix: `.catch` + `finally { working.value = false }`; em erro, reverter patch
  otimista (ou chamar `reloadListing()`).

### 16. [CORRIGIDO] LDAP filter/DN injection — `ldapsync/lib.py:101,126,155-157`
> **Status:** **Já corrigido no código.** `escape_dn_chars` e `escape_filter_chars` já são aplicados em `modoboa/ldapsync/lib.py`.

### 17. [CORRIGIDO] `pdfcredentials/lib.py:43` — path traversal via `account.username`
> **Status:** **Já corrigido no código.** `get_creds_filename` já valida se o caminho não escapa do diretório com `if os.path.dirname(fname) != storage_dir: raise InternalError...`.

### 18. `amavis/lib.py:42` — `secret_id` sem compare const-time
- `if secret_id != smart_str(msgrcpt.mail.secret_id):` (timing attack no token
  de liberação de quarentena self-service).
- Fix: `if not hmac.compare_digest(force_str(secret_id), smart_str(...)):`.

### 19. `webmail/viewsets.py:166-179` — paginação out-of-range retorna `count:0`
- Quando `paginator.getpage(page)` é `None`, response envelope hardcode
  `count: 0`. Clientes que leem `count` como total real vêem mailbox fantasma.
- Fix: incluir `"count": total` (computado em l.163) no branch de página vazia.

---

## Categorias sem achados (auditadas)

- **SQL injection / raw query**: únicos `cursor.execute` (`amavis/sql_connector.py:62`,
  `amavis/checks/settings_checks.py:51/53`) são parametrizados.
- **XSS / templates**: `|safe` em `login.html:38`,
  `generic_fields_group.html:17`, `generate_postfix_maps.py:78/86`,
  `settings.py.tpl:183` são outputs auto-escapados ou announcements
  admin-controlados (intencional).
- **CSRF**: único `csrf_exempt` (`autoconfig/views.py:64`) é stateless e
  intencional (Outlook POSTa XML sem cookie).
- **Command injection / subprocess**: `lib/sysutils.py:41`,
  `pdfcredentials/tests/test_lib.py:62/70`, DKIM `openssl` em
  `_manage_dkim_keys.py:66/78` — todos list-form ou fixed strings; nomes de
  domínio já validados contra traversal (`_manage_dkim_keys.py:25-42`).
- **Secrets em logs**: nenhum logger emite senha/token (policyd só loga
  SASL username/counter; `core/jobs.py:19` loga idade).
- **`WEBMAIL_IMAP_POOL`**: pool corretamente gated; email list faz 1 SORT +
  1 bulk FETCH por página (`webmail/lib/imaputils.py:846`), sem round-trip por
  msg.
- **`LocalConfig` per request**: `get_instance` (`core/models.py:514`) é cached
  via Django cache c/ invalidação on save/delete; middleware reusa. OK.
- **`parameters/tools.py`**: lê `_parameters` em memória; defaults no
  registry. Sem hit DB por chamada.
- **Migrations / `post_delete` orphans / `m2m_changed`**: handlers de
  `admin/handlers.py:97-140` limpam alias recipients + self-alias + quota OK;
  nada deixa órfão nos paths webmail.
- **Bare `except`**: `webmail/lib/{imaputils,imapheader,imapemail,fetch_parser,sendmail,attachments}.py`
  têm `except: pass` em decodes / `OSError` / `CHECK` no logout — todos
  estreitos e intencionais.
- **`datetime.now()` vs `timezone.now()`**: só `webmail/lib/imapheader.py:120`
  usa `datetime.now()` naive; comparado com `datetime.fromtimestamp` (mesmo
  frame TZ) — sem bug.
- **mark_as_junk #66**: já corrigido em `webmail/viewsets.py:247-251`.

---

## Sugestão de split em PRs

| PR | Escopo | Itens |
| --- | --- | --- |
| **hotfix** | Segurança + perda de dados | #1, #2 (#3 já corrigido) |
| **perf** | N+1 list pages | #7, #8 (+ #9 se caber) |
| **cleanup** | Resto | #4, #5, #6, #10-15, #18, #19 (#16 e #17 já corrigidos) |

Ordem recomendada: hotfix → perf → cleanup. Os hotfixes podem ser cherry-picked
em `master` direto; os de perf merecem testes de regressão nos endpoints de
listagem (Domain/Account) p/ confirmar que annotate/prefetch não mudam shape do
JSON.