import repository from './repository'

const resource = 'senderaddresses'

export default {
  getAll () {
    return repository.get(`${resource}/`)
  },
  getAllForMailbox (mailboxId) {
    return repository.get(`${resource}/`, { params: { mailbox: mailboxId } })
  },
  create (data) {
    return repository.post(`${resource}/`, data)
  },
  delete (addressId) {
    return repository.delete(`${resource}/${addressId}/`)
  }
}
