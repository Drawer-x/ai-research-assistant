import axios from 'axios'

const instance = axios.create({
  // Vite 开发环境默认走 /api 代理；部署时可通过 VITE_API_BASE_URL 指向后端。
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
})

// 请求拦截器：自动带上 token
instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：统一处理错误
instance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // token 过期或无效，跳转到登录页
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default instance
