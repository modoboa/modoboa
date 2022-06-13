import Vue from 'vue'
import VueRouter from 'vue-router'

import store from '@/store'

import ParametersForm from '@/components/parameters/ParametersForm'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import(/* webpackChunkName: "dashboard" */ '../views/Dashboard.vue'),
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/login',
    name: 'Login',
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "about" */ '../views/Login.vue')
  },
  {
    path: '/twofa',
    name: 'TwoFA',
    component: () => import('../views/TwoFA.vue')
  },
  {
    path: '/domains',
    name: 'DomainList',
    component: () => import('../views/domains/Domains.vue'),
    meta: {
      requiresAuth: true,
      allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins']
    }
  },
  {
    path: '/domains/:id',
    name: 'DomainDetail',
    component: () => import('../views/domains/Domain.vue'),
    meta: {
      requiresAuth: true,
      allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins']
    }
  },
  {
    path: '/domains/:id/edit',
    name: 'DomainEdit',
    component: () => import('../views/domains/DomainEdit.vue'),
    meta: {
      requiresAuth: true,
      allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins']
    }
  },
  {
    path: '/identities',
    name: 'Identities',
    component: () => import('../views/identities/Identities.vue'),
    meta: {
      requiresAuth: true,
      allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins']
    }
  },
  {
    path: '/identities/accounts/:id',
    name: 'AccountDetail',
    component: () => import('../views/identities/Account.vue'),
    meta: {
      requiresAuth: true,
      allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins']
    }
  },
  {
    path: '/identities/accounts/:id/edit',
    name: 'AccountEdit',
    component: () => import('../views/identities/AccountEdit.vue'),
    meta: {
      requiresAuth: true,
      allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins']
    }
  },
  {
    path: '/identities/aliases/:id',
    name: 'AliasDetail',
    component: () => import('../views/identities/Alias.vue'),
    meta: {
      requiresAuth: true,
      allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins']
    }
  },
  {
    path: '/identities/aliases/:id/edit',
    name: 'AliasEdit',
    component: () => import('../views/identities/AliasEdit.vue'),
    meta: {
      requiresAuth: true,
      allowedRoles: ['DomainAdmins', 'Resellers', 'SuperAdmins']
    }
  },
  {
    path: '/parameters/:app',
    name: 'ParametersEdit',
    component: ParametersForm,
    meta: {
      requiresAuth: true,
      allowedRoles: ['SuperAdmins']
    }
  },
  {
    path: '/alarms',
    name: 'Alarms',
    component: () => import('../views/alarms/Alarms.vue'),
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/logs/audit_trail',
    name: 'AuditTrail',
    component: () => import('../views/logs/AuditTrail.vue'),
    meta: {
      requiresAuth: true,
      allowedRoles: ['SuperAdmins']
    }
  },
  {
    path: '/logs/messages',
    name: 'MessageLog',
    component: () => import('../views/logs/Messages.vue'),
    meta: {
      requiresAuth: true,
      allowedRoles: ['DomainAdmins', 'SuperAdmins']
    }
  },
  {
    path: '/user/profile',
    name: 'UserProfile',
    component: () => import('../views/user/Profile.vue'),
    meta: {
      requiresAuth: true,
      layout: 'user'
    }
  },
  {
    path: '/user/security',
    name: 'UserSecurity',
    component: () => import('../views/user/Security.vue'),
    meta: {
      requiresAuth: true,
      layout: 'user'
    }
  },
  {
    path: '/user/forward',
    name: 'UserForward',
    component: () => import('../views/user/Forward.vue'),
    meta: {
      requiresAuth: true,
      layout: 'user'
    }
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

router.beforeEach((to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    store.dispatch('auth/initialize').then(() => {
      if (!store.getters['auth/isAuthenticated']) {
        next({ name: 'Login' })
      } else {
        if (to.meta.allowedRoles !== undefined) {
          if (to.meta.allowedRoles.indexOf(store.getters['auth/authUser'].role) === -1) {
            next({ name: 'Dashboard' })
            return
          }
        }
        next()
      }
    })
  } else {
    next()
  }
})

export default router
