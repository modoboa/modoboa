import repository from './repository'

export default {
  getUserMailboxes(mailbox) {
    const params = {}
    if (mailbox) {
      params.mailbox = mailbox
    }
    return repository.get('/webmail/mailboxes/', { params })
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
}
