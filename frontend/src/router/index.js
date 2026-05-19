import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore, useGlobalStore, usePluginsStore } from '@/stores'
import { useGlobalConfig } from '@/main'
import constants from '@/constants.json'
import { registerRemote, loadRemoteComponent } from '@/utils/federation'

function buildPluginRoute(routeDef, remoteName) {
  const route = { ...routeDef }
  delete route.parent
  delete route.remote
  if (typeof route.component === 'string' && route.component) {
    if (!remoteName) {
      throw new Error(
        `Plugin route "${route.name}" declares a component but its plugin has no remote`
      )
    }
    route.component = loadRemoteComponent(remoteName, route.component)
  }
  if (Array.isArray(route.children)) {
    route.children = route.children.map((child) =>
      buildPluginRoute(child, remoteName)
    )
  }
  return route
}

let pluginRoutesRegistered = false

async function ensurePluginRoutes(router) {
  if (pluginRoutesRegistered) {
    return
  }
  pluginRoutesRegistered = true
  const pluginsStore = usePluginsStore()
  try {
    await pluginsStore.fetchManifests()
  } catch (err) {
    pluginRoutesRegistered = false
    throw err
  }
  for (const manifest of pluginsStore.manifests) {
    const remoteOk = registerRemote(manifest.remote)
    for (const routeDef of manifest.routes || []) {
      try {
        const route = buildPluginRoute(
          routeDef,
          remoteOk ? manifest.remote.name : null
        )
        if (routeDef.parent) {
          router.addRoute(routeDef.parent, route)
        } else {
          router.addRoute(route)
        }
      } catch (err) {
        console.error(
          `Failed to register plugin route "${routeDef.name}" of ${manifest.name}`,
          err
        )
      }
    }
  }
}

const routes = [
  {
    path: '/login',
    component: () => import('@/layouts/empty/EmptyLayout.vue'),
    children: [
      {
        path: '',
        name: 'Login',
        component: () => import('@/views/login/LoginView.vue'),
      },
      {
        path: 'logged',
        name: 'LoginCallback',
        component: () => import('@/views/login/LoginCallbackView.vue'),
        props: {
          redirectUrl: '/admin',
        },
      },
    ],
  },
  {
    path: '/admin',
    name: 'AdminLayout',
    component: () => import('@/layouts/admin/AdminLayout.vue'),
    meta: {
      allowedRoles: [
        constants.DOMAIN_ADMIN,
        constants.RESELLER,
        constants.SUPER_ADMIN,
      ],
    },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: {
          requiresAuth: true,
        },
      },
      {
        path: 'domains',
        component: () => import('@/layouts/empty/EmptyLayout.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: [
            constants.DOMAIN_ADMIN,
            constants.RESELLER,
            constants.SUPER_ADMIN,
          ],
        },
        children: [
          {
            path: '',
            name: 'DomainList',
            component: () => import('@/views/admin/domains/DomainsView.vue'),
            meta: {
              requiresAuth: true,
              allowedRoles: [
                constants.DOMAIN_ADMIN,
                constants.RESELLER,
                constants.SUPER_ADMIN,
              ],
            },
          },
          {
            path: ':id',
            name: 'DomainDetail',
            meta: {
              requiresAuth: true,
              allowedRoles: [
                constants.DOMAIN_ADMIN,
                constants.RESELLER,
                constants.SUPER_ADMIN,
              ],
            },
            component: () => import('@/views/admin/domains/DomainView.vue'),
          },
          {
            path: ':id/edit',
            name: 'DomainEdit',
            meta: {
              requiresAuth: true,
              allowedRoles: [
                constants.DOMAIN_ADMIN,
                constants.RESELLER,
                constants.SUPER_ADMIN,
              ],
            },
            component: () => import('@/views/admin/domains/DomainEditView.vue'),
          },
        ],
      },
      {
        path: 'imap_migration',
        component: () => import('@/layouts/empty/EmptyLayout.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: [
            constants.DOMAIN_ADMIN,
            constants.RESELLER,
            constants.SUPER_ADMIN,
          ],
        },
        children: [
          {
            path: 'migrations',
            name: 'MigrationsList',
            component: () =>
              import('@/views/admin/imap_migration/MigrationsView.vue'),
            meta: {
              requiresAuth: true,
              allowedRoles: [constants.RESELLER, constants.SUPER_ADMIN],
            },
          },
          {
            path: 'providers',
            component: () => import('@/layouts/empty/EmptyLayout.vue'),
            meta: {
              requiresAuth: true,
              allowedRoles: [constants.RESELLER, constants.SUPER_ADMIN],
            },
            children: [
              {
                path: '',
                name: 'ProvidersList',
                component: () =>
                  import('@/views/admin/imap_migration/ProvidersView.vue'),
                meta: {
                  requiresAuth: true,
                  allowedRoles: [constants.RESELLER, constants.SUPER_ADMIN],
                },
              },
              {
                path: 'providers/:id/edit',
                name: 'ProviderEdit',
                component: () =>
                  import('@/views/admin/imap_migration/ProviderEditView.vue'),
                meta: {
                  requiresAuth: true,
                  allowedRoles: [constants.RESELLER, constants.SUPER_ADMIN],
                },
              },
            ],
          },
        ],
      },
      {
        path: 'identities',
        component: () => import('@/layouts/empty/EmptyLayout.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: [
            constants.DOMAIN_ADMIN,
            constants.RESELLER,
            constants.SUPER_ADMIN,
          ],
        },
        children: [
          {
            path: '',
            name: 'Identities',
            component: () =>
              import('@/views/admin/identities/IdentitiesView.vue'),
            meta: {
              requiresAuth: true,
              allowedRoles: [
                constants.DOMAIN_ADMIN,
                constants.RESELLER,
                constants.SUPER_ADMIN,
              ],
            },
          },
          {
            path: 'accounts/:id',
            name: 'AccountDetail',
            component: () => import('@/views/admin/identities/AccountView.vue'),
            meta: {
              requiresAuth: true,
              allowedRoles: [
                constants.DOMAIN_ADMIN,
                constants.RESELLER,
                constants.SUPER_ADMIN,
              ],
            },
          },
          {
            path: 'accounts/:id/edit',
            name: 'AccountEdit',
            component: () =>
              import('@/views/admin/identities/AccountEditView.vue'),
            meta: {
              requiresAuth: true,
              allowedRoles: [
                constants.DOMAIN_ADMIN,
                constants.RESELLER,
                constants.SUPER_ADMIN,
              ],
            },
          },
          {
            path: 'aliases/:id',
            name: 'AliasDetail',
            component: () => import('@/views/admin/identities/AliasView.vue'),
            meta: {
              requiresAuth: true,
              allowedRoles: [
                constants.DOMAIN_ADMIN,
                constants.RESELLER,
                constants.SUPER_ADMIN,
              ],
            },
          },
          {
            path: 'aliases/:id/edit',
            name: 'AliasEdit',
            component: () =>
              import('@/views/admin/identities/AliasEditView.vue'),
            meta: {
              requiresAuth: true,
              allowedRoles: [
                constants.DOMAIN_ADMIN,
                constants.RESELLER,
                constants.SUPER_ADMIN,
              ],
            },
          },
        ],
      },
      {
        path: 'parameters/:app',
        name: 'ParametersEdit',
        component: () => import('@/views/admin/ParametersView.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: [constants.SUPER_ADMIN],
        },
      },
      {
        path: 'alarms',
        name: 'Alarms',
        component: () => import('@/views/admin/alarms/AlarmsView.vue'),
        meta: {
          requiresAuth: true,
        },
      },
      {
        path: 'monitoring/statistics',
        name: 'Statistics',
        component: () => import('@/views/admin/monitoring/StatisticsView.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: [constants.SUPER_ADMIN],
        },
      },
      {
        path: 'monitoring/audit_trail',
        name: 'AuditTrail',
        component: () => import('@/views/admin/monitoring/AuditTrailView.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: [constants.SUPER_ADMIN],
        },
      },
      {
        path: 'monitoring/messages',
        name: 'MessageLog',
        component: () => import('@/views/admin/monitoring/MessagesView.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: [
            constants.DOMAIN_ADMIN,
            constants.RESELLER,
            constants.SUPER_ADMIN,
          ],
        },
      },
      {
        path: 'information',
        name: 'Information',
        component: () => import('@/views/admin/InformationView.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: [constants.SUPER_ADMIN],
        },
      },
    ],
  },
  {
    path: '/account',
    component: () => import('@/layouts/account/AccountLayout.vue'),
    meta: {
      requiresAuth: true,
    },
    children: [
      {
        path: 'filters/:filterset?',
        name: 'AccountFilters',
        component: () => import('@/views/account/FiltersView.vue'),
        meta: {
          requiresAuth: true,
          requiresMailbox: true,
        },
      },
      {
        path: 'parameters/:app',
        name: 'AccountParametersEdit',
        component: () => import('@/views/account/ParametersView.vue'),
        meta: {
          requiresAuth: true,
        },
      },
      {
        path: ':tab?',
        name: 'AccountSettings',
        component: () => import('@/views/account/SettingsView.vue'),
        meta: {
          requiresAuth: true,
        },
      },
    ],
  },
  {
    path: '/user',
    meta: {
      requiresAuth: true,
    },
    children: [
      {
        path: '',
        name: 'UserDashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: {
          requiresAuth: true,
        },
      },
      {
        path: 'contacts',
        component: () => import('@/layouts/user/UserLayout.vue'),
        meta: {
          requiresAuth: true,
          requiresMailbox: true,
        },
        children: [
          {
            path: ':category?',
            name: 'ContactList',
            component: () => import('@/views/contacts/AddressBook.vue'),
            meta: {
              requiresAuth: true,
            },
          },
        ],
      },
      {
        path: 'calendars',
        component: () => import('@/layouts/user/UserLayout.vue'),
        meta: {
          requiresAuth: true,
          requiresMailbox: true,
        },
        children: [
          {
            path: '',
            name: 'CalendarView',
            component: () => import('@/views/calendars/CalendarView.vue'),
            meta: {
              requiresAuth: true,
              requiresMailbox: true,
            },
          },
        ],
      },
      {
        path: 'webmail',
        component: () => import('@/layouts/webmail/WebmailLayout.vue'),
        meta: {
          requiresAuth: true,
          requiresMailbox: true,
        },
        children: [
          {
            path: '',
            name: 'MailboxView',
            component: () => import('@/views/webmail/MailboxView.vue'),
            meta: {
              requiresAuth: true,
              requiresMailbox: true,
            },
          },
          {
            path: 'view',
            name: 'EmailView',
            component: () => import('@/views/webmail/EmailView.vue'),
            meta: {
              requiresAuth: true,
              requiresMailbox: true,
            },
          },
          {
            path: 'compose',
            name: 'ComposeEmailView',
            component: () => import('@/views/webmail/ComposeEmailView.vue'),
            meta: {
              requiresAuth: true,
              requiresMailbox: true,
            },
          },
          {
            path: 'reply',
            name: 'ReplyEmailView',
            component: () => import('@/views/webmail/ReplyEmailView.vue'),
            meta: {
              requiresAuth: true,
              requiresMailbox: true,
            },
          },
          {
            path: 'forward',
            name: 'ForwardEmailView',
            component: () => import('@/views/webmail/ForwardEmailView.vue'),
            meta: {
              requiresAuth: true,
              requiresMailbox: true,
            },
          },
        ],
      },
      {
        path: 'quarantine',
        component: () => import('@/layouts/quarantine/QuarantineLayout.vue'),
        meta: {
          requiresAuth: true,
        },
        children: [
          {
            path: '',
            name: 'QuarantineView',
            component: () => import('@/views/quarantine/QuarantineView.vue'),
            meta: {
              requiresAuth: true,
            },
          },
          {
            path: ':mailid/:rcpt',
            name: 'QuarantineMessageView',
            component: () => import('@/views/quarantine/MessageView.vue'),
            meta: {
              requiresAuth: true,
            },
          },
        ],
      },
      {
        path: 'selfquarantine',
        component: () => import('@/layouts/quarantine/SelfServiceLayout.vue'),
        props: { loadTheme: false },
        meta: {
          requiresAuth: false,
        },
        children: [
          {
            path: ':mailid/:rcpt',
            name: 'SelfQuarantineMessageView',
            component: () => import('@/views/quarantine/MessageView.vue'),
          },
        ],
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: { name: 'Dashboard', params: {} },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const config = useGlobalConfig()

  document.title = config.HTML_PAGE_TITLE
    ? config.HTML_PAGE_TITLE
    : 'Welcome to Modoboa'
  if (to.meta?.requiresAuth === true) {
    const previousPage = window.location.href
    sessionStorage.setItem('previousPage', previousPage)
    const authStore = useAuthStore()
    const globalStore = useGlobalStore()
    const isAuth = await authStore.validateAccess()
    if (isAuth) {
      const justRegistered = !pluginRoutesRegistered
      if (!pluginRoutesRegistered) {
        try {
          await ensurePluginRoutes(router)
        } catch (err) {
          console.error('Failed to load plugin routes', err)
        }
      }
      if (justRegistered) {
        const resolved = router.resolve(to.fullPath)
        if (
          resolved.matched.length &&
          resolved.matched[0].path !== to.matched[0]?.path
        ) {
          next({ ...resolved, replace: true })
          return
        }
      }
      if (to.meta.allowedRoles !== undefined) {
        if (to.meta.allowedRoles.indexOf(authStore.authUser.role) === -1) {
          await globalStore.fetchAvailableApplications()
          const nextPage = globalStore.webmailEnabled
            ? 'MailboxView'
            : 'AccountSettings'
          next({ name: nextPage })
          return
        }
      }
      if (to.meta.requiresMailbox && !authStore.authUser.mailbox) {
        next({ name: 'Dashboard' })
        return
      }
    } else {
      next({ name: 'Login' })
      return
    }
  }
  next()
})

export default router
