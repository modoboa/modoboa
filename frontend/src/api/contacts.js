import repository from './repository'

export default {
  getDefaultAddressBook() {
    return repository.get('/address-books/default/')
  },
  synchronizeToAddressBook() {
    return repository.get('/address-books/sync_to_cdav/')
  },
  synchronizeFromAddressBook() {
    return repository.get('/address-books/sync_from_cdav/')
  },
  getContacts(params) {
    return repository.get('/contacts/', { params })
  },
  createContact(data) {
    return repository.post('/contacts/', data)
  },
  updateContact(contactId, data) {
    return repository.patch(`/contacts/${contactId}/`, data)
  },
  deleteContact(contactId) {
    return repository.delete(`/contacts/${contactId}/`)
  },
  getCategories() {
    return repository.get('/categories/')
  },
  addCategory(data) {
    return repository.post('/categories/', data)
  },
  updateCategory(categoryId, data) {
    return repository.patch(`/categories/${categoryId}/`, data)
  },
  deleteCategory(categoryId) {
    return repository.delete(`/categories/${categoryId}/`)
  },
}
