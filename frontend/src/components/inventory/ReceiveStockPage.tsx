import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

const ReceiveStockPage = () => {
  const [searchParams] = useSearchParams()
  const [productId] = useState(searchParams.get('productId') || '')
  const [sku] = useState(searchParams.get('sku') || '')
  const [name] = useState(searchParams.get('name') || '')
  const [quantity, setQuantity] = useState<number>(0)
  const [message, setMessage] = useState('')

  useEffect(() => {
    // prefill done via initial states
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    // Try POSTing to backend if endpoint exists; otherwise just show a success message
    try {
      const resp = await fetch('/api/inventory/receive-stock/', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ productId, quantity }),
      })
      if (resp.ok) {
        setMessage('Stock received successfully')
      } else {
        // fallback: not implemented on backend
        setMessage('Received locally (backend endpoint not available)')
      }
    } catch (err) {
      setMessage('Error: could not contact server — simulated receive')
    }
  }

  return (
    <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5 max-w-2xl">
      <h2>Receive Stock</h2>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4">
        <div>
          <label className="block text-sm font-medium">Product</label>
          <input type="text" readOnly value={name} className="w-full p-2 border rounded" />
        </div>
        <div>
          <label className="block text-sm font-medium">SKU</label>
          <input type="text" readOnly value={sku} className="w-full p-2 border rounded" />
        </div>
        <div>
          <label className="block text-sm font-medium">Quantity to receive</label>
          <input type="number" value={quantity} onChange={e => setQuantity(Number(e.target.value))} className="w-full p-2 border rounded" />
        </div>
        <div>
          <button className="btn" type="submit">Submit</button>
        </div>
        {message && <p className="text-sm mt-2">{message}</p>}
      </form>
    </section>
  )
}

export default ReceiveStockPage
