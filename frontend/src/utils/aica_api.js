/**
 * AI_CA API client additions.
 * ADD these exports to your existing src/utils/api.js — do not replace the file.
 * Copy-paste the aicaAPI object into your existing api.js.
 */

import axios from 'axios'
const api = axios.create({ baseURL: '/api', headers: { 'Content-Type': 'application/json' } })

export const aicaAPI = {
  // Overview dashboard data
  getOverview: (regime = 'new') =>
    api.get(`/ai-ca/overview?regime=${regime}`),

  // Classify transactions
  classify: (transactionIds = null, useAi = true) =>
    api.post('/ai-ca/classify', { transaction_ids: transactionIds, use_ai: useAi }),

  // Tax summary computation
  getTaxSummary: (regime = 'new', financialYear = '2024-25', existingTds = 0) =>
    api.get(`/ai-ca/tax-summary?regime=${regime}&financial_year=${financialYear}&existing_tds=${existingTds}`),

  // Financial statements (P&L, Cash Flow, Expense)
  getFinancialStatements: (params = {}) => {
    const query = new URLSearchParams(params).toString()
    return api.get(`/ai-ca/financial-statements?${query}`)
  },

  // Ledger entries
  getLedger: () => api.get('/ai-ca/ledger'),

  // Generate reports
  generateReport: (data) => api.post('/ai-ca/reports', data),

  // Download PDF
  downloadPdf: async (reportType = 'full', period = 'monthly', taxRegime = 'new', financialYear = '2024-25', year = null) => {
    const resp = await api.post('/ai-ca/reports', {
      report_type: reportType,
      period,
      year,
      format: 'pdf',
      tax_regime: taxRegime,
      financial_year: financialYear,
    }, { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `financeai_report_${new Date().toISOString().split('T')[0]}.pdf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  },

  // Download Excel
  downloadExcel: async (reportType = 'full', period = 'monthly', taxRegime = 'new', financialYear = '2024-25') => {
    const resp = await api.post('/ai-ca/reports', {
      report_type: reportType,
      period,
      format: 'excel',
      tax_regime: taxRegime,
      financial_year: financialYear,
    }, { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([resp.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = `financeai_report_${new Date().toISOString().split('T')[0]}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  },

  // AI-CA Chat
  chat: (message, history = [], includeTaxContext = true) =>
    api.post('/ai-ca/chat', {
      message,
      conversation_history: history,
      include_tax_context: includeTaxContext,
    }),

  // Get Taxpayer Profile
  getProfile: () => api.get('/ai-ca/profile'),

  // Save Taxpayer Profile
  saveProfile: (profile) => api.post('/ai-ca/profile', profile),

  // Download ITR JSON
  downloadITRJson: async (profile, taxRegime = 'new', financialYear = '2024-25') => {
    const resp = await api.post('/ai-ca/itr/json', {
      profile,
      tax_regime: taxRegime,
      financial_year: financialYear
    })
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(resp.data, null, 2))
    const a = document.createElement('a')
    a.href = dataStr
    a.download = `itr1_sahaj_${profile.pan}_${financialYear}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  },

  // Download ITR PDF Form
  downloadITRPdf: async (profile, taxRegime = 'new', financialYear = '2024-25') => {
    const resp = await api.post('/ai-ca/itr/pdf', {
      profile,
      tax_regime: taxRegime,
      financial_year: financialYear
    }, { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `itr1_sahaj_${profile.pan}_${financialYear}.pdf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  },

  // Download Form 16 Summary
  downloadForm16: async (profile, taxRegime = 'new', financialYear = '2024-25') => {
    const resp = await api.post('/ai-ca/document/form16', {
      profile,
      tax_regime: taxRegime,
      financial_year: financialYear
    }, { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `form16_${profile.pan}_${financialYear}.pdf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  },

  // Download Form 26AS Statement
  downloadForm26as: async (profile, taxRegime = 'new', financialYear = '2024-25') => {
    const resp = await api.post('/ai-ca/document/form26as', {
      profile,
      tax_regime: taxRegime,
      financial_year: financialYear
    }, { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `form26as_${profile.pan}_${financialYear}.pdf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  },
}

export default api
