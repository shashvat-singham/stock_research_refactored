import { 
  Brain, 
  FileText, 
  Newspaper, 
  TrendingUp, 
  Lightbulb,
  BarChart3,
  Search,
  Database,
  AlertCircle,
  Info,
  CheckCircle,
  Loader2
} from 'lucide-react'
import { Badge } from '@/components/ui/badge.jsx'

/**
 * Get icon for log event type
 */
function getLogIcon(type, agent) {
  switch (type) {
    case 'agent_start':
      return <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
    case 'agent_complete':
      return <CheckCircle className="h-4 w-4 text-green-600" />
    case 'agent_progress':
      return <Loader2 className="h-4 w-4 animate-spin text-purple-600" />
    case 'tool_call':
      return <FileText className="h-4 w-4 text-orange-600" />
    case 'search_query':
      return <Search className="h-4 w-4 text-indigo-600" />
    case 'data_fetch':
      return <Database className="h-4 w-4 text-cyan-600" />
    case 'analysis':
      return <BarChart3 className="h-4 w-4 text-purple-600" />
    case 'thinking':
      return <Brain className="h-4 w-4 text-pink-600" />
    case 'error':
      return <AlertCircle className="h-4 w-4 text-red-600" />
    case 'info':
      return <Info className="h-4 w-4 text-gray-600" />
    default:
      return <Info className="h-4 w-4 text-gray-600" />
  }
}

/**
 * Get agent-specific icon
 */
function getAgentIcon(agent) {
  switch (agent) {
    case 'news':
      return <Newspaper className="h-3 w-3" />
    case 'price':
      return <TrendingUp className="h-3 w-3" />
    case 'synthesis':
      return <Brain className="h-3 w-3" />
    case 'orchestrator':
      return <BarChart3 className="h-3 w-3" />
    default:
      return null
  }
}

/**
 * Get color class for log type
 */
function getLogColor(type) {
  switch (type) {
    case 'agent_start':
      return 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/10'
    case 'agent_complete':
      return 'border-l-green-500 bg-green-50 dark:bg-green-900/10'
    case 'agent_progress':
      return 'border-l-purple-500 bg-purple-50 dark:bg-purple-900/10'
    case 'tool_call':
      return 'border-l-orange-500 bg-orange-50 dark:bg-orange-900/10'
    case 'search_query':
      return 'border-l-indigo-500 bg-indigo-50 dark:bg-indigo-900/10'
    case 'data_fetch':
      return 'border-l-cyan-500 bg-cyan-50 dark:bg-cyan-900/10'
    case 'analysis':
      return 'border-l-purple-500 bg-purple-50 dark:bg-purple-900/10'
    case 'thinking':
      return 'border-l-pink-500 bg-pink-50 dark:bg-pink-900/10'
    case 'error':
      return 'border-l-red-500 bg-red-50 dark:bg-red-900/10'
    case 'info':
      return 'border-l-gray-500 bg-gray-50 dark:bg-gray-900/10'
    default:
      return 'border-l-gray-500 bg-gray-50 dark:bg-gray-900/10'
  }
}

/**
 * Format timestamp to readable time
 */
function formatTime(timestamp) {
  try {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: false
    })
  } catch {
    return ''
  }
}

/**
 * LogEntry component - displays a single log entry
 */
export function LogEntry({ log }) {
  const { type, timestamp, message, agent, details } = log

  return (
    <div 
      className={`
        border-l-4 rounded-r-lg p-3 mb-2 
        transition-all duration-300 ease-in-out
        hover:shadow-md
        ${getLogColor(type)}
      `}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="flex-shrink-0 mt-0.5">
          {getLogIcon(type, agent)}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            {/* Agent badge */}
            {agent && (
              <Badge 
                variant="outline" 
                className="text-xs flex items-center gap-1 capitalize"
              >
                {getAgentIcon(agent)}
                {agent}
              </Badge>
            )}

            {/* Timestamp */}
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {formatTime(timestamp)}
            </span>
          </div>

          {/* Message */}
          <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed">
            {message}
          </p>

          {/* Details (if any) */}
          {details && Object.keys(details).length > 0 && (
            <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
              {details.ticker && (
                <span className="font-mono font-semibold">{details.ticker}</span>
              )}
              {details.progress !== undefined && (
                <span className="ml-2">Progress: {details.progress}%</span>
              )}
              {details.tool && (
                <span className="ml-2">Tool: {details.tool}</span>
              )}
              {details.query && (
                <span className="ml-2 italic">"{details.query}"</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
