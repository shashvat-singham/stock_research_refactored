import { useEffect, useRef, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Button } from '@/components/ui/button.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { 
  Activity, 
  ChevronDown, 
  ChevronUp, 
  Trash2,
  Pause,
  Play,
  Wifi,
  WifiOff
} from 'lucide-react'
import { LogEntry } from './LogEntry.jsx'

/**
 * StreamingLogPanel component - displays real-time streaming logs
 */
export function StreamingLogPanel({ logs, isConnected, error, onClear }) {
  const [isExpanded, setIsExpanded] = useState(true)
  const [autoScroll, setAutoScroll] = useState(true)
  const scrollAreaRef = useRef(null)
  const bottomRef = useRef(null)

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, autoScroll])

  // Toggle expanded state
  const toggleExpanded = () => {
    setIsExpanded(!isExpanded)
  }

  // Toggle auto-scroll
  const toggleAutoScroll = () => {
    setAutoScroll(!autoScroll)
  }

  return (
    <Card className="mb-8 border-2 border-blue-200 dark:border-blue-800">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Activity className="h-5 w-5 text-blue-600" />
              Agent Activity Stream
            </CardTitle>
            
            {/* Connection status badge */}
            <Badge 
              variant={isConnected ? "default" : "secondary"}
              className={`flex items-center gap-1 ${
                isConnected 
                  ? 'bg-green-100 text-green-800 border-green-200' 
                  : 'bg-gray-100 text-gray-800 border-gray-200'
              }`}
            >
              {isConnected ? (
                <>
                  <Wifi className="h-3 w-3" />
                  Connected
                </>
              ) : (
                <>
                  <WifiOff className="h-3 w-3" />
                  Disconnected
                </>
              )}
            </Badge>

            {/* Log count badge */}
            {logs.length > 0 && (
              <Badge variant="outline" className="text-xs">
                {logs.length} {logs.length === 1 ? 'event' : 'events'}
              </Badge>
            )}
          </div>

          {/* Controls */}
          <div className="flex items-center gap-2">
            {/* Auto-scroll toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleAutoScroll}
              className="h-8 px-2"
              title={autoScroll ? "Pause auto-scroll" : "Resume auto-scroll"}
            >
              {autoScroll ? (
                <Play className="h-4 w-4" />
              ) : (
                <Pause className="h-4 w-4" />
              )}
            </Button>

            {/* Clear logs */}
            {logs.length > 0 && onClear && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClear}
                className="h-8 px-2"
                title="Clear logs"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}

            {/* Expand/collapse toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleExpanded}
              className="h-8 px-2"
            >
              {isExpanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Error display */}
        {error && (
          <div className="mt-2 text-sm text-red-600 dark:text-red-400">
            Error: {error}
          </div>
        )}
      </CardHeader>

      {/* Log content */}
      {isExpanded && (
        <CardContent className="pt-0">
          <ScrollArea 
            ref={scrollAreaRef}
            className="h-[400px] w-full rounded-md border border-gray-200 dark:border-gray-700 p-4"
          >
            {logs.length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                <div className="text-center">
                  <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Waiting for agent activity...</p>
                  {!isConnected && (
                    <p className="text-xs mt-1">Connecting to stream...</p>
                  )}
                </div>
              </div>
            ) : (
              <div>
                {logs.map((log) => (
                  <LogEntry key={log.id} log={log} />
                ))}
                <div ref={bottomRef} />
              </div>
            )}
          </ScrollArea>

          {/* Footer info */}
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
            Real-time updates powered by WebSocket
          </div>
        </CardContent>
      )}
    </Card>
  )
}
