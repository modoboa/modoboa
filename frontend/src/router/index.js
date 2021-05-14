import Vue from 'vue'
import VueRouter from 'vue-router'

import store from '@/store'

import ParametersForm from '@/components/parameters/ParametersForm'
import LogList from '@/components/logs/LogList'

Vue.use(VueRouter)

const routes = [
  {
    path: '/login',
    name: 'Login',
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "about" */ '../views/Login.vue')
  },
  {
    path: '/domains',
    name: 'DomainList',
    component: () => import('../views/Domains.vue'),
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/domains/:id',
    name: 'DomainDetail',
    component: () => import('../views/Domain.vue'),
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/domains/:id/edit',
    name: 'DomainEdit',
    component: () => import('../views/DomainEdit.vue'),
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/identities',
    name: 'Identities',
    component: () => import('../views/identities/Identities.vue'),
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/identities/accounts/:id/edit',
    name: 'AccountEdit',
    component: () => import('../views/identities/AccountEdit.vue'),
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/identities/aliases/:id/edit',
    name: 'AliasEdit',
    component: () => import('../views/identities/AliasEdit.vue'),
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/parameters/:app',
    name: 'ParametersEdit',
    component: ParametersForm,
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/logs/',
    name: 'LogList',
    component: LogList,
    meta: {
      requiresAuth: true
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
        next('/login/')
      } else {
        next()
      }
    })
  } else {
    next()
  }
})

export default router
