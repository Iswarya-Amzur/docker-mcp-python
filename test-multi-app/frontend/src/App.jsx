import { useState, useEffect } from 'react'
import axios from 'axios'

function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/data')
        setData(response.data)
      } catch (error) {
        console.error('Error fetching data:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
  }, [])

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Multi-Service Test App</h1>
      <h2>Frontend: React + Vite</h2>
      <h3>Backend Data:</h3>
      {loading ? (
        <p>Loading...</p>
      ) : data ? (
        <div>
          <p><strong>Message:</strong> {data.message}</p>
          <p><strong>Data:</strong> {JSON.stringify(data.data)}</p>
        </div>
      ) : (
        <p>Failed to load data from backend</p>
      )}
    </div>
  )
}

export default App