import { reactive } from 'vue'
import axios from './axios'
import { normalizeCurrentUser, unwrapApiData } from './apiData'

export const authState = reactive({ user: null, loading: false, loaded: false })

export const setAuthFromLogin = response => {
  const data = unwrapApiData(response) || {}
  const token = data.token || data.access_token
  if (token) localStorage.setItem('token', token)
  authState.user = normalizeCurrentUser(data.user || data)
  authState.loaded = true
  return authState.user
}

export const loadCurrentUser = async () => {
  if (!localStorage.getItem('token')) return null
  if (authState.loading || authState.loaded) return authState.user
  authState.loading = true
  try {
    authState.user = normalizeCurrentUser(await axios.get('/api/auth/me'))
    authState.loaded = true
    return authState.user
  } finally {
    authState.loading = false
  }
}

export const clearAuth = () => {
  localStorage.removeItem('token')
  authState.user = null
  authState.loaded = false
}
