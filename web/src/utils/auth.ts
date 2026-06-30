export type AuthUser = {
  id: number
  username: string
  email: string | null
  phone: string | null
}

const TOKEN_KEY = 'surface_access_token'
const USER_KEY = 'surface_user'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function getStoredUser(): AuthUser | null {
  const value = localStorage.getItem(USER_KEY)
  if (!value) {
    return null
  }

  try {
    return JSON.parse(value) as AuthUser
  } catch {
    return null
  }
}

export function setStoredUser(user: AuthUser) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function isAuthenticated() {
  return Boolean(getToken())
}
