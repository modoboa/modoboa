import { createPinia } from 'pinia'

export * from './global.store'
export * from './auth.store'
export * from './bus.store'
export * from './layout.store'
export * from './domains.store'
export * from './accounts.store'
export * from './aliases.store'
export * from './identities.store'
export * from './parameters.store'
export * from './providers.store'
export * from './contacts.store'

export default createPinia()
