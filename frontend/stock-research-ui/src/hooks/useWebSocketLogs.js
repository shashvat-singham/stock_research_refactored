import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * Custom hook for managing WebSocket connection and receiving streaming logs
 * @param {string} requestId - The request ID to connect to
 * @param {boolean} enabled - Whether to enable the WebSocket connection
 * @returns {object} - { logs, isConnected, error, clearLogs }
 */
export function useWebSocketLogs(requestId, enabled = true) {
  const [logs, setLogs] = useState([])
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState(null)
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const reconnectAttemptsRef = useRef(0)
  const maxReconnectAttempts = 5

  const clearLogs = useCallback(() => {
    setLogs([])
  }, [])

  const connect = useCallback(() => {
    if (!requestId || !enabled) return

    try {
      // Close existing connection if any
      if (wsRef.current) {
        wsRef.current.close()
      }

      // Create WebSocket connection
      const wsUrl = `ws://localhost:8000/ws/${requestId}`
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('WebSocket connected:', requestId)
        setIsConnected(true)
        setError(null)
        reconnectAttemptsRef.current = 0
      }

      ws.onmessage = (event) => {
        try {
          const logEvent = JSON.parse(event.data)
          
          // Add unique ID for React key
          const logWithId = {
            ...logEvent,
            id: `${Date.now()}-${Math.random()}`
          }

          setLogs((prevLogs) => [...prevLogs, logWithId])
        } catch (err) {
          console.error('Error parsing log message:', err)
        }
      }

      ws.onerror = (event) => {
        console.error('WebSocket error:', event)
        setError('WebSocket connection error')
      }

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason)
        setIsConnected(false)

        // Attempt to reconnect if not a normal closure
        if (
          event.code !== 1000 && 
          reconnectAttemptsRef.current < maxReconnectAttempts &&
          enabled
        ) {
          reconnectAttemptsRef.current += 1
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000)
          
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, delay)
        }
      }

      wsRef.current = ws
    } catch (err) {
      console.error('Error creating WebSocket:', err)
      setError(err.message)
    }
  }, [requestId, enabled])

  useEffect(() => {
    if (enabled && requestId) {
      connect()
    }

    // Cleanup on unmount or when requestId changes
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [requestId, enabled, connect])

  return {
    logs,
    isConnected,
    error,
    clearLogs
  }
}
