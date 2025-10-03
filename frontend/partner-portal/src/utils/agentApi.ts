/**
 * Agent API utilities for communicating with the AI service
 */

// Types for Agentic RAG
export type AgentChatRequest = {
  message: string
  session_id: string
  user_profile?: {
    preferences?: Record<string, any>
    history?: any[]
    budget_range?: [number, number]
    preferred_cities?: string[]
    preferred_amenities?: string[]
    travel_companion?: string
  }
  context?: Record<string, any>
}

export type SearchResultResponse = {
  establishment_id: string
  name: string
  relevance_score: number
  metadata: Record<string, any>
  explanation: string
}

export type AgentChatResponse = {
  success: boolean
  results: SearchResultResponse[]
  intent: string
  strategy_used: string
  explanation: string
  suggestions: string[]
  confidence: number
  processing_time: number
  metadata: Record<string, any>
}

export type AgentSearchRequest = {
  query: string
  strategy?: string
}

// Suggestion type (compatible with existing API)
export type Suggestion = {
  establishmentId: string
  establishmentName: string
  city: string
  itemType: string
  finalPrice: number
  unitsAvailable: number  // Changed from string to number for compatibility
  imageUrlMain: string
  floorArea: string
  itemImageUrl: string
  relevanceScore?: number
  explanation?: string
}

/**
 * Call Agent Chat API
 */
export const callAgentChat = async (
  message: string, 
  sessionId: string,
  userProfile?: AgentChatRequest['user_profile'],
  context?: Record<string, any>
): Promise<AgentChatResponse> => {
  const request: AgentChatRequest = {
    message,
    session_id: sessionId,
    user_profile: userProfile,
    context
  }

  const response = await fetch('http://localhost:8000/agent/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request)
  })

  if (!response.ok) {
    throw new Error(`Agent API error: ${response.status} - ${response.statusText}`)
  }

  return response.json()
}

/**
 * Call Agent Search API
 */
export const callAgentSearch = async (
  query: string, 
  strategy?: string
): Promise<AgentChatResponse> => {
  const request: AgentSearchRequest = {
    query,
    strategy
  }

  const response = await fetch('http://localhost:8000/agent/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request)
  })

  if (!response.ok) {
    throw new Error(`Agent Search API error: ${response.status} - ${response.statusText}`)
  }

  return response.json()
}

/**
 * Convert agent results to suggestion format for compatibility
 */
export const convertAgentResultsToSuggestions = (results: SearchResultResponse[]): Suggestion[] => {
  return results.map(result => ({
    establishmentId: result.establishment_id,
    establishmentName: result.name,
    city: result.metadata.city || 'N/A',
    itemType: result.metadata.type || 'HOTEL',
    finalPrice: result.metadata.price_range_vnd || 0,
    unitsAvailable: typeof result.metadata.availability?.units_available === 'number' 
      ? result.metadata.availability.units_available 
      : parseInt(result.metadata.availability?.units_available || '0') || 0,
    imageUrlMain: result.metadata.image_url_main || '',
    relevanceScore: result.relevance_score,
    explanation: result.explanation,
    // Add missing fields for compatibility
    floorArea: result.metadata.floor_area || 'Standard',
    itemImageUrl: result.metadata.image_url_main || ''
  }))
}

/**
 * Check if agent service is available
 */
export const checkAgentHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch('http://localhost:8000/agent/stats', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    })
    return response.ok
  } catch {
    return false
  }
}

/**
 * Get agent statistics
 */
export const getAgentStats = async (): Promise<any> => {
  try {
    const response = await fetch('http://localhost:8000/agent/stats', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    })

    if (!response.ok) {
      throw new Error(`Agent stats error: ${response.status}`)
    }

    return response.json()
  } catch (error) {
    console.error('Failed to get agent stats:', error)
    return null
  }
}

/**
 * Create a unique session ID
 */
export const createSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Update user profile based on agent insights
 */
export const updateUserProfileFromAgent = (
  currentProfile: AgentChatRequest['user_profile'],
  agentMetadata: Record<string, any>
): AgentChatRequest['user_profile'] => {
  if (!agentMetadata?.user_insights) {
    return currentProfile
  }

  return {
    ...currentProfile,
    preferences: { 
      ...currentProfile?.preferences, 
      ...agentMetadata.user_insights 
    }
  }
}

/**
 * Extract search strategy from context
 */
export const extractSearchStrategy = (context: Record<string, any>): string | undefined => {
  // Determine strategy based on context
  if (context.amenities_priority && context.amenities_priority.length > 3) {
    return 'contextual' // Many specific requirements
  }
  
  if (context.max_price && context.max_price > 3000000) {
    return 'hybrid' // High budget, likely specific needs
  }
  
  return 'semantic' // Default semantic search
}

/**
 * Build context for agent from current parameters
 */
export const buildAgentContext = (params: Record<string, any>): Record<string, any> => {
  const context: Record<string, any> = { ...params }
  
  // Add derived context
  if (params.amenities_priority) {
    context.amenities_count = params.amenities_priority.split(',').length
  }
  
  if (params.max_price) {
    context.budget_category = params.max_price < 1000000 ? 'budget' : 
                             params.max_price < 3000000 ? 'mid' : 'luxury'
  }
  
  if (params.duration) {
    context.trip_length = params.duration < 3 ? 'short' : 
                         params.duration < 7 ? 'medium' : 'long'
  }
  
  return context
}
