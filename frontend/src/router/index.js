import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue')
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue')
    },
    {
      path: '/papers',
      name: 'papers',
      component: () => import('../views/PapersView.vue')
    },
    {
      path: '/papers/:id',
      name: 'paperDetail',
      component: () => import('../views/PaperDetailView.vue')
    },
    {
      path: '/graph',
      name: 'graph',
      component: () => import('../views/GraphView.vue')
    },
    {
      path: '/agent',
      name: 'agent',
      component: () => import('../views/AgentView.vue')
    },
    {
      path: '/review',
      name: 'review',
      component: () => import('../views/ReviewView.vue')
    }
  ]
})

export default router