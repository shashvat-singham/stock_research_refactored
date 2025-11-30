import { useState, useEffect, useMemo } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { 
  Search, 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  Brain, 
  FileText, 
  Newspaper, 
  Building, 
  Users, 
  Lightbulb,
  BarChart3,
  Clock,
  ExternalLink,
  AlertCircle,
  CheckCircle,
  Loader2,
  HelpCircle,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react'
import './App.css'
import { useWebSocketLogs } from './hooks/useWebSocketLogs.js'
import { StreamingLogPanel } from './components/StreamingLogPanel.jsx'

const API_BASE_URL = 'http://localhost:8000/api/v1'

// New Confirmation Dialog Component
function ConfirmationDialog({ prompt, onConfirm, onReject }) {
  return (
    <Card className="mb-8 border-2 border-blue-300 bg-blue-50 dark:bg-blue-900/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-blue-900 dark:text-blue-100">
          <HelpCircle className="h-5 w-5" />
          Confirmation Needed
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert className="border-blue-200 bg-white dark:bg-gray-800">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Did you mean this?</AlertTitle>
          <AlertDescription className="mt-2 text-base">
            {prompt.message}
          </AlertDescription>
        </Alert>

        {prompt.suggestion && (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 space-y-2">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-600 dark:text-gray-400">Original Input:</span>
                <p className="text-gray-900 dark:text-gray-100 font-mono">{prompt.suggestion.original_input}</p>
              </div>
              <div>
                <span className="font-medium text-gray-600 dark:text-gray-400">Suggested:</span>
                <p className="text-gray-900 dark:text-gray-100 font-semibold">
                  {prompt.suggestion.corrected_name} ({prompt.suggestion.ticker})
                </p>
              </div>
              <div>
                <span className="font-medium text-gray-600 dark:text-gray-400">Confidence:</span>
                <Badge className={
                  prompt.suggestion.confidence === 'high' ? 'bg-green-100 text-green-800' :
                  prompt.suggestion.confidence === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-gray-100 text-gray-800'
                }>
                  {prompt.suggestion.confidence.toUpperCase()}
                </Badge>
              </div>
              <div>
                <span className="font-medium text-gray-600 dark:text-gray-400">Explanation:</span>
                <p className="text-sm text-gray-700 dark:text-gray-300">{prompt.suggestion.explanation}</p>
              </div>
            </div>
          </div>
        )}

        <div className="flex gap-3 justify-end">
          <Button 
            variant="outline" 
            onClick={onReject}
            className="flex items-center gap-2"
          >
            <ThumbsDown className="h-4 w-4" />
            No, that's not right
          </Button>
          <Button 
            onClick={onConfirm}
            className="flex items-center gap-2 bg-green-600 hover:bg-green-700"
          >
            <ThumbsUp className="h-4 w-4" />
            Yes, proceed with {prompt.suggestion?.ticker || 'this'}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function App() {
  const [query, setQuery] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState('')
  
  // New state for confirmation flow
  const [confirmationPrompt, setConfirmationPrompt] = useState(null)
  const [conversationId, setConversationId] = useState(null)
  const [originalQuery, setOriginalQuery] = useState('')
  
  // State for WebSocket streaming
  const [currentRequestId, setCurrentRequestId] = useState(null)
  const [enableWebSocket, setEnableWebSocket] = useState(false)
  
  // WebSocket logs hook
  const { logs, isConnected, error: wsError, clearLogs } = useWebSocketLogs(
    currentRequestId,
    enableWebSocket
  )

  const handleAnalyze = async (confirmationResponse = null) => {
    if (!query.trim() && !confirmationResponse) return

    setIsAnalyzing(true)
    setError(null)
    setProgress(0)
    setCurrentStep('Initializing analysis...')

    // If this is the first request, clear previous results
    if (!confirmationResponse) {
      setAnalysisResult(null)
      setConfirmationPrompt(null)
      setOriginalQuery(query)
      clearLogs()
    }

    try {
      // Generate request ID for WebSocket connection
      const requestId = `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      setCurrentRequestId(requestId)
      setEnableWebSocket(true)
      
      const requestBody = {
        query: confirmationResponse ? originalQuery : query,
        max_iterations: 3,
        timeout_seconds: 60,
        request_id: requestId
      }

      // Add conversation fields if this is a confirmation response
      if (confirmationResponse && conversationId) {
        requestBody.conversation_id = conversationId
        requestBody.confirmation_response = confirmationResponse
      }
      
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`)
      }

      const result = await response.json()

      // Check if confirmation is needed
      if (result.needs_confirmation && result.confirmation_prompt) {
        setConfirmationPrompt(result.confirmation_prompt)
        setConversationId(result.confirmation_prompt.conversation_id)
        setProgress(0)
        setCurrentStep('Waiting for confirmation...')
      } else {
        // Normal analysis result
        setAnalysisResult(result)
        setConfirmationPrompt(null)
        setConversationId(null)
        setProgress(100)
        setCurrentStep('Analysis complete')
      }
    } catch (err) {
      setError(err.message)
      setConfirmationPrompt(null)
    } finally {
      setIsAnalyzing(false)
      // Keep WebSocket open for a bit to receive final logs
      setTimeout(() => {
        setEnableWebSocket(false)
      }, 2000)
    }
  }

  const handleConfirm = () => {
    handleAnalyze('Yes')
  }

  const handleReject = () => {
    handleAnalyze('No')
  }

  const getStanceIcon = (stance) => {
    switch (stance) {
      case 'buy':
        return <TrendingUp className="h-4 w-4 text-green-600" />
      case 'sell':
        return <TrendingDown className="h-4 w-4 text-red-600" />
      default:
        return <Minus className="h-4 w-4 text-yellow-600" />
    }
  }

  const getStanceColor = (stance) => {
    switch (stance) {
      case 'buy':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'sell':
        return 'bg-red-100 text-red-800 border-red-200'
      default:
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    }
  }

  const getConfidenceColor = (confidence) => {
    switch (confidence) {
      case 'high':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'low':
        return 'bg-gray-100 text-gray-800 border-gray-200'
      default:
        return 'bg-purple-100 text-purple-800 border-purple-200'
    }
  }

  const getAgentIcon = (agentType) => {
    switch (agentType) {
      case 'news':
        return <Newspaper className="h-4 w-4" />
      case 'filings':
        return <FileText className="h-4 w-4" />
      case 'earnings':
        return <BarChart3 className="h-4 w-4" />
      case 'insider':
        return <Users className="h-4 w-4" />
      case 'patents':
        return <Lightbulb className="h-4 w-4" />
      case 'price':
        return <TrendingUp className="h-4 w-4" />
      default:
        return <Brain className="h-4 w-4" />
    }
  }

  // Simulate progress updates during analysis
  useEffect(() => {
    if (isAnalyzing && !confirmationPrompt) {
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) return prev
          return prev + Math.random() * 10
        })
      }, 1000)

      return () => clearInterval(interval)
    }
  }, [isAnalyzing, confirmationPrompt])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            Stock Research Chatbot
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            AI-powered multi-agent research with smart spelling correction
          </p>
          <Badge className="mt-2 bg-blue-100 text-blue-800 border-blue-200">
            🆕 Gemini-Powered Smart Correction
          </Badge>
        </div>

        {/* Query Input */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5" />
              Research Query
            </CardTitle>
            <CardDescription>
              Enter company names or tickers - typos are OK! (e.g., "Analyze matae for 1 month" or "Compare microsft and gogle")
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <Textarea
                placeholder="Try: 'Analyze matae for 1 month' or 'Compare microsft, gogle, and amazn'"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="flex-1"
                rows={3}
                disabled={isAnalyzing || confirmationPrompt !== null}
              />
              <Button 
                onClick={() => handleAnalyze()}
                disabled={isAnalyzing || !query.trim() || confirmationPrompt !== null}
                className="px-8"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Brain className="h-4 w-4 mr-2" />
                    Analyze
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Confirmation Dialog */}
        {confirmationPrompt && (
          <ConfirmationDialog 
            prompt={confirmationPrompt}
            onConfirm={handleConfirm}
            onReject={handleReject}
          />
        )}

        {/* Streaming Log Panel - Show during confirmation too */}
        {(isAnalyzing || logs.length > 0) && (
          <StreamingLogPanel 
            logs={logs}
            isConnected={isConnected}
            error={wsError}
            onClear={clearLogs}
          />
        )}

        {/* Progress Indicator */}
        {isAnalyzing && !confirmationPrompt && (
          <Card className="mb-8">
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Analysis Progress</span>
                  <span className="text-sm text-gray-500">{Math.round(progress)}%</span>
                </div>
                <Progress value={progress} className="w-full" />
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Clock className="h-4 w-4" />
                  {currentStep}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Error Display */}
        {error && (
          <Alert className="mb-8 border-red-200 bg-red-50">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-red-800">
              {error}
            </AlertDescription>
          </Alert>
        )}

        {/* Analysis Results */}
        {analysisResult && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Tickers Analyzed</p>
                      <p className="text-2xl font-bold">{analysisResult.tickers_analyzed?.length || 0}</p>
                    </div>
                    <Building className="h-8 w-8 text-blue-600" />
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Agents Used</p>
                      <p className="text-2xl font-bold">{analysisResult.agents_used?.length || 0}</p>
                    </div>
                    <Brain className="h-8 w-8 text-purple-600" />
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Analysis Time</p>
                      <p className="text-2xl font-bold">{Math.round(analysisResult.total_latency_ms / 1000)}s</p>
                    </div>
                    <Clock className="h-8 w-8 text-green-600" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Ticker Insights */}
            <div className="space-y-6">
              {analysisResult.insights?.map((insight, index) => (
                <Card key={index} className="overflow-hidden">
                  <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700">
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-2xl">{insight.ticker}</CardTitle>
                        {insight.company_name && (
                          <CardDescription className="text-lg">{insight.company_name}</CardDescription>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={`${getStanceColor(insight.stance)} flex items-center gap-1`}>
                          {getStanceIcon(insight.stance)}
                          {insight.stance.toUpperCase()}
                        </Badge>
                        <Badge className={getConfidenceColor(insight.confidence)}>
                          {insight.confidence.toUpperCase()} CONFIDENCE
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  
                  <CardContent className="p-6">
                    <Tabs defaultValue="summary" className="w-full">
                      <TabsList className="grid w-full grid-cols-5">
                        <TabsTrigger value="summary">Summary</TabsTrigger>
                        <TabsTrigger value="drivers">Drivers</TabsTrigger>
                        <TabsTrigger value="risks">Risks</TabsTrigger>
                        <TabsTrigger value="catalysts">Catalysts</TabsTrigger>
                        <TabsTrigger value="sources">Sources</TabsTrigger>
                      </TabsList>
                      
                      <TabsContent value="summary" className="mt-4">
                        <div className="space-y-4">
                          {/* Price and Market Data */}
                          {insight.current_price && (
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                              <div>
                                <p className="text-sm text-gray-600 dark:text-gray-400">Current Price</p>
                                <p className="text-lg font-bold">${insight.current_price.toFixed(2)}</p>
                              </div>
                              {insight.market_cap && (
                                <div>
                                  <p className="text-sm text-gray-600 dark:text-gray-400">Market Cap</p>
                                  <p className="text-lg font-bold">
                                    {insight.market_cap >= 1e12 
                                      ? `$${(insight.market_cap / 1e12).toFixed(2)}T`
                                      : insight.market_cap >= 1e9
                                      ? `$${(insight.market_cap / 1e9).toFixed(2)}B`
                                      : insight.market_cap >= 1e6
                                      ? `$${(insight.market_cap / 1e6).toFixed(2)}M`
                                      : `$${insight.market_cap.toFixed(2)}`
                                    }
                                  </p>
                                </div>
                              )}
                              {insight.pe_ratio && (
                                <div>
                                  <p className="text-sm text-gray-600 dark:text-gray-400">P/E Ratio</p>
                                  <p className="text-lg font-bold">{insight.pe_ratio.toFixed(2)}</p>
                                </div>
                              )}
                              {insight.trend && (
                                <div>
                                  <p className="text-sm text-gray-600 dark:text-gray-400">Trend</p>
                                  <p className="text-lg font-bold capitalize">{insight.trend}</p>
                                </div>
                              )}
                            </div>
                          )}
                          
                          {/* Technical Levels */}
                          {(insight.support_levels?.length > 0 || insight.resistance_levels?.length > 0) && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                              {insight.support_levels?.length > 0 && (
                                <div>
                                  <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Support Levels</p>
                                  <div className="flex flex-wrap gap-2">
                                    {insight.support_levels.map((level, idx) => (
                                      <Badge key={idx} variant="outline" className="bg-green-100 text-green-800">
                                        ${level.toFixed(2)}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {insight.resistance_levels?.length > 0 && (
                                <div>
                                  <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Resistance Levels</p>
                                  <div className="flex flex-wrap gap-2">
                                    {insight.resistance_levels.map((level, idx) => (
                                      <Badge key={idx} variant="outline" className="bg-red-100 text-red-800">
                                        ${level.toFixed(2)}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                          
                          <Separator />
                          
                          <div>
                            <h4 className="font-semibold mb-2">Executive Summary</h4>
                            <p className="text-gray-700 dark:text-gray-300">{insight.summary}</p>
                          </div>
                          <Separator />
                          <div>
                            <h4 className="font-semibold mb-2">Investment Rationale</h4>
                            <p className="text-gray-700 dark:text-gray-300">{insight.rationale}</p>
                          </div>
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="drivers" className="mt-4">
                        <div className="space-y-2">
                          {insight.key_drivers?.map((driver, idx) => (
                            <div key={idx} className="flex items-start gap-2">
                              <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                              <span className="text-gray-700 dark:text-gray-300">{driver}</span>
                            </div>
                          ))}
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="risks" className="mt-4">
                        <div className="space-y-2">
                          {insight.risks?.map((risk, idx) => (
                            <div key={idx} className="flex items-start gap-2">
                              <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                              <span className="text-gray-700 dark:text-gray-300">{risk}</span>
                            </div>
                          ))}
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="catalysts" className="mt-4">
                        <div className="space-y-2">
                          {insight.catalysts?.map((catalyst, idx) => (
                            <div key={idx} className="flex items-start gap-2">
                              <TrendingUp className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                              <span className="text-gray-700 dark:text-gray-300">{catalyst}</span>
                            </div>
                          ))}
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="sources" className="mt-4">
                        <ScrollArea className="h-64">
                          <div className="space-y-3">
                            {insight.sources?.map((source, idx) => (
                              <div key={idx} className="border rounded-lg p-3">
                                <div className="flex items-start justify-between">
                                  <div className="flex-1">
                                    <h5 className="font-medium text-sm">{source.title || 'Source'}</h5>
                                    {source.snippet && (
                                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                                        {source.snippet}
                                      </p>
                                    )}
                                    {source.published_at && (
                                      <p className="text-xs text-gray-500 mt-1">
                                        Published: {new Date(source.published_at).toLocaleDateString()}
                                      </p>
                                    )}
                                  </div>
                                  <Button variant="ghost" size="sm" asChild>
                                    <a href={source.url} target="_blank" rel="noopener noreferrer">
                                      <ExternalLink className="h-3 w-3" />
                                    </a>
                                  </Button>
                                </div>
                              </div>
                            ))}
                          </div>
                        </ScrollArea>
                      </TabsContent>
                    </Tabs>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Agent Execution Details */}
            {analysisResult.insights?.some(insight => insight.agent_traces?.length > 0) && (
              <Card>
                <CardHeader>
                  <CardTitle>Agent Execution Details</CardTitle>
                  <CardDescription>
                    Detailed trace of how each research agent gathered information
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-96">
                    <div className="space-y-4">
                      {analysisResult.insights?.map((insight, insightIdx) => (
                        <div key={insightIdx}>
                          <h4 className="font-semibold text-lg mb-2">{insight.ticker}</h4>
                          {insight.agent_traces?.map((trace, traceIdx) => (
                            <div key={traceIdx} className="border rounded-lg p-4 mb-3">
                              <div className="flex items-center gap-2 mb-2">
                                {getAgentIcon(trace.agent_type)}
                                <span className="font-medium capitalize">{trace.agent_type} Agent</span>
                                <Badge variant={trace.success ? "default" : "destructive"}>
                                  {trace.success ? "Success" : "Failed"}
                                </Badge>
                                {trace.total_latency_ms && (
                                  <Badge variant="outline">
                                    {Math.round(trace.total_latency_ms)}ms
                                  </Badge>
                                )}
                              </div>
                              {trace.steps?.map((step, stepIdx) => (
                                <div key={stepIdx} className="ml-6 border-l-2 border-gray-200 pl-4 pb-2">
                                  <div className="text-sm">
                                    <p className="font-medium">Step {step.step_number}: {step.thought}</p>
                                    <p className="text-gray-600 mt-1">Action: {step.action}</p>
                                    <p className="text-gray-600 mt-1">Result: {step.observation}</p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App

