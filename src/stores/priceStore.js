import { create } from 'zustand'

export const usePriceStore = create((set, get) => ({
  prices: {},
  ws: null,
  connected: false,

  connectWebSocket: (symbols) => {
    // For demo, simulate price updates
    const mockPrices = {
      BTCUSDT: { price: 98500, change: 2.35 },
      ETHUSDT: { price: 3450, change: 1.82 },
      DOGEUSDT: { price: 0.32, change: -1.24 },
      SOLUSDT: { price: 185, change: 4.56 },
    }
    
    set({ prices: mockPrices, connected: true })

    // Simulate real-time updates
    const interval = setInterval(() => {
      set(state => {
        const newPrices = { ...state.prices }
        Object.keys(newPrices).forEach(symbol => {
          const change = (Math.random() - 0.5) * 0.1
          newPrices[symbol] = {
            ...newPrices[symbol],
            price: newPrices[symbol].price * (1 + change / 100),
            change: newPrices[symbol].change + (Math.random() - 0.5) * 0.1,
          }
        })
        return { prices: newPrices }
      })
    }, 2000)

    // Store interval id for cleanup
    set({ ws: interval })

    // Real WebSocket implementation would be:
    // const streams = symbols.map(s => `${s.toLowerCase()}@ticker`).join('/')
    // const ws = new WebSocket(`wss://stream.binance.com:9443/ws/${streams}`)
    // ws.onmessage = (event) => {
    //   const data = JSON.parse(event.data)
    //   set(state => ({
    //     prices: {
    //       ...state.prices,
    //       [data.s]: { price: parseFloat(data.c), change: parseFloat(data.P) }
    //     }
    //   }))
    // }
  },

  disconnectWebSocket: () => {
    const { ws } = get()
    if (ws) {
      clearInterval(ws)
      set({ ws: null, connected: false })
    }
  },

  updatePrice: (symbol, price, change) => {
    set(state => ({
      prices: {
        ...state.prices,
        [symbol]: { price, change }
      }
    }))
  },
}))
