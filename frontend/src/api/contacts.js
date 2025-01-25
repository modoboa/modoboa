import repository from './repository'

export default {
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
