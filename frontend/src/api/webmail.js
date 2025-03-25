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
  getEmailContent(mailbox, mailid) {
    const params = {
      mailbox,
      mailid,
    }
    return repository.get(`/webmail/emails/content/`, { params })
  },
}
