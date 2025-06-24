import repository from './repository'

export default {
  getUserMailboxes(mailbox) {
    const params = {}
    if (mailbox) {
      params.mailbox = mailbox
    }
    return repository.get('/webmail/mailboxes/', { params })
  },
  getUserMailboxQuota(mailbox) {
    const params = { mailbox }
    return repository.get('/webmail/mailboxes/quota/', { params })
  },
  getUserMailboxUnseen(mailbox) {
    const params = { mailbox }
    return repository.get('webmail/mailboxes/unseen/', { params })
  },
  createUserMailbox(body) {
    return repository.post('/webmail/mailboxes/', body)
  },
  renameUserMailbox(body) {
    return repository.post('/webmail/mailboxes/rename/', body)
  },
  compressUserMailbox(body) {
    return repository.post('/webmail/mailboxes/compress/', body)
  },
  deleteUserMailbox(body) {
    return repository.post('/webmail/mailboxes/delete/', body)
  },
  emptyUserMailbox(mailbox) {
    const body = { name: mailbox }
    return repository.post('/webmail/mailboxes/empty/', body)
  },
  getMailboxEmails(mailbox, options) {
    const params = {
      mailbox,
      ...options,
    }
    return repository.get(`/webmail/emails/`, { params })
  },
  getEmailContent(mailbox, mailid, options) {
    const params = {
      mailbox,
      mailid,
      ...options,
    }
    return repository.get(`/webmail/emails/content/`, { params })
  },
  getEmailSource(mailbox, mailid) {
    const params = {
      mailbox,
      mailid,
    }
    return repository.get(`/webmail/emails/source/`, { params })
  },
  getEmailAttachment(mailbox, mailid, partnum) {
    const params = {
      mailbox,
      mailid,
      partnum,
    }
    return repository.get(`/webmail/emails/attachment/`, {
      params,
      responseType: 'blob',
    })
  },
  deleteSelection(mailbox, selection) {
    const body = {
      mailbox,
      selection,
    }
    return repository.post('/webmail/emails/delete/', body)
  },
  markSelectionAsJunk(mailbox, selection) {
    const body = {
      mailbox,
      selection,
    }
    return repository.post('/webmail/emails/mark_as_junk/', body)
  },
  markSelectionAsNotJunk(mailbox, selection) {
    const body = {
      mailbox,
      selection,
    }
    return repository.post('/webmail/emails/mark_as_not_junk/', body)
  },
  flagSelection(mailbox, selection, status) {
    const body = {
      mailbox,
      selection,
      status,
    }
    return repository.post('/webmail/emails/flag/', body)
  },
  sendEmailFromComposeSession(uid, body) {
    return repository.post(`/webmail/compose-sessions/${uid}/send/`, body)
  },
  getComposeSession(uid) {
    return repository.get(`/webmail/compose-sessions/${uid}/`)
  },
  createComposeSession() {
    return repository.post('/webmail/compose-sessions/')
  },
  getAllowedSenders() {
    return repository.get('/webmail/compose-sessions/allowed_senders/')
  },
  uploadAttachment(sessionUid, body) {
    return repository.post(
      `/webmail/compose-sessions/${sessionUid}/attachments/`,
      body,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    )
  },
  removeAttachment(sessionUid, name) {
    return repository.delete(
      `/webmail/compose-sessions/${sessionUid}/attachments/${name}/`
    )
  },
}
