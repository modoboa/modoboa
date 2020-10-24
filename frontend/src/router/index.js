import Vue from 'vue'
import VueRouter from 'vue-router'

import store from '@/store'

import DomainForm from '@/components/domains/DomainForm'
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
    path: '/domains/',
    name: 'DomainList',
    component: () => import('../views/Domains.vue'),
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/domains/add/',
    name: 'DomainAdd',
    component: DomainForm,
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/domains/:domainPk([0-9]+)/',
    name: 'DomainEdit',
    component: DomainForm,
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
