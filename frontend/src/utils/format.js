export const formatCurrency = (amount) => {
  if (amount === undefined || amount === null) return '₹0'
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount)
}

export const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

export const formatShortDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })
}

export const getCategoryColor = (category) => {
  const colors = {
    'Food & Dining': '#f59e0b', 'Transportation': '#3b82f6', 'Shopping': '#8b5cf6',
    'Entertainment': '#ec4899', 'Bills & Utilities': '#6366f1', 'Health & Medical': '#10b981',
    'Education': '#14b8a6', 'Travel': '#f97316', 'Income': '#34d399', 'Investment': '#a78bfa', 'Other': '#94a3b8',
  }
  return colors[category] || '#94a3b8'
}

export const getCategoryIcon = (category) => {
  const icons = {
    'Food & Dining': '🍽️', 'Transportation': '🚗', 'Shopping': '🛍️', 'Entertainment': '🎭',
    'Bills & Utilities': '⚡', 'Health & Medical': '❤️', 'Education': '📚', 'Travel': '✈️',
    'Income': '💰', 'Investment': '📈', 'Other': '📦',
  }
  return icons[category] || '📦'
}
