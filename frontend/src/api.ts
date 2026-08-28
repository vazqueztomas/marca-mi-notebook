import axios from 'axios'
import type { Bid, SpotsResponse } from './types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
})

// Attach admin token as Bearer header (cookies don't cross Vercel origins)
api.interceptors.request.use((config) => {
  if (config.url?.startsWith('/admin')) {
    const token = localStorage.getItem('admin_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const spotsAPI = {
  getSpots: () => api.get<SpotsResponse>('/spots'),
  getBids: (spotId: number) => api.get<{ id: number; bids: Bid[] }>(`/spots/${spotId}/bids`),
  // No explicit Content-Type: axios sets multipart boundary itself for FormData
  createBid: (spotId: number, data: FormData) => api.post(`/spots/${spotId}/bids`, data),
}

export const adminAPI = {
  login: (password: string) => api.post<{ token: string }>('/admin/login', { password }),
  getSpots: () => api.get('/admin/spots'),
  closeSpot: (spotId: number) => api.post(`/admin/spots/${spotId}/close`, {}),
  rejectBid: (bidId: number) => api.post(`/admin/bids/${bidId}/reject`, {}),
}
