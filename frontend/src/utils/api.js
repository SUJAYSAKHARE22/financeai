import axios from 'axios'

const api = axios.create({ baseURL: '/api', headers: { 'Content-Type': 'application/json' } })

export const transactionsAPI = {
  getAll: () => api.get('/transactions/'),
  create: (data) => api.post('/transactions/', data),
  delete: (id) => api.delete(`/transactions/${id}`),
  getMonthlyStats: () => api.get('/transactions/stats/monthly'),
  getTrends: () => api.get('/transactions/stats/trends'),
}

export const budgetsAPI = {
  getAll: () => api.get('/budgets/'),
  create: (data) => api.post('/budgets/', data),
  update: (id, limit) => api.put(`/budgets/${id}?limit=${limit}`),
  delete: (id) => api.delete(`/budgets/${id}`),
}

export const goalsAPI = {
  getAll: () => api.get('/goals/'),
  create: (data) => api.post('/goals/', data),
  updateProgress: (id, amount) => api.put(`/goals/${id}/progress?current_amount=${amount}`),
  delete: (id) => api.delete(`/goals/${id}`),
}

export const dashboardAPI = {
  getSummary: () => api.get('/dashboard/summary'),
}

export const aiAPI = {
  // Streaming chat — returns raw fetch response for SSE
  chatStream: async (message, history, onDelta, onDone) => {
    const resp = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, conversation_history: history })
    })
    if (!resp.ok) throw new Error('AI request failed')
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const json = JSON.parse(line.slice(6))
            if (json.delta) onDelta(json.delta)
            if (json.done) onDone()
          } catch {}
        }
      }
    }
    onDone()
  },
  getInsights: () => api.get('/ai/insights'),
}

export default api
