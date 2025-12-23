import React from 'react'

const FundamentalData = ({ data }) => {
  if (!data) return <div className="text-gray-400">Loading...</div>
  
  const fundamentalItems = [
    { label: 'Market Cap', value: `₹${(data.market_cap / 10000000)?.toFixed(2)} Cr` },
    { label: 'P/E Ratio', value: data.pe_ratio?.toFixed(2) },
    { label: 'P/B Ratio', value: data.pb_ratio?.toFixed(2) },
    { label: 'Dividend Yield', value: `${data.dividend_yield?.toFixed(2)}%` },
    { label: 'ROE', value: `${data.roe?.toFixed(2)}%` },
    { label: 'Debt to Equity', value: data.debt_to_equity?.toFixed(2) },
    { label: 'Revenue Growth', value: `${data.revenue_growth?.toFixed(2)}%` },
    { label: 'Profit Growth', value: `${data.profit_growth?.toFixed(2)}%` },
    { label: 'EPS', value: `₹${data.eps?.toFixed(2)}` },
    { label: 'Book Value', value: `₹${data.book_value?.toFixed(2)}` },
  ]
  
  return (
    <div className="space-y-4">
      {/* Company Info */}
      <div className="bg-gray-700 rounded-lg p-4">
        <div className="font-semibold text-lg">{data.company_name}</div>
        <div className="text-gray-400 text-sm">{data.sector}</div>
      </div>
      
      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-3">
        {fundamentalItems.map((item) => (
          <div key={item.label}>
            <div className="text-gray-400 text-sm">{item.label}</div>
            <div className="font-semibold mt-1">{item.value}</div>
          </div>
        ))}
      </div>
      
      {/* Valuation */}
      <div className="bg-gray-700 rounded-lg p-4 mt-4">
        <div className="text-sm text-gray-400 mb-2">Valuation</div>
        <div className="space-y-2">
          {data.pe_ratio < 20 && (
            <div className="text-green-400 text-sm">✓ Attractive P/E ratio</div>
          )}
          {data.roe > 15 && (
            <div className="text-green-400 text-sm">✓ Strong ROE</div>
          )}
          {data.debt_to_equity < 1 && (
            <div className="text-green-400 text-sm">✓ Healthy debt levels</div>
          )}
          {data.dividend_yield > 2 && (
            <div className="text-green-400 text-sm">✓ Good dividend yield</div>
          )}
        </div>
      </div>
    </div>
  )
}

export default FundamentalData
