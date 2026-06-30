import { get, post } from '../utils/request'

export type RegistrationSettingResponse = {
  enabled: boolean
}

export type RegistrationSettingRequest = {
  enabled: boolean
}

export function getRegistrationSetting() {
  return get<RegistrationSettingResponse>('/settings/registration')
}

export function updateRegistrationSetting(request: RegistrationSettingRequest) {
  return post<RegistrationSettingResponse>('/settings/registration', request)
}
