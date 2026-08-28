import axios from 'axios'
import type { Bid, SpotsResponse } from './types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
})

export const spotsAPI = {
  getSpots: () => api.get<SpotsResponse>('/spots'),
  getBids: (spotId: number) => api.get<{ id: number; bids: Bid[] }>(`/spots/${spotId}/bids`),
  createBid: (spotId: number, data: FormData) =>
    api.post(`/spots/${spotId}/bids`, data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

export const adminAPI = {
  login: (password: string) => api.post<{ token: string }>('/admin/login', { password }),
  getSpots: () => api.get('/admin/spots'),
  closSpot: (spotId: number) => api.post(`/admin/spots/${spotId}/close`, {}),
  rejectBid: (bidId: number) => api.post(`/admin/bids/${bidId}/reject`, {}),
}
