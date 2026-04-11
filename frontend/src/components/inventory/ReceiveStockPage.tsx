import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

const ReceiveStockPage = () => {
  const [searchParams] = useSearchParams()
  const [productId] = useState(searchParams.get('productId') || '')
  const [sku] = useState(searchParams.get('sku') || '')
  const [name] = useState(searchParams.get('name') || '')
  const [quantity, setQuantity] = useState<number>(0)
  const [message, setMessage] = useState('')
  const [suppliers, setSuppliers] = useState<Array<{ id: number; name: string }>>([])
  const [supplierId, setSupplierId] = useState<string>('')

  useEffect(() => {
    // prefill done via initial states
    const fetchSuppliers = async () => {
      try {
        const res = await fetch('/api/inventory/suppliers/', { credentials: 'include' })
        if (!res.ok) return
        const data = await res.json()
        setSuppliers(data)
        if (data && data.length > 0) {
          setSupplierId(String(data[0].id))
        }
      } catch (err) {
        // ignore
      }
    }
    fetchSuppliers()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    // POST to backend stock-movements endpoint (movement_type = IN)
    if (!productId) {
      setMessage('Product not selected — please open Receive from a product or low-stock row.')
      return
    }

    const payload: any = {
      product: Number(productId),
      movement_type: 'INBOUND',
      quantity,
      supplier: supplierId ? Number(supplierId) : null,
    }

    try {
      const resp = await fetch('/api/inventory/stock-movements/', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (resp.ok) {
        setMessage('Stock received successfully')
        // navigate back to movements list to see the new movement
        setTimeout(() => {
          window.location.href = '/inventory/stock-movements'
        }, 800)
      } else {
        const text = await resp.text()
        setMessage(`Server error: ${resp.status} ${text}`)
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
          <label className="block text-sm font-medium">Supplier</label>
          <select value={supplierId} onChange={e => setSupplierId(e.target.value)} className="w-full p-2 border rounded">
            <option value="">Select supplier</option>
            {suppliers.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
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
