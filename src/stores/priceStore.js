import { create } from 'zustand'
import api from '../api/client'

export const usePriceStore = create((set, get) => ({
  prices: {},
  ws: null,
  connected: false,
  loading: false,
  error: null,

  // Fetch prices from Coinbase API
  fetchPrices: async () => {
    const symbols = ['BTC-USD', 'ETH-USD', 'DOGE-USD', 'SOL-USD']
    
    set({ loading: true, error: null })
    
    try {
      const pricePromises = symbols.map(async (symbol) => {
        try {
          const response = await api.get(`/api/trading/coinbase/ticker/${symbol}`)
          const data = response.data
          
          // Get the latest trade price
          const trades = data.trades || []
          const latestPrice = trades.length > 0 ? parseFloat(trades[0].price) : 0
          const bestBid = parseFloat(data.best_bid) || latestPrice
          const bestAsk = parseFloat(data.best_ask) || latestPrice
          
          return {
            symbol: symbol.replace('-USD', 'USD'),
            price: latestPrice,
            bid: bestBid,
            ask: bestAsk,
            change: 0, // Will be calculated from previous price
          }
        } catch (err) {
          console.error(`Error fetching ${symbol}:`, err)
          return null
        }
      })
      
      const results = await Promise.all(pricePromises)
      
      set(state => {
        const newPrices = { ...state.prices }
        
        results.forEach(result => {
          if (result) {
            const prevPrice = newPrices[result.symbol]?.price || result.price
            const change = prevPrice > 0 
              ? ((result.price - prevPrice) / prevPrice) * 100 
              : 0
            
            newPrices[result.symbol] = {
              price: result.price,
              bid: result.bid,
              ask: result.ask,
              change: newPrices[result.symbol]?.change !== undefined 
                ? newPrices[result.symbol].change + change 
                : 0,
              lastUpdate: new Date().toISOString(),
            }
          }
        })
        
        return { prices: newPrices, loading: false, connected: true }
      })
    } catch (err) {
      console.error('Error fetching prices:', err)
      set({ error: err.message, loading: false })
    }
  },

  // Start polling for prices
  connectWebSocket: (symbols) => {
    const { fetchPrices } = get()
    
    // Initial fetch
    fetchPrices()
    
    // Poll every 3 seconds
    const interval = setInterval(() => {
      fetchPrices()
    }, 3000)
    
    set({ ws: interval, connected: true })
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
