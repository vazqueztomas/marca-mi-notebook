import axios from 'axios'
import type { Bid, SpotsResponse } from './types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
})

export const spotsAPI = {
  getSpots: () => api.get<SpotsResponse>('/spots'),
  getBids: (spotId: number) => api.get<{ id: number; bids: Bid[] }>(`/spots/${spotId}/bids`),
  // No explicit Content-Type: axios sets multipart boundary itself for FormData
  createBid: (spotId: number, data: FormData) => api.post(`/spots/${spotId}/bids`, data),
}

export const adminAPI = {
  login: async (password: string) => {
    const res = await api.post<{ token: string }>('/admin/login', { password })
    // Backend reads the token from a session_token cookie on admin routes
    document.cookie = `session_token=${res.data.token}; path=/; max-age=${24 * 60 * 60}; samesite=lax`
    return res
  },
  getSpots: () => api.get('/admin/spots'),
  closeSpot: (spotId: number) => api.post(`/admin/spots/${spotId}/close`, {}),
  rejectBid: (bidId: number) => api.post(`/admin/bids/${bidId}/reject`, {}),
}
