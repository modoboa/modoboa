/**
 * Handlers do MSW para o modo de desenvolvimento sem backend.
 *
 * Os paths usam curinga (`*`) no início porque o baseURL real é `/api/v2/`.
 * Para mexer numa view específica, adicione um handler aqui devolvendo o
 * shape que aquela view espera. O handler catch-all do final evita que a app
 * quebre em endpoints ainda não mockados (e avisa no console).
 */
import { http, HttpResponse, delay } from 'msw'

import * as fx from './fixtures'

const json = (data, init) => HttpResponse.json(data, init)

// In-memory attachments per compose session (mock mode only).
const composeSessions = {}

// ----- webmail: helpers das caixas com estado (fx.webmailMessages) -----
const WEBMAIL_PAGE_SIZE = 20

const webmailBox = (name) => fx.webmailMessages[name] || []

// Remove da caixa de origem as mensagens da seleção (na ordem pedida).
function webmailTake(mailbox, selection) {
  const list = webmailBox(mailbox)
  const taken = []
  for (const id of selection || []) {
    const idx = list.findIndex((m) => m.imapid === String(id))
    if (idx !== -1) {
      taken.push(list.splice(idx, 1)[0])
    }
  }
  return taken
}

// Insere mensagens numa caixa destino com UID NOVO — mesmo contrato do IMAP
// real (o UID antigo deixa de valer após move/delete).
function webmailAppend(mailbox, messages) {
  if (!fx.webmailMessages[mailbox]) {
    fx.webmailMessages[mailbox] = []
  }
  const list = fx.webmailMessages[mailbox]
  let nextId = list.reduce((mx, m) => Math.max(mx, Number(m.imapid)), 0)
  for (const msg of messages) {
    nextId += 1
    list.unshift({ ...msg, imapid: String(nextId) })
  }
}

export const handlers = [
  // ----- bootstrap (necessário para a app subir "logada") -----
  http.get('*/account/me/', () => json(fx.currentUser)),
  http.get('*/account/available_applications/', () => json(fx.applications)),
  http.get('*/capabilities/', () =>
    json({
      capabilities: {
        imap_migration: {},
        rspamd: { location: '/rspamd' },
      },
    })
  ),

  http.get('*/admin/news_feed/', () => json([])),
  http.get('*/admin/statistics/', () =>
    json({
      domain_count: 1,
      domain_alias_count: 0,
      account_count: 1,
      alias_count: 0,
    })
  ),
  http.get('*/admin/components/', () =>
    json([
      {
        name: 'modoboa',
        version: '3.0.0',
        last_version: '3.0.0',
        description: 'Core mail hosting platform',
        changelog_url: null,
        update: false,
      },
      {
        name: 'modoboa-webmail',
        version: '2.1.0',
        last_version: '2.1.0',
        description: 'Webmail plugin for Modoboa',
        changelog_url: null,
        update: false,
      },
    ])
  ),
  http.get('*/notifications/', () => json([])),
  http.get('*/alarms/', () => json(fx.alarms)),
  // CategoryViewSet não usa paginação: devolve um array puro. Sem este handler,
  // o catch-all paginado ({count,results}) faria `categories.value` virar um
  // objeto não-iterável e quebraria o AddressBook (for...of em leftMenuItems).
  http.get('*/categories/', () =>
    json([
      { pk: 1, name: 'Family' },
      { pk: 2, name: 'Work' },
    ])
  ),
  http.get('*/statistics/', () =>
    json({
      graphs: {
        averagetraffic: {
          title: 'Average Traffic',
          series: [
            {
              name: 'Received',
              data: [
                [1719266400000, 10],
                [1719270000000, 15],
                [1719273600000, 8],
              ],
            },
            {
              name: 'Sent',
              data: [
                [1719266400000, 5],
                [1719270000000, 12],
                [1719273600000, 14],
              ],
            },
          ],
        },
        averagetrafficsize: {
          title: 'Average Traffic Size (KB)',
          series: [
            {
              name: 'Size',
              data: [
                [1719266400000, 1024],
                [1719270000000, 2048],
                [1719273600000, 512],
              ],
            },
          ],
        },
        accountcreationgraphic: {
          title: 'Account Creations',
          series: [
            {
              name: 'Creations',
              data: [
                [1719266400000, 1],
                [1719270000000, 0],
                [1719273600000, 2],
              ],
            },
          ],
        },
      },
    })
  ),
  // Sem remotes/plugins federados no modo mock:
  http.get('*/frontend/plugins/', () => json([])),
  http.get('*/parameters/global/applications/', () => json(fx.parameterApps)),
  http.get('*/parameters/global/structure/', ({ request }) => {
    const url = new URL(request.url)
    const app = url.searchParams.get('app')
    if (app === 'core') {
      return json([
        {
          label: 'Geral',
          display: '',
          parameters: [],
        },
      ])
    }
    if (app === 'imap_migration') {
      return json([
        {
          label: 'Migração IMAP',
          display: '',
          parameters: [
            {
              name: 'enabled_imapmigration',
              label: 'Ativar migração IMAP',
              help_text: 'Habilita migração IMAP para os domínios',
              widget: 'BooleanField',
              display: '',
            },
          ],
        },
      ])
    }
    return json([
      {
        label: 'Configurações',
        display: '',
        parameters: [],
      },
    ])
  }),
  http.get('*/parameters/global/:app/', ({ params }) => {
    if (params.app === 'imap_migration') {
      return json({
        label: 'Migração IMAP',
        params: { enabled_imapmigration: true },
      })
    }
    if (params.app === 'core') {
      return json({
        label: 'Geral',
        params: {},
      })
    }
    return json({ label: 'Configurações', params: {} })
  }),
  http.put('*/parameters/global/:app/', async ({ request, params }) => {
    const body = await request.json()
    return json({
      label:
        params.app === 'core'
          ? 'Geral'
          : params.app === 'imap_migration'
            ? 'Migração IMAP'
            : 'Configurações',
      params: body,
    })
  }),

  // ----- user parameters -----
  http.get('*/parameters/user/applications/', () => json(fx.userParameterApps)),
  http.get('*/parameters/user/structure/', ({ request }) => {
    const url = new URL(request.url)
    const app = url.searchParams.get('app')
    if (app === 'core') {
      return json([
        {
          label: 'Geral',
          display: '',
          parameters: [
            {
              name: 'items_per_page',
              label: 'Itens por página',
              help_text: 'Número de itens exibidos nas tabelas',
              widget: 'NumberField',
              display: '',
            },
          ],
        },
      ])
    }
    return json([])
  }),
  http.get('*/parameters/user/:app/', ({ params }) => {
    if (params.app === 'core') {
      return json({
        label: 'Geral',
        params: {
          items_per_page: 50,
        },
      })
    }
    return json({ label: 'Configurações', params: {} })
  }),
  http.put('*/parameters/user/:app/', async ({ request, params }) => {
    const body = await request.json()
    return json({
      label: params.app === 'core' ? 'Geral' : 'Configurações',
      params: body,
    })
  }),

  // ----- languages -----
  http.get('*/languages/', () =>
    json([
      { code: 'cs', label: 'Czech' },
      { code: 'de', label: 'German' },
      { code: 'el', label: 'Greek' },
      { code: 'en', label: 'English' },
      { code: 'es', label: 'Spanish' },
      { code: 'fi', label: 'Finnish' },
      { code: 'fr', label: 'French' },
      { code: 'it', label: 'Italian' },
      { code: 'ja', label: 'Japanese' },
      { code: 'nl', label: 'Dutch' },
      { code: 'pl', label: 'Polish' },
      { code: 'pt_BR', label: 'Portuguese (BR)' },
      { code: 'ru', label: 'Russian' },
      { code: 'sv', label: 'Swedish' },
      { code: 'zh', label: 'Chinese' },
    ])
  ),

  // ----- webmail -----
  http.get('*/webmail/mailboxes/', () => {
    // Contadores derivados do estado atual das caixas mockadas.
    const mailboxes = fx.mailboxes.mailboxes.map((mb) => {
      const msgs = fx.webmailMessages[mb.name]
      if (!msgs) {
        return mb
      }
      return {
        ...mb,
        nbmessages: msgs.length,
        unseen: msgs.filter((m) => m.style === 'unseen').length,
      }
    })
    return json({ ...fx.mailboxes, mailboxes })
  }),
  http.get('*/webmail/mailboxes/unseen/', ({ request }) => {
    const url = new URL(request.url)
    const mailbox = url.searchParams.get('mailbox') || 'INBOX'
    return json({
      counter: webmailBox(mailbox).filter((m) => m.style === 'unseen').length,
    })
  }),
  http.get('*/webmail/mailboxes/quota/', () => json(fx.quota)),
  http.post('*/webmail/mailboxes/empty/', async ({ request }) => {
    const body = await request.json()
    const list = webmailBox(body.name)
    list.splice(0, list.length)
    return json({ status: 'ok' })
  }),
  http.get('*/webmail/emails/', async ({ request }) => {
    // Realistic latency: real IMAP FETCH is not instant, and it also lets
    // <v-infinite-scroll> settle between pages instead of draining the whole
    // mailbox on mount (matches production behaviour).
    await delay(300)
    const url = new URL(request.url)
    const mailbox = url.searchParams.get('mailbox') || 'INBOX'
    const page = Number(url.searchParams.get('page') || '1')
    const search = (url.searchParams.get('search') || '').toLowerCase()
    let list = webmailBox(mailbox)
    if (search) {
      list = list.filter(
        (m) =>
          m.subject.toLowerCase().includes(search) ||
          m.from_address.fulladdress.toLowerCase().includes(search)
      )
    }
    const count = list.length
    const start = (page - 1) * WEBMAIL_PAGE_SIZE
    const results = list.slice(start, start + WEBMAIL_PAGE_SIZE)
    return json({
      count,
      first_index: count ? start + 1 : 0,
      last_index: start + results.length,
      prev_page: page > 1 ? page - 1 : null,
      next_page: start + WEBMAIL_PAGE_SIZE < count ? page + 1 : null,
      results,
    })
  }),
  http.get('*/webmail/emails/content/', ({ request }) => {
    const url = new URL(request.url)
    const mailbox = url.searchParams.get('mailbox') || 'INBOX'
    const mailid = url.searchParams.get('mailid')
    // Mesmo contrato do backend real (lib/imapemail.py): `dformat=plain`
    // devolve texto puro; `context=reply` prefixa "Re: ", injeta a linha
    // "Fulano wrote:" e cita com "> "; `context=forward` prefixa "Fwd: " e
    // injeta o bloco de cabeçalhos originais.
    const dformat = url.searchParams.get('dformat') || 'html'
    const context = url.searchParams.get('context')
    const msg = webmailBox(mailbox).find((m) => m.imapid === mailid)
    if (!msg) {
      return new HttpResponse(null, { status: 404 })
    }
    // Como no IMAP: buscar o conteúdo marca a mensagem como lida.
    msg.style = ''
    let subject = msg.subject
    let body
    if (dformat === 'plain') {
      body = Array.from(
        { length: 6 },
        (_, i) =>
          `Parágrafo ${i + 1} do corpo mockado de "${msg.subject}". ` +
          'Texto suficiente para exercitar rolagem e leitura no dev:mock.'
      ).join('\n\n')
    } else if (/backup/i.test(msg.subject) && !context) {
      // E-mail texto-puro (cron/log): o backend embrulha em <pre>
      // (viewmail_plain). Linhas compridas sem espaço — o caso que era
      // cortado na borda do iframe no celular.
      const logLines = Array.from(
        { length: 20 },
        (_, i) =>
          `Erro ao processar o conteúdo da notícia número ${i + 1} do portal\n` +
          ` URL: https://exemplo.com.br/noticias/categoria/subcategoria/titulo-bem-comprido-da-noticia-${i + 1}?utm_source=cron&utm_medium=email\n` +
          `  File "/usr/lib/python3/dist-packages/urllib3/connectionpool.py", line 700, in urlopen`
      ).join('\n')
      body = `<pre>${logLines}</pre>`
    } else if (/newsletter/i.test(msg.subject) && !context) {
      // E-mail "grande" estilo marketing, imitando a saída do backend após o
      // lxml Cleaner (page_structure=True embrulha tudo num fragmento e o
      // <style> sobrevive dentro dele). CSS típico de newsletter: reset com
      // html/body { height:100% }, tabelas de 600px, cores etc — é o caso que
      // historicamente gera scroll duplo/perda de formatação no iframe.
      const rows = Array.from(
        { length: 30 },
        (_, i) =>
          `<tr><td class="cell"><h2>Seção ${i + 1}</h2>` +
          `<p>Conteúdo longo da newsletter mockada, item ${i + 1}. ` +
          'Texto suficiente para forçar rolagem vertical no leitor.</p>' +
          `<a class="btn" href="#">Botão ${i + 1}</a></td></tr>`
      ).join('')
      body =
        '<div><style>' +
        'html, body { height: 100%; margin: 0; padding: 0; }' +
        'body { background: #f2f2f7; font-family: Georgia, serif; }' +
        '.wrap { width: 600px; margin: 0 auto; background: #ffffff; }' +
        '.hero { background: #1a1a2e; color: #ffffff; padding: 32px; text-align: center; }' +
        '.cell { padding: 20px 32px; border-bottom: 1px solid #e2e2ea; }' +
        '.cell h2 { color: #4a2ea0; margin: 0 0 8px; }' +
        '.btn { display: inline-block; background: #7c5cff; color: #ffffff; ' +
        'padding: 10px 22px; text-decoration: none; font-weight: bold; }' +
        '</style>' +
        `<table class="wrap" cellpadding="0" cellspacing="0">` +
        `<tr><td class="hero"><h1>${msg.subject}</h1></td></tr>${rows}` +
        '</table></div>'
    } else {
      const paragraphs = Array.from(
        { length: 6 },
        (_, i) =>
          `<p>Parágrafo ${i + 1} do corpo mockado de "${msg.subject}". ` +
          'Texto suficiente para exercitar rolagem e leitura no dev:mock.</p>'
      ).join('')
      body = `<h3>${msg.subject}</h3>${paragraphs}`
    }
    if (context === 'reply') {
      subject = /^re\s*:/i.test(subject) ? subject : `Re: ${subject}`
      const who = msg.from_address.name || msg.from_address.address
      if (dformat === 'plain') {
        body = `${who} wrote:\n` + body.split('\n').map((l) => `>${l}`).join('\n')
      } else {
        body = `<p>${who} wrote:</p>${body}`
      }
    } else if (context === 'forward') {
      subject = `Fwd: ${subject}`
      const hdr = `Subject: ${msg.subject}\nDate: ${msg.date}\nFrom: ${msg.from_address.fulladdress}`
      body =
        dformat === 'plain'
          ? `----- Original message -----\n${hdr}\n\n${body}`
          : `<p>----- Original message -----<br>${hdr.replace(/\n/g, '<br>')}</p>${body}`
    }
    return json({
      subject,
      from_address: msg.from_address,
      to: [
        {
          fulladdress: fx.currentUser.email,
          address: fx.currentUser.email,
          name: 'Dev Admin',
        },
      ],
      cc: [],
      body,
      date: msg.date,
      attachments: msg.attachments ? [{ name: 'anexo.pdf', partnum: '2' }] : [],
    })
  }),
  http.get('*/webmail/emails/source/', ({ request }) => {
    const url = new URL(request.url)
    const mailbox = url.searchParams.get('mailbox') || 'INBOX'
    const mailid = url.searchParams.get('mailid')
    const msg = webmailBox(mailbox).find((m) => m.imapid === mailid)
    if (!msg) {
      return new HttpResponse(null, { status: 404 })
    }
    return json({
      source:
        `From: ${msg.from_address.fulladdress}\r\n` +
        `To: ${fx.currentUser.email}\r\n` +
        `Subject: ${msg.subject}\r\n` +
        `Date: ${msg.date}\r\n\r\n(corpo mockado)`,
    })
  }),
  http.post('*/webmail/emails/move/', async ({ request }) => {
    const body = await request.json()
    const taken = webmailTake(body.source, body.selection)
    webmailAppend(body.destination, taken)
    return json({ count: taken.length })
  }),
  http.post('*/webmail/emails/delete/', async ({ request }) => {
    const body = await request.json()
    const taken = webmailTake(body.source, body.selection)
    // Como o backend real: delete move para a Lixeira; se a origem JÁ É a
    // Lixeira, apaga em definitivo.
    if (body.source !== 'Trash') {
      webmailAppend('Trash', taken)
    }
    return json({ count: taken.length })
  }),
  http.post('*/webmail/emails/mark_as_junk/', async ({ request }) => {
    const body = await request.json()
    const taken = webmailTake(body.source, body.selection)
    webmailAppend('Junk', taken)
    return json({ count: taken.length })
  }),
  http.post('*/webmail/emails/mark_as_not_junk/', async ({ request }) => {
    const body = await request.json()
    const taken = webmailTake(body.source, body.selection)
    webmailAppend('INBOX', taken)
    return json({ count: taken.length })
  }),
  http.post('*/webmail/emails/flag/', async ({ request }) => {
    const body = await request.json()
    const list = webmailBox(body.mailbox)
    for (const id of body.selection || []) {
      const msg = list.find((m) => m.imapid === String(id))
      if (!msg) {
        continue
      }
      if (body.status === 'read') {
        msg.style = ''
      } else if (body.status === 'unread') {
        msg.style = 'unseen'
      } else if (body.status === 'flagged') {
        msg.flagged = true
      } else if (body.status === 'unflagged') {
        msg.flagged = false
      }
    }
    return json({ count: (body.selection || []).length })
  }),

  // ----- webmail: compose sessions + attachments -----
  // Estado em memória por sessão, só para o modo mock.
  http.get('*/webmail/compose-sessions/allowed_senders/', () =>
    json([{ address: fx.currentUser.email }])
  ),
  http.post('*/webmail/compose-sessions/', () => {
    const uid = `mock-${Date.now()}`
    composeSessions[uid] = []
    return json({ uid, attachments: [], editor_format: 'plain', signature: '' })
  }),
  http.get('*/webmail/compose-sessions/:uid/', ({ params }) =>
    json({
      uid: params.uid,
      attachments: composeSessions[params.uid] || [],
      editor_format: 'plain',
      signature: '',
    })
  ),
  http.post(
    '*/webmail/compose-sessions/:uid/attachments/',
    async ({ params, request }) => {
      const fd = await request.formData()
      const fileEntry = fd.get('attachment')
      const fname = (fileEntry && fileEntry.name) || 'arquivo.bin'
      const attachment = { fname, tmpname: `tmp-${Date.now()}` }
      composeSessions[params.uid] = composeSessions[params.uid] || []
      composeSessions[params.uid].push(attachment)
      return json(attachment)
    }
  ),
  http.delete(
    '*/webmail/compose-sessions/:uid/attachments/:name/',
    ({ params }) => {
      const list = composeSessions[params.uid] || []
      composeSessions[params.uid] = list.filter(
        (a) => a.tmpname !== params.name
      )
      return new HttpResponse(null, { status: 204 })
    }
  ),
  http.post('*/webmail/compose-sessions/:uid/send/', () => json({ status: 'ok' })),
  // Como o backend real: salvar apaga o rascunho anterior (se `mailid` veio
  // no corpo) e cria um novo com UID NOVO na pasta Drafts, devolvendo esse
  // uid. Salvar repetidamente SEM repassar o mailid retornado duplica o
  // rascunho — igual ao IMAP de verdade.
  http.post('*/webmail/compose-sessions/:uid/save/', async ({ request }) => {
    const body = await request.json()
    if (body.mailid) {
      webmailTake('Drafts', [body.mailid])
    }
    const drafts = webmailBox('Drafts')
    const mailid =
      drafts.reduce((mx, m) => Math.max(mx, Number(m.imapid)), 0) + 1
    drafts.unshift({
      imapid: String(mailid),
      subject: body.subject || '(sem assunto)',
      from_address: {
        fulladdress: body.sender,
        name: '',
        address: body.sender,
      },
      date: new Date().toISOString(),
      size: (body.body || '').length + 512,
      style: 'unseen',
      answered: false,
      forwarded: false,
      flagged: false,
      attachments: false,
    })
    return json({ ...body, mailid })
  }),

  // ----- admin (amostras) -----
  http.get('*/domains/', () => json(fx.domains)),
  http.get('*/identities/', () => json(fx.identities)),
  http.get('*/accounts/', () =>
    json({
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          pk: 1,
          username: fx.currentUser.username,
          first_name: fx.currentUser.first_name,
          last_name: fx.currentUser.last_name,
          role: fx.currentUser.role,
          is_active: true,
        },
      ],
    })
  ),
  http.get('*/logs/audit-trail/', () =>
    json({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          date_created: '2026-06-24T12:00:00Z',
          level: 'INFO',
          logger: 'admin',
          message: 'Domain example.com created successfully',
        },
        {
          date_created: '2026-06-24T12:05:00Z',
          level: 'WARNING',
          logger: 'system',
          message: 'High disk space usage threshold warning',
        },
      ],
    })
  ),
  http.get('*/logs/messages/', () =>
    json({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          queue_id: 'A1B2C3D4',
          date: '2026-06-24T12:01:00Z',
          status: 'sent',
          rcpt: 'user@example.com',
          sender: 'admin@example.com',
        },
        {
          queue_id: 'E5F6G7H8',
          date: '2026-06-24T12:03:00Z',
          status: 'deferred',
          rcpt: 'customer@external.com',
          sender: 'user@example.com',
        },
      ],
    })
  ),

  // ----- email-providers -----
  http.get('*/email-providers/', () => json(fx.emailProviders)),
  http.get('*/email-providers/:id/', ({ params }) => {
    const p = fx.emailProviders.find((p) => p.id === Number(params.id))
    return p ? json(p) : new HttpResponse(null, { status: 404 })
  }),
  http.post('*/email-providers/', async ({ request }) => {
    const body = await request.json()
    const newProvider = {
      id: fx.emailProviders.length + 1,
      ...body,
      domains: [],
    }
    fx.emailProviders.push(newProvider)
    return json(newProvider)
  }),
  http.put('*/email-providers/:id/', async ({ request, params }) => {
    const body = await request.json()
    const idx = fx.emailProviders.findIndex((p) => p.id === Number(params.id))
    if (idx !== -1) {
      fx.emailProviders[idx] = { ...fx.emailProviders[idx], ...body }
      return json(fx.emailProviders[idx])
    }
    return new HttpResponse(null, { status: 404 })
  }),
  http.delete('*/email-providers/:id/', ({ params }) => {
    const idx = fx.emailProviders.findIndex((p) => p.id === Number(params.id))
    if (idx !== -1) {
      fx.emailProviders.splice(idx, 1)
    }
    return new HttpResponse(null, { status: 204 })
  }),

  // ----- migrations -----
  http.get('*/migrations/', () => json(fx.migrations)),
  http.delete('*/migrations/:id/', ({ params }) => {
    const idx = fx.migrations.findIndex((m) => m.id === Number(params.id))
    if (idx !== -1) {
      fx.migrations.splice(idx, 1)
    }
    return new HttpResponse(null, { status: 204 })
  }),

  // ----- FIDO (WebAuthn) -----
  http.get('*/fido/', () => json(fx.fidoCreds)),
  http.put('*/fido/:id/', async ({ request, params }) => {
    const body = await request.json()
    const idx = fx.fidoCreds.findIndex((c) => c.id === Number(params.id))
    if (idx !== -1) {
      fx.fidoCreds[idx] = { ...fx.fidoCreds[idx], ...body }
      return json(fx.fidoCreds[idx])
    }
    return new HttpResponse(null, { status: 404 })
  }),
  http.delete('*/fido/:id/', ({ params }) => {
    const idx = fx.fidoCreds.findIndex((c) => c.id === Number(params.id))
    if (idx !== -1) {
      fx.fidoCreds.splice(idx, 1)
    }
    return json({ tfa_enabled: false })
  }),

  // ----- forward -----
  http.get('*/account/forward/', () => json(fx.forward)),
  http.post('*/account/forward/', async ({ request }) => {
    const body = await request.json()
    Object.assign(fx.forward, body)
    return json(fx.forward)
  }),

  // ----- armessage -----
  http.get('*/account/armessage/', () => json(fx.armessage)),
  http.put('*/account/armessage/', async ({ request }) => {
    const body = await request.json()
    Object.assign(fx.armessage, body)
    return json(fx.armessage)
  }),

  // ----- api_token -----
  http.get('*/account/api_token/', () => json(fx.apiToken)),
  http.post('*/account/api_token/', () => {
    fx.apiToken.token = '8f7d9a3b5c6e1f0d2a4b6c8d0e2f4a6b8c0d2e4f'
    return json(fx.apiToken, { status: 201 })
  }),
  http.delete('*/account/api_token/', () => {
    fx.apiToken.token = null
    return new HttpResponse(null, { status: 204 })
  }),

  // ----- filtersets & filters -----
  http.get('*/account/filtersets/', () => json(fx.filtersets)),
  http.post('*/account/filtersets/', async ({ request }) => {
    const body = await request.json()
    const newFilterSet = { name: body.name, active: false }
    fx.filtersets.push(newFilterSet)
    fx.filtersMap[body.name] = []
    return json(newFilterSet)
  }),
  http.post('*/account/filtersets/deactivate_active/', () => {
    fx.filtersets.forEach((fs) => {
      fs.active = false
    })
    return json({ status: 'ok' })
  }),
  http.get('*/account/filtersets/condition_templates/', () =>
    json(fx.conditionTemplates)
  ),
  http.get('*/account/filtersets/action_templates/', () =>
    json(fx.actionTemplates)
  ),
  http.get('*/account/filtersets/:filterset/download/', ({ params }) => {
    return json(`# Sieve Filter file for ${params.filterset}\nkeep;`)
  }),
  http.put('*/account/filtersets/:filterset/', async () => {
    return json({ status: 'ok' })
  }),
  http.delete('*/account/filtersets/:filterset/', ({ params }) => {
    const idx = fx.filtersets.findIndex((fs) => fs.name === params.filterset)
    if (idx !== -1) {
      fx.filtersets.splice(idx, 1)
      delete fx.filtersMap[params.filterset]
    }
    return new HttpResponse(null, { status: 204 })
  }),
  http.post('*/account/filtersets/:filterset/activate/', ({ params }) => {
    fx.filtersets.forEach((fs) => {
      fs.active = fs.name === params.filterset
    })
    return json({ status: 'ok' })
  }),
  http.get('*/account/filtersets/:filterset/filters/', ({ params }) => {
    return json(fx.filtersMap[params.filterset] || [])
  }),
  http.post(
    '*/account/filtersets/:filterset/filters/',
    async ({ request, params }) => {
      const body = await request.json()
      if (!fx.filtersMap[params.filterset]) {
        fx.filtersMap[params.filterset] = []
      }
      const newFilter = { ...body, enabled: true }
      fx.filtersMap[params.filterset].push(newFilter)
      return json(newFilter)
    }
  ),
  http.put(
    '*/account/filtersets/:filterset/filters/:filter/',
    async ({ request, params }) => {
      const body = await request.json()
      const filtersList = fx.filtersMap[params.filterset] || []
      const idx = filtersList.findIndex((f) => f.name === params.filter)
      if (idx !== -1) {
        filtersList[idx] = { ...filtersList[idx], ...body }
        return json(filtersList[idx])
      }
      return new HttpResponse(null, { status: 404 })
    }
  ),
  http.delete(
    '*/account/filtersets/:filterset/filters/:filter/',
    ({ params }) => {
      const filtersList = fx.filtersMap[params.filterset] || []
      const idx = filtersList.findIndex((f) => f.name === params.filter)
      if (idx !== -1) {
        filtersList.splice(idx, 1)
      }
      return new HttpResponse(null, { status: 204 })
    }
  ),
  http.post(
    '*/account/filtersets/:filterset/filters/:filter/enable/',
    ({ params }) => {
      const filtersList = fx.filtersMap[params.filterset] || []
      const filterObj = filtersList.find((f) => f.name === params.filter)
      if (filterObj) {
        filterObj.enabled = true
      }
      return json({ status: 'ok' })
    }
  ),
  http.post(
    '*/account/filtersets/:filterset/filters/:filter/disable/',
    ({ params }) => {
      const filtersList = fx.filtersMap[params.filterset] || []
      const filterObj = filtersList.find((f) => f.name === params.filter)
      if (filterObj) {
        filterObj.enabled = false
      }
      return json({ status: 'ok' })
    }
  ),
  http.post(
    '*/account/filtersets/:filterset/filters/:filter/move_up/',
    ({ params }) => {
      const filtersList = fx.filtersMap[params.filterset] || []
      const idx = filtersList.findIndex((f) => f.name === params.filter)
      if (idx > 0) {
        const temp = filtersList[idx]
        filtersList[idx] = filtersList[idx - 1]
        filtersList[idx - 1] = temp
      }
      return json({ status: 'ok' })
    }
  ),
  http.post(
    '*/account/filtersets/:filterset/filters/:filter/move_down/',
    ({ params }) => {
      const filtersList = fx.filtersMap[params.filterset] || []
      const idx = filtersList.findIndex((f) => f.name === params.filter)
      if (idx !== -1 && idx < filtersList.length - 1) {
        const temp = filtersList[idx]
        filtersList[idx] = filtersList[idx + 1]
        filtersList[idx + 1] = temp
      }
      return json({ status: 'ok' })
    }
  ),

  // ----- calendars & contacts (mocks to avoid console warnings) -----
  http.get('*/user-calendars/', () => json(fx.userCalendars)),
  http.get('*/user-calendars/:id/events/', () => json(fx.events)),
  http.get('*/attendees/', () => json(fx.attendees)),
  http.get('*/categories/', () => json(fx.categories)),
  http.get('*/address-books/default/', () => json(fx.defaultAddressBook)),
  http.get('*/contacts/', () => json(fx.contacts)),

  // ----- catch-all: mantém a app de pé em endpoints não mockados -----
  http.all('*/api/v2/*', ({ request }) => {
    const { pathname } = new URL(request.url)
    console.warn(`[mock] sem fixture: ${request.method} ${pathname}`)
    // Shape paginado vazio do DRF (cobre a maioria das listas).
    return json({ count: 0, next: null, previous: null, results: [] })
  }),
]
