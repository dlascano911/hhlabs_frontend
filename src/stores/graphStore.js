import { create } from 'zustand'
import api from '../api/client'

export const useGraphStore = create((set, get) => ({
  graphs: [],
  currentGraph: null,
  loading: false,
  error: null,

  fetchGraphs: async () => {
    set({ loading: true })
    try {
      const response = await api.get('/api/graphs')
      set({ graphs: response.data, loading: false })
    } catch (error) {
      console.error('Error fetching graphs:', error)
      // For demo, set some mock data
      set({ 
        graphs: [
          { id: '1', name: 'Estrategia DOGE', is_active: true, coins: ['DOGEUSDT'] },
          { id: '2', name: 'BTC Scalping', is_active: false, coins: ['BTCUSDT'] },
        ], 
        loading: false 
      })
    }
  },

  fetchGraph: async (id) => {
    set({ loading: true })
    try {
      const response = await api.get(`/api/graphs/${id}`)
      set({ currentGraph: response.data, loading: false })
    } catch (error) {
      console.error('Error fetching graph:', error)
      set({ loading: false })
    }
  },

  createGraph: async (graphData) => {
    try {
      const response = await api.post('/api/graphs', graphData)
      set(state => ({ 
        graphs: [...state.graphs, response.data],
        currentGraph: response.data 
      }))
      return response.data
    } catch (error) {
      console.error('Error creating graph:', error)
      // For demo, create locally
      const newGraph = { ...graphData, id: Date.now().toString() }
      set(state => ({ 
        graphs: [...state.graphs, newGraph],
        currentGraph: newGraph 
      }))
      return newGraph
    }
  },

  saveGraph: async (id, graphData) => {
    try {
      const response = await api.put(`/api/graphs/${id}`, graphData)
      set(state => ({
        graphs: state.graphs.map(g => g.id === id ? response.data : g),
        currentGraph: response.data
      }))
      return response.data
    } catch (error) {
      console.error('Error saving graph:', error)
      // For demo, save locally
      set(state => ({
        graphs: state.graphs.map(g => g.id === id ? { ...g, ...graphData } : g),
        currentGraph: { ...state.currentGraph, ...graphData }
      }))
    }
  },

  deleteGraph: async (id) => {
    try {
      await api.delete(`/api/graphs/${id}`)
      set(state => ({
        graphs: state.graphs.filter(g => g.id !== id),
        currentGraph: state.currentGraph?.id === id ? null : state.currentGraph
      }))
    } catch (error) {
      console.error('Error deleting graph:', error)
    }
  },

  toggleGraphActive: async (id) => {
    const graph = get().graphs.find(g => g.id === id)
    if (graph) {
      await get().saveGraph(id, { is_active: !graph.is_active })
    }
  },
}))
