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
    },
    {
      path: '/plans',
      name: 'plans',
      component: () => import('../views/PlanListView.vue')
    },
    {
      path: '/plans/:id',
      name: 'planDetail',
      component: () => import('../views/PlanDetailView.vue')
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'notFound',
      component: () => import('../views/NotFoundView.vue')
    }
  ]
})

// ===== 路由守卫 =====
router.beforeEach((to) => {
  const publicPages = ['/login', '/register']
  const token = localStorage.getItem('token')
  if (!publicPages.includes(to.path) && !token) return '/login'
  if (publicPages.includes(to.path) && token) return '/papers'
})

export default router