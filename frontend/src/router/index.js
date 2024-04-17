// Composables
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores'

const routes = [
  {
    path: '/login',
    component: () => import('@/layouts/default/DefaultLayout.vue'),
    children: [
      {
        path: '',
        name: 'Login',
        component: () => import('@/views/login/LoginView.vue'),
      },
      {
        path: 'twofa',
        name: 'TwoFA',
        component: () => import('@/views/login/TwoFA.vue'),
      },
      {
        path: 'logged',
        name: 'LoginCallback',
        component: () => import('@/views/login/LoginCallbackView.vue'),
      },
      {
        path: 'password_recovery',
        name: 'PasswordRecovery',
        component: () => import('../views/login/PasswordRecoveryView.vue'),
      },
      {
        path: 'password_recovery/confirm/:id?/:token?/',
        name: 'PasswordRecoveryChangeForm',
        component: () =>
          import('../views/login/PasswordRecoveryChangeView.vue'),
      },
      {
        path: 'password_recovery/sms_confirm',
        name: 'PasswordRecoverySms',
        component: () =>
          import('../views/login/PasswordRecoverySmsTotpView.vue'),
      },
    ],
  },
  {
    path: '/admin',
    component: () => import('@/layouts/dashboard/DashboardLayout.vue'),
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: {
          requiresAuth: true,
        },
      },
      {
        path: 'domains',
        component: () => import('@/layouts/default/DefaultLayout.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins'],
        },
        children: [
          {
            path: '',
            name: 'DomainList',
            component: () => import('@/views/admin/domains/DomainsView.vue'),
            meta: {
              requiresAuth: true,
              allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins'],
            },
          },
          {
            path: ':id',
            name: 'DomainDetail',
            meta: {
              requiresAuth: true,
              allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins'],
            },
            component: () => import('@/views/admin/domains/DomainView.vue'),
          },
          {
            path: ':id/edit',
            name: 'DomainEdit',
            meta: {
              requiresAuth: true,
              allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins'],
            },
            component: () => import('@/views/admin/domains/DomainEditView.vue'),
          },
        ],
      },
      {
        path: 'imap_migration',
        component: () => import('@/layouts/default/DefaultLayout.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins'],
        },
        children: [
          {
            path: 'migrations',
            name: 'MigrationsList',
            component: () =>
              import('@/views/admin/imap_migration/MigrationsView.vue'),
            meta: {
              requiresAuth: true,
              allowedRoles: ['Resellers', 'SuperAdmins'],
            },
          },
          {
            path: 'providers',
            component: () => import('@/layouts/default/DefaultLayout.vue'),
            meta: {
              requiresAuth: true,
              allowedRoles: ['Resellers', 'SuperAdmins'],
            },
            children: [
              {
                path: '',
                name: 'ProvidersList',
                component: () =>
                  import('@/views/admin/imap_migration/ProvidersView.vue'),
                meta: {
                  requiresAuth: true,
                  allowedRoles: ['Resellers', 'SuperAdmins'],
                },
              },
              {
                path: 'providers/:id/edit',
                name: 'ProviderEdit',
                component: () =>
                  import('@/views/admin/imap_migration/ProviderEditView.vue'),
                meta: {
                  requiresAuth: true,
                  allowedRoles: ['Resellers', 'SuperAdmins'],
                },
              },
            ],
          },
        ],
      },
      {
        path: 'identities',
        component: () => import('@/layouts/default/DefaultLayout.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins'],
        },
        children: [
          {
            path: '',
            name: 'Identities',
            component: () =>
              import('@/views/admin/identities/IdentitiesView.vue'),
            meta: {
              requiresAuth: true,
              allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins'],
            },
          },
          {
            path: 'accounts/:id',
            name: 'AccountDetail',
            component: () => import('@/views/admin/identities/AccountView.vue'),
            meta: {
              requiresAuth: true,
              allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins'],
            },
          },
          {
            path: 'accounts/:id/edit',
            name: 'AccountEdit',
            component: () =>
              import('@/views/admin/identities/AccountEditView.vue'),
            meta: {
              requiresAuth: true,
              allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins'],
            },
          },
          {
            path: 'aliases/:id',
            name: 'AliasDetail',
            component: () => import('@/views/admin/identities/AliasView.vue'),
            meta: {
              requiresAuth: true,
              allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins'],
            },
          },
          {
            path: 'aliases/:id/edit',
            name: 'AliasEdit',
            component: () =>
              import('@/views/admin/identities/AliasEditView.vue'),
            meta: {
              requiresAuth: true,
              allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins'],
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
          allowedRoles: ['SuperAdmins'],
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
          allowedRoles: ['SuperAdmins'],
        },
      },
      {
        path: 'monitoring/audit_trail',
        name: 'AuditTrail',
        component: () => import('@/views/admin/monitoring/AuditTrailView.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: ['SuperAdmins'],
        },
      },
      {
        path: 'monitoring/messages',
        name: 'MessageLog',
        component: () => import('@/views/admin/monitoring/MessagesView.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: ['DomainAdmins', 'SuperAdmins'],
        },
      },
      {
        path: 'information',
        name: 'Information',
        component: () => import('@/views/admin/InformationView.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: ['SuperAdmins'],
        },
      },
    ],
  },
  {
    path: '/account',
    component: () => import('@/layouts/dashboard/DashboardLayout.vue'),
    meta: {
      layout: 'account',
      requiresAuth: true,
    },
    children: [
      {
        path: 'filters/:filterset?',
        name: 'AccountFilters',
        component: () => import('@/views/account/FiltersView.vue'),
        meta: {
          layout: 'account',
          requiresAuth: true,
          requiresMailbox: true,
        },
      },
      {
        path: ':tab?',
        name: 'AccountSettings',
        component: () => import('@/views/account/SettingsView.vue'),
        meta: {
          layout: 'account',
          requiresAuth: true,
        },
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
  if (to.meta.requiresAuth !== undefined) {
    const previousPage = window.location.href
    sessionStorage.setItem('previousPage', previousPage)
    const authStore = useAuthStore()
    if (!authStore.authUser) {
      await authStore.initialize()
    }
    authStore.validateAccess()
    if (to.meta.allowedRoles !== undefined) {
      if (to.meta.allowedRoles.indexOf(authStore.authUser.role) === -1) {
        next({ name: 'Dashboard' })
        return
      }
    }
    if (to.meta.requiresMailbox && !authStore.authUser.mailbox) {
      next({ name: 'Dashboard' })
    }
  }
  next()
})

export default router
