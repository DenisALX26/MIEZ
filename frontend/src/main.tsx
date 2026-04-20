import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster, toast } from 'react-hot-toast'
import './index.css'
import App from './App.tsx'

const extractErrorMessage = (error: unknown): string => {
  if (error instanceof Error && error.message) {
    return error.message
  }

  return 'Something went wrong. Please try again.'
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
    },
    mutations: {
      onError: (error: unknown) => {
        toast.error(extractErrorMessage(error))
      },
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <Toaster position="top-right" />
    </QueryClientProvider>
  </StrictMode>,
)
