import { get, post } from '../utils/request'
import type { AuthUser } from '../utils/auth'

export type RegisterStatusResponse = {
  enabled: boolean
}

export type RegisterRequest = {
  username: string
  email?: string
  phone?: string
  password: string
}

export type LoginRequest = {
  account: string
  password: string
}

export type LoginResponse = {
  access_token: string
  token_type: 'bearer'
  user: AuthUser
}

export function getRegisterStatus() {
  return get<RegisterStatusResponse>('/user/register-status')
}

export function registerUser(request: RegisterRequest) {
  return post<AuthUser>('/user/register', request)
}

export function loginUser(request: LoginRequest) {
  return post<LoginResponse>('/user/login', request)
}

export function getCurrentUser() {
  return get<AuthUser>('/user/me')
}
