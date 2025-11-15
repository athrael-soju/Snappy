# Snappy Plus Master Plan
## Vision-Powered Realtime AI Assistant with Memory

---

## Executive Summary

**Snappy Plus** is a premium feature that transforms Snappy into an interactive, voice-enabled AI assistant with persistent memory. Users will interact with an elegant, minimalist interface featuring bidirectional voice communication via OpenAI's Realtime API, supported by a Neo4j knowledge graph for long-term and short-term memory using the Graphiti framework.

### Key Differentiators
- **Bidirectional Voice**: Natural conversation using OpenAI Realtime API
- **Persistent Memory**: Neo4j knowledge graph with Graphiti framework
- **Visual Simplicity**: Peach/orange gradient with voice-reactive animation (inspired by "Her")
- **Tool Integration**: Access to existing knowledge base and external services
- **Personalized Onboarding**: Initial conversation to learn user preferences

---

## Current Architecture Analysis

### Strengths to Leverage
✅ **Modular Microservices**: Easy to add Neo4j, authentication, and new services
✅ **FastAPI Backend**: Async-ready, OpenAPI schema generation
✅ **Next.js 16 + React 19**: Modern frontend with server actions
✅ **SSE Infrastructure**: Real-time progress tracking already implemented
✅ **Configuration System**: Schema-driven, runtime-updateable
✅ **Existing Knowledge Base**: ColPali + Qdrant RAG system ready for tool calls

### Critical Gaps to Address
❌ **No Authentication/Authorization**: Cannot identify or restrict users
❌ **No User Database**: No persistent user profiles
❌ **No Payment Integration**: Cannot manage premium subscriptions
❌ **No WebSocket Support**: Needed for Realtime API
❌ **No Neo4j**: Graph database required for memory system
❌ **No Multi-tenancy**: Single shared knowledge base

---

## Technology Stack Additions

### Backend Services
| Component | Technology | Purpose | Why This Choice |
|-----------|-----------|---------|-----------------|
| **Graph Database** | Neo4j (Enterprise 5.x) | User memory, relationships, knowledge graph | Industry standard, Graphiti integration, ACID compliance |
| **Authentication** | FastAPI-Users + JWT | User management, session handling | FastAPI native, production-proven, OAuth2 ready |
| **User Database** | PostgreSQL 16 | User profiles, subscriptions, audit logs | ACID guarantees, JSON support, full-text search |
| **Payment Processing** | Stripe API | Subscription billing, usage tracking | Industry leader, comprehensive webhooks, PCI compliant |
| **WebSocket Gateway** | FastAPI WebSockets | Realtime API proxy, bidirectional communication | Native FastAPI support, async-ready |
| **Memory Framework** | Graphiti | Knowledge graph management, entity extraction | Purpose-built for Neo4j, temporal memory support |
| **Task Queue** | Celery + Redis | Async memory processing, background jobs | Battle-tested, scales horizontally |

### Frontend Libraries
| Component | Technology | Purpose | Why This Choice |
|-----------|-----------|---------|-----------------|
| **Realtime Audio** | `@openai/realtime-api-beta` | OpenAI Realtime API client | Official SDK, WebRTC support |
| **Audio Visualization** | `react-audio-visualize` + Framer Motion | Voice-reactive ball animation | Lightweight, smooth animations |
| **WebSocket Client** | Native WebSocket API | Bidirectional communication | Built into browsers, Next.js compatible |
| **Voice Activity Detection** | `@ricky0123/vad-web` | Detect user speech start/end | Browser-based, no backend dependency |
| **Authentication UI** | NextAuth.js v5 (Auth.js) | Login flows, session management | Next.js 16 compatible, OAuth ready |

### Infrastructure
| Component | Technology | Purpose | Why This Choice |
|-----------|-----------|---------|-----------------|
| **Container Orchestration** | Docker Compose (dev), Kubernetes (prod) | Service management | Current stack uses Compose, K8s for scale |
| **Secrets Management** | Vault (prod), .env (dev) | API keys, credentials | Enterprise standard, audit trails |
| **Monitoring** | Prometheus + Grafana | System health, usage metrics | Open-source, Neo4j exporter available |
| **Logging** | Loki + Promtail | Centralized logs | Integrates with Grafana, low resource usage |

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Snappy Plus UI (Next.js 16 Page)                         │ │
│  │  - Voice-reactive ball animation                          │ │
│  │  - WebSocket connection to backend                        │ │
│  │  - Audio input/output handling                            │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────┘
                            │ WebSocket (bidirectional)
┌───────────────────────────┴─────────────────────────────────────┐
│                    BACKEND (FastAPI)                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  WebSocket Gateway (/api/realtime/ws)                     │ │
│  │  - OpenAI Realtime API proxy                              │ │
│  │  - Tool call orchestration                                │ │
│  │  - Session management                                     │ │
│  └────┬────────────────────────────────────┬─────────────────┘ │
│       │                                    │                   │
│  ┌────▼──────────┐  ┌──────────────┐  ┌───▼─────────────────┐ │
│  │  Auth Service │  │  User Service│  │  Memory Service     │ │
│  │  (JWT)        │  │  (PostgreSQL)│  │  (Neo4j + Graphiti) │ │
│  └───────────────┘  └──────────────┘  └─────────────────────┘ │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Tool Orchestrator                                         │ │
│  │  - Knowledge Base Tool (existing RAG)                      │ │
│  │  - Memory Recording Tool (knowledge graph)                 │ │
│  │  - Weather Tool (external API)                             │ │
│  │  - Web Browse Tool (future)                                │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────┐
│                    EXTERNAL SERVICES                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  OpenAI      │  │  Neo4j       │  │  PostgreSQL  │         │
│  │  Realtime API│  │  (Graph DB)  │  │  (User DB)   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Stripe      │  │  Redis       │  │  Existing    │         │
│  │  (Billing)   │  │  (Queue)     │  │  Services    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                       (Qdrant, MinIO, etc)     │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow: Voice Conversation with Memory

```
User speaks
    ↓
Frontend (VAD detects speech) → captures audio
    ↓
WebSocket → sends audio chunks to backend
    ↓
Backend → forwards to OpenAI Realtime API
    ↓
OpenAI processes speech → generates response + potential tool calls
    ↓
Backend receives tool call (e.g., "search_knowledge_base")
    ↓
Tool Orchestrator → executes tool (existing RAG system)
    ↓
Tool result → sent to OpenAI Realtime API
    ↓
OpenAI generates final response with context
    ↓
Backend → forwards audio response to frontend
    ↓
Frontend → plays audio + animates ball
    ↓
ASYNC: Celery task → Memory Service
    ↓
Graphiti extracts entities/relationships → saves to Neo4j
```

---

## Database Schemas

### PostgreSQL Schema (User Management)

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    subscription_tier VARCHAR(50) DEFAULT 'free', -- free, plus, enterprise
    subscription_status VARCHAR(50) DEFAULT 'inactive', -- active, canceled, past_due
    stripe_customer_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscription history
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
    tier VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_period_start TIMESTAMP NOT NULL,
    current_period_end TIMESTAMP NOT NULL,
    cancel_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Usage tracking
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- voice_message, tool_call, memory_query
    tokens_used INTEGER,
    duration_seconds INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Onboarding state
CREATE TABLE user_onboarding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    completed BOOLEAN DEFAULT FALSE,
    current_step INTEGER DEFAULT 0,
    preferences JSONB, -- Stores user preferences from onboarding
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions (for WebSocket connection tracking)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_stripe_customer_id ON users(stripe_customer_id);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX idx_usage_logs_session_id ON usage_logs(session_id);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(session_token);
```

### Neo4j Schema (Knowledge Graph)

**Node Types:**

```cypher
// User node
(:User {
    id: "uuid",
    email: "string",
    name: "string",
    created_at: datetime,
    updated_at: datetime
})

// Conversation node (represents a session)
(:Conversation {
    id: "uuid",
    user_id: "uuid",
    started_at: datetime,
    ended_at: datetime,
    summary: "string",
    message_count: integer
})

// Message node (individual exchanges)
(:Message {
    id: "uuid",
    conversation_id: "uuid",
    role: "user|assistant",
    content: "string",
    timestamp: datetime,
    tool_calls: ["array of tool names"]
})

// Entity nodes (extracted by Graphiti)
(:Person {
    id: "uuid",
    name: "string",
    first_mentioned: datetime,
    last_mentioned: datetime,
    mentions_count: integer
})

(:Concept {
    id: "uuid",
    name: "string",
    description: "string",
    category: "string",
    first_mentioned: datetime,
    last_mentioned: datetime
})

(:Topic {
    id: "uuid",
    name: "string",
    description: "string",
    importance_score: float
})

(:Preference {
    id: "uuid",
    category: "string", // e.g., "communication_style", "interests"
    key: "string",
    value: "string",
    confidence: float,
    created_at: datetime,
    updated_at: datetime
})

// Document reference (from existing knowledge base)
(:Document {
    id: "uuid",
    filename: "string",
    qdrant_collection: "string",
    indexed_at: datetime
})
```

**Relationship Types:**

```cypher
// User relationships
(:User)-[:HAS_CONVERSATION]->(:Conversation)
(:User)-[:HAS_PREFERENCE]->(:Preference)
(:User)-[:KNOWS_ABOUT]->(:Concept)
(:User)-[:INTERESTED_IN]->(:Topic)

// Conversation relationships
(:Conversation)-[:CONTAINS_MESSAGE]->(:Message)
(:Conversation)-[:DISCUSSES_TOPIC]->(:Topic)
(:Conversation)-[:REFERENCES_DOCUMENT]->(:Document)

// Message relationships
(:Message)-[:MENTIONS_ENTITY]->(:Person|:Concept|:Topic)
(:Message)-[:PRECEDED_BY]->(:Message)

// Entity relationships (learned over time)
(:Person)-[:RELATED_TO]->(:Person)
(:Concept)-[:RELATED_TO]->(:Concept)
(:Topic)-[:SUBTOPIC_OF]->(:Topic)
(:Preference)-[:CONFLICTS_WITH]->(:Preference)
(:Preference)-[:SUPPORTS]->(:Topic)

// Temporal relationships
(:Message)-[:OCCURRED_IN_CONTEXT]->(:Conversation)
(:Entity)-[:MENTIONED_IN]->(:Message)
```

**Example Queries:**

```cypher
// Get user's recent conversations with summaries
MATCH (u:User {id: $user_id})-[:HAS_CONVERSATION]->(c:Conversation)
WHERE c.ended_at > datetime() - duration({days: 7})
RETURN c
ORDER BY c.started_at DESC
LIMIT 10;

// Find all preferences for a user
MATCH (u:User {id: $user_id})-[:HAS_PREFERENCE]->(p:Preference)
RETURN p.category, p.key, p.value, p.confidence
ORDER BY p.confidence DESC;

// Get related concepts to enrich conversation context
MATCH (u:User {id: $user_id})-[:KNOWS_ABOUT]->(c:Concept)
MATCH (c)-[:RELATED_TO*1..2]->(related:Concept)
RETURN DISTINCT related.name, related.description
LIMIT 20;

// Retrieve conversation history with context
MATCH (u:User {id: $user_id})-[:HAS_CONVERSATION]->(conv:Conversation)-[:CONTAINS_MESSAGE]->(m:Message)
WHERE conv.id = $conversation_id
OPTIONAL MATCH (m)-[:MENTIONS_ENTITY]->(e)
RETURN m.content, m.role, m.timestamp, collect(e) as entities
ORDER BY m.timestamp ASC;
```

---

## API Design

### Authentication Endpoints

```python
# POST /api/auth/register
Request:
{
    "email": "user@example.com",
    "password": "secure_password",
    "full_name": "John Doe"
}
Response: 201 Created
{
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "subscription_tier": "free"
}

# POST /api/auth/login
Request:
{
    "email": "user@example.com",
    "password": "secure_password"
}
Response: 200 OK
{
    "access_token": "jwt_token",
    "refresh_token": "jwt_token",
    "token_type": "bearer",
    "expires_in": 3600
}

# POST /api/auth/refresh
Headers: Authorization: Bearer <refresh_token>
Response: 200 OK
{
    "access_token": "new_jwt_token",
    "token_type": "bearer",
    "expires_in": 3600
}

# POST /api/auth/logout
Headers: Authorization: Bearer <access_token>
Response: 204 No Content
```

### Subscription Management Endpoints

```python
# GET /api/subscriptions/me
Headers: Authorization: Bearer <access_token>
Response: 200 OK
{
    "tier": "plus",
    "status": "active",
    "current_period_end": "2025-02-15T00:00:00Z",
    "cancel_at_period_end": false,
    "usage_this_month": {
        "voice_minutes": 120,
        "tool_calls": 450,
        "limit_voice_minutes": 500,
        "limit_tool_calls": 10000
    }
}

# POST /api/subscriptions/create-checkout-session
Headers: Authorization: Bearer <access_token>
Request:
{
    "tier": "plus", // plus or enterprise
    "return_url": "https://app.snappy.com/snappy-plus"
}
Response: 200 OK
{
    "checkout_url": "https://checkout.stripe.com/...",
    "session_id": "stripe_session_id"
}

# POST /api/subscriptions/cancel
Headers: Authorization: Bearer <access_token>
Response: 200 OK
{
    "status": "canceled",
    "cancel_at": "2025-02-15T00:00:00Z"
}

# POST /api/webhooks/stripe
# Webhook endpoint for Stripe events
# Handles: subscription.created, subscription.updated, subscription.deleted, invoice.paid, etc.
```

### Snappy Plus Realtime Endpoints

```python
# WebSocket /api/realtime/ws
# Query params: access_token (JWT)
# Protocol: Bidirectional WebSocket

# Client → Server messages:
{
    "type": "audio_chunk",
    "data": "base64_encoded_audio",
    "format": "pcm16", // or mp3, opus
    "sample_rate": 24000
}

{
    "type": "session.update",
    "session": {
        "modalities": ["text", "audio"],
        "instructions": "Custom instructions...",
        "voice": "alloy",
        "input_audio_format": "pcm16",
        "output_audio_format": "pcm16"
    }
}

{
    "type": "conversation.item.create",
    "item": {
        "type": "message",
        "role": "user",
        "content": [{"type": "input_text", "text": "Hello"}]
    }
}

# Server → Client messages:
{
    "type": "audio_chunk",
    "data": "base64_encoded_audio",
    "message_id": "msg_123"
}

{
    "type": "response.text.delta",
    "delta": "partial text...",
    "message_id": "msg_123"
}

{
    "type": "response.function_call",
    "function_name": "search_knowledge_base",
    "arguments": "{\"query\": \"...\"}"
}

{
    "type": "response.function_call_output",
    "call_id": "call_123",
    "output": "{\"results\": [...]}"
}

{
    "type": "error",
    "error": {
        "code": "unauthorized",
        "message": "Invalid token"
    }
}

# GET /api/realtime/onboarding/status
Headers: Authorization: Bearer <access_token>
Response: 200 OK
{
    "completed": false,
    "current_step": 2,
    "total_steps": 5,
    "preferences": {
        "communication_style": "casual",
        "interests": ["technology", "science"]
    }
}

# POST /api/realtime/onboarding/complete
Headers: Authorization: Bearer <access_token>
Request:
{
    "preferences": {
        "communication_style": "professional",
        "interests": ["technology", "finance"],
        "preferred_voice": "nova",
        "notification_preferences": {
            "email": true,
            "push": false
        }
    }
}
Response: 200 OK
{
    "completed": true,
    "message": "Onboarding completed successfully"
}
```

### Memory Service Endpoints

```python
# GET /api/memory/conversations
Headers: Authorization: Bearer <access_token>
Query params: limit=10, offset=0, days=7
Response: 200 OK
{
    "conversations": [
        {
            "id": "uuid",
            "started_at": "2025-01-10T14:30:00Z",
            "ended_at": "2025-01-10T14:45:00Z",
            "summary": "Discussed document retrieval optimization",
            "message_count": 12,
            "topics": ["RAG", "embeddings", "performance"]
        }
    ],
    "total": 25,
    "limit": 10,
    "offset": 0
}

# GET /api/memory/conversations/{conversation_id}
Headers: Authorization: Bearer <access_token>
Response: 200 OK
{
    "id": "uuid",
    "started_at": "2025-01-10T14:30:00Z",
    "ended_at": "2025-01-10T14:45:00Z",
    "messages": [
        {
            "id": "msg_1",
            "role": "user",
            "content": "How can I improve search performance?",
            "timestamp": "2025-01-10T14:30:15Z",
            "entities": [
                {"type": "Concept", "name": "search performance"}
            ]
        },
        {
            "id": "msg_2",
            "role": "assistant",
            "content": "You can improve search performance by...",
            "timestamp": "2025-01-10T14:30:22Z",
            "tool_calls": ["search_knowledge_base"]
        }
    ]
}

# GET /api/memory/preferences
Headers: Authorization: Bearer <access_token>
Response: 200 OK
{
    "preferences": [
        {
            "category": "communication_style",
            "key": "formality",
            "value": "professional",
            "confidence": 0.85,
            "updated_at": "2025-01-10T14:30:00Z"
        }
    ]
}

# GET /api/memory/search
Headers: Authorization: Bearer <access_token>
Query params: query="embeddings", type="concept", limit=10
Response: 200 OK
{
    "results": [
        {
            "type": "Concept",
            "name": "ColPali embeddings",
            "description": "Vision-based document embeddings",
            "relevance_score": 0.92,
            "first_mentioned": "2025-01-05T10:00:00Z",
            "last_mentioned": "2025-01-10T14:30:00Z",
            "mentions_count": 8
        }
    ]
}
```

### Tool Definitions (for OpenAI Realtime API)

```json
{
    "name": "search_knowledge_base",
    "description": "Search the user's document knowledge base using vision-based semantic search. Use this when the user asks about content in their uploaded documents.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language search query"
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return (default: 5)",
                "default": 5
            },
            "mode": {
                "type": "string",
                "enum": ["image", "ocr", "hybrid"],
                "description": "Retrieval mode: image-only, OCR text, or hybrid",
                "default": "hybrid"
            }
        },
        "required": ["query"]
    }
}

{
    "name": "record_memory",
    "description": "Record important information about the user, their preferences, or key topics discussed. Use this to build long-term memory about the user.",
    "parameters": {
        "type": "object",
        "properties": {
            "entity_type": {
                "type": "string",
                "enum": ["preference", "concept", "person", "topic"],
                "description": "Type of information to record"
            },
            "name": {
                "type": "string",
                "description": "Name or key of the entity"
            },
            "value": {
                "type": "string",
                "description": "Value or description"
            },
            "category": {
                "type": "string",
                "description": "Category (for preferences: communication_style, interests, etc.)"
            },
            "confidence": {
                "type": "number",
                "description": "Confidence level (0-1)",
                "default": 0.8
            }
        },
        "required": ["entity_type", "name", "value"]
    }
}

{
    "name": "get_weather",
    "description": "Get current weather for a location",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name or coordinates"
            },
            "units": {
                "type": "string",
                "enum": ["metric", "imperial"],
                "default": "metric"
            }
        },
        "required": ["location"]
    }
}
```

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)

**Goal**: Establish core infrastructure for user management and authentication

#### Backend Tasks
- [ ] Set up PostgreSQL database and connection pool
- [ ] Implement user authentication with FastAPI-Users
  - User registration with email verification
  - Login/logout with JWT tokens
  - Password reset flow
  - Refresh token rotation
- [ ] Create user service with CRUD operations
- [ ] Add authentication middleware to existing routes
- [ ] Update OpenAPI schema with auth endpoints

#### Frontend Tasks
- [ ] Install NextAuth.js v5 (Auth.js)
- [ ] Create authentication pages
  - `/login` - Login form
  - `/register` - Registration form
  - `/forgot-password` - Password reset
- [ ] Implement protected route wrapper
- [ ] Update navigation to show user state
- [ ] Add logout functionality
- [ ] Run `yarn gen:sdk` to regenerate API client

#### Infrastructure
- [ ] Add PostgreSQL to docker-compose.yml
- [ ] Create database migration scripts
- [ ] Set up environment variables for secrets
- [ ] Update CORS configuration for auth cookies

#### Testing
- [ ] Unit tests for auth service
- [ ] Integration tests for registration/login flow
- [ ] Test protected route access

**Deliverable**: Users can register, login, and access protected routes

---

### Phase 2: Subscription & Billing (Weeks 3-4)

**Goal**: Enable premium tier subscriptions via Stripe

#### Backend Tasks
- [ ] Install Stripe Python SDK
- [ ] Create subscription service
  - Stripe customer creation
  - Checkout session creation
  - Subscription status checking
  - Usage tracking
- [ ] Implement webhook handler for Stripe events
  - `customer.subscription.created`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.paid`
  - `invoice.payment_failed`
- [ ] Add subscription tier checking middleware
- [ ] Create usage logging system
- [ ] Update OpenAPI schema

#### Frontend Tasks
- [ ] Create subscription management page (`/subscription`)
  - Current plan display
  - Upgrade/downgrade options
  - Usage metrics dashboard
  - Billing history
- [ ] Implement Stripe Checkout integration
- [ ] Add subscription status indicators
- [ ] Create usage warning notifications (approaching limits)
- [ ] Run `yarn gen:sdk`

#### Infrastructure
- [ ] Set up Stripe account (test mode)
- [ ] Configure webhook endpoint
- [ ] Add Stripe API keys to secrets
- [ ] Create subscription products in Stripe
  - "Snappy Plus" - $20/month
  - Metered usage tiers (optional)

#### Testing
- [ ] Test complete subscription flow (checkout → webhook → activation)
- [ ] Test subscription cancellation
- [ ] Test usage limit enforcement
- [ ] Verify webhook signature validation

**Deliverable**: Users can subscribe to Snappy Plus and access is gated by subscription status

---

### Phase 3: Neo4j & Graphiti Setup (Week 5)

**Goal**: Establish knowledge graph infrastructure for memory

#### Backend Tasks
- [ ] Install Neo4j Python driver (`neo4j`)
- [ ] Install Graphiti framework (`graphiti-core`)
- [ ] Create Neo4j connection manager
- [ ] Initialize graph schema
  - Create constraints for unique IDs
  - Create indexes for performance
- [ ] Implement Graphiti integration
  - Entity extraction pipeline
  - Relationship inference
  - Temporal episode management
- [ ] Create memory service
  - Store conversation
  - Store message
  - Extract and save entities
  - Query memory
- [ ] Add memory endpoints to API
- [ ] Update OpenAPI schema

#### Infrastructure
- [ ] Add Neo4j Enterprise 5.x to docker-compose.yml
- [ ] Configure Neo4j plugins (APOC, Graph Data Science)
- [ ] Set up persistent volume for graph data
- [ ] Configure Neo4j authentication
- [ ] Enable Neo4j Browser for debugging (localhost:7474)

#### Testing
- [ ] Test Neo4j connection and queries
- [ ] Test Graphiti entity extraction
- [ ] Test memory storage and retrieval
- [ ] Load test with sample conversations

**Deliverable**: Neo4j is running and can store/retrieve conversation memory

---

### Phase 4: Snappy Plus UI (Week 6)

**Goal**: Build the minimalist voice interface

#### Frontend Tasks
- [ ] Install audio libraries
  - `@openai/realtime-api-beta`
  - `react-audio-visualize` or custom canvas animation
  - `@ricky0123/vad-web` (Voice Activity Detection)
- [ ] Create Snappy Plus page (`/snappy-plus`)
  - Peach/orange gradient background (CSS)
  - Centered animated ball component
  - Microphone permission handling
  - Audio playback controls (mute/unmute)
- [ ] Implement voice-reactive animation
  - Audio level detection
  - Smooth scaling/pulsing with Framer Motion
  - Idle state gentle breathing animation
  - Speaking state reactive pulsing
- [ ] Create WebSocket connection manager
  - Connection state handling
  - Reconnection logic with exponential backoff
  - Error handling and user feedback
- [ ] Add conversation history sidebar (collapsible)
  - Message list with timestamps
  - Entity highlights
  - Export conversation option
- [ ] Add settings panel
  - Voice selection (alloy, echo, fable, onyx, nova, shimmer)
  - Microphone selection
  - Audio output selection
  - VAD sensitivity
- [ ] Implement mobile responsiveness

#### Design System
- [ ] Define color palette
  - Primary gradient: `#FF6B6B` (coral) → `#FFD93D` (golden)
  - Background gradient: `#FFF5E6` (light peach) → `#FFE8CC` (light orange)
  - Text: `#2C2C2C` (near black)
  - Accent: `#FF8C42` (vibrant orange)
- [ ] Create animation variants
  - Idle: subtle scale pulse (0.98 → 1.02, 2s ease-in-out)
  - Listening: faster pulse + glow effect
  - Speaking: reactive to audio amplitude
  - Thinking: rotating gradient shimmer
- [ ] Typography
  - Headings: System font stack (SF Pro, Segoe UI)
  - Body: Inter or default system font
  - Sizes: Minimal text, large breathing room

#### Testing
- [ ] Test on Chrome, Firefox, Safari
- [ ] Test microphone permissions flow
- [ ] Test audio playback across devices
- [ ] Test animation performance (60fps target)
- [ ] Test mobile responsiveness

**Deliverable**: Beautiful, functional voice interface (UI only, no backend connection yet)

---

### Phase 5: Realtime API Integration (Weeks 7-8)

**Goal**: Connect UI to OpenAI Realtime API via backend WebSocket

#### Backend Tasks
- [ ] Install OpenAI Python SDK with Realtime API support
- [ ] Create WebSocket endpoint (`/api/realtime/ws`)
  - Authenticate user via JWT in query params or initial message
  - Establish OpenAI Realtime API connection
  - Proxy audio chunks bidirectionally
  - Handle session configuration
- [ ] Implement tool orchestration
  - Parse function calls from OpenAI
  - Execute tool logic
  - Return results to OpenAI
- [ ] Create session manager
  - Track active WebSocket connections
  - Associate sessions with users
  - Handle graceful disconnection
  - Clean up on timeout/error
- [ ] Add rate limiting for Snappy Plus endpoints
  - Per-user request limits
  - Usage quota enforcement
- [ ] Update OpenAPI schema (WebSocket not in schema, but document separately)

#### Frontend Tasks
- [ ] Connect WebSocket to backend
- [ ] Implement audio streaming
  - Capture microphone input
  - Send PCM16 chunks via WebSocket
  - Receive and play audio responses
- [ ] Integrate Voice Activity Detection
  - Detect speech start/end
  - Visual feedback (ball animation change)
- [ ] Handle tool calls
  - Display "thinking" state during tool execution
  - Show tool results in conversation history (optional)
- [ ] Add error handling
  - Connection lost → retry UI
  - Microphone access denied → fallback message
  - Subscription expired → upgrade prompt
- [ ] Implement message history rendering
  - User messages (text if available)
  - Assistant responses (text + audio indicator)
  - Tool calls (collapsed/expandable)

#### Testing
- [ ] Test end-to-end voice conversation
- [ ] Test tool calling (search knowledge base)
- [ ] Test session persistence across page reloads
- [ ] Test concurrent users (load testing)
- [ ] Test error scenarios (network loss, token expiry)

**Deliverable**: Fully functional bidirectional voice chat with tool calling

---

### Phase 6: Memory System Integration (Week 9)

**Goal**: Record and utilize conversation memory

#### Backend Tasks
- [ ] Implement async memory recording
  - Celery task for background processing
  - Graphiti entity extraction from conversation
  - Save to Neo4j knowledge graph
- [ ] Create memory retrieval service
  - Query recent conversations
  - Retrieve user preferences
  - Find related concepts
- [ ] Integrate memory into conversation context
  - Prepend relevant memory to system prompt
  - Include user preferences in instructions
  - Reference past conversations in responses
- [ ] Implement memory tool for Realtime API
  - Tool definition: `record_memory`
  - Allow AI to explicitly save important info

#### Frontend Tasks
- [ ] Create memory dashboard page (`/memory`)
  - Conversation timeline
  - Entity graph visualization (optional: use vis.js or react-force-graph)
  - Preferences editor
  - Search memories
- [ ] Add memory indicators in Snappy Plus UI
  - Subtle notification when AI references past conversation
  - Highlight entities mentioned in current conversation
- [ ] Export memory feature
  - Download conversation history as JSON
  - GDPR compliance (data portability)

#### Testing
- [ ] Test memory recording after conversations
- [ ] Test memory retrieval in new conversations
- [ ] Verify Graphiti entity extraction accuracy
- [ ] Test memory search functionality

**Deliverable**: AI remembers past conversations and user preferences

---

### Phase 7: Onboarding Flow (Week 10)

**Goal**: Initial conversation to learn about new users

#### Backend Tasks
- [ ] Create onboarding service
  - Define onboarding questions
  - Track progress
  - Save preferences to PostgreSQL and Neo4j
- [ ] Add onboarding status to user profile
- [ ] Create onboarding completion endpoint
- [ ] Define initial system prompt for onboarding

#### Frontend Tasks
- [ ] Create onboarding flow
  - Detect first-time Snappy Plus user
  - Guide through 5 introductory questions
  - Save preferences
  - Transition to normal mode
- [ ] Design onboarding questions
  1. "Hi! I'm Snappy Plus. What should I call you?"
  2. "What brings you to Snappy Plus today?"
  3. "How would you like me to communicate? Formal or casual?"
  4. "What topics are you most interested in?"
  5. "Great! I'll remember our conversation. Ready to get started?"
- [ ] Add skip option (with warning)
- [ ] Show progress indicator (5 steps)

#### Testing
- [ ] Test complete onboarding flow
- [ ] Verify preferences are saved correctly
- [ ] Test skip functionality
- [ ] Ensure onboarding doesn't repeat for returning users

**Deliverable**: New users have personalized onboarding experience

---

### Phase 8: Additional Tools (Week 11)

**Goal**: Add weather and web browsing tools

#### Backend Tasks
- [ ] Implement weather tool
  - Integrate with OpenWeatherMap API or similar
  - Parse location from user request
  - Return formatted weather data
- [ ] Implement web browsing tool (optional/future)
  - Use Playwright or Selenium
  - Fetch and summarize web pages
  - Handle rate limiting and errors
- [ ] Register tools with Realtime API
- [ ] Add usage tracking for tool calls

#### Frontend Tasks
- [ ] Display tool results in conversation
  - Weather: Show formatted card with temperature, conditions
  - Web results: Show source URL and summary
- [ ] Add tool usage indicators in UI

#### Testing
- [ ] Test weather tool with various locations
- [ ] Test error handling (invalid location, API down)
- [ ] Test web browsing tool (if implemented)

**Deliverable**: AI can fetch weather and (optionally) browse web

---

### Phase 9: Polish & Optimization (Week 12)

**Goal**: Performance, security, and UX improvements

#### Backend Tasks
- [ ] Optimize database queries
  - Add missing indexes
  - Review N+1 queries
  - Implement query caching where appropriate
- [ ] Add comprehensive logging
  - Structured logs with correlation IDs
  - Error tracking (Sentry integration optional)
- [ ] Implement rate limiting
  - Per-user API limits
  - WebSocket connection limits
- [ ] Security audit
  - SQL injection prevention
  - XSS prevention
  - CSRF protection
  - Secrets rotation
- [ ] Add health check endpoints
  - `/health/liveness` - Service is running
  - `/health/readiness` - Service is ready to accept traffic

#### Frontend Tasks
- [ ] Performance optimization
  - Code splitting for Snappy Plus page
  - Lazy load heavy components
  - Optimize animation frame rates
- [ ] Accessibility improvements
  - Keyboard navigation
  - Screen reader support
  - ARIA labels
- [ ] Error boundaries
  - Graceful error handling
  - User-friendly error messages
- [ ] Loading states
  - Skeleton screens
  - Progressive enhancement
- [ ] Add analytics (optional)
  - Track feature usage (privacy-compliant)
  - Monitor conversion funnel

#### Testing
- [ ] Load testing
  - Concurrent WebSocket connections
  - Database query performance
  - Memory usage under load
- [ ] Security testing
  - Penetration testing
  - Dependency vulnerability scanning
- [ ] User acceptance testing
  - Internal team testing
  - Beta user feedback

#### Documentation
- [ ] API documentation (auto-generated via OpenAPI)
- [ ] User guide for Snappy Plus
- [ ] Deployment runbook
- [ ] Troubleshooting guide

**Deliverable**: Production-ready Snappy Plus feature

---

## Security Considerations

### Authentication & Authorization
1. **JWT Tokens**
   - Use short-lived access tokens (15 minutes)
   - Long-lived refresh tokens (7 days) stored httpOnly cookies
   - Rotate refresh tokens on each use
   - Blacklist tokens on logout (Redis cache)

2. **Password Security**
   - Argon2id hashing (FastAPI-Users default)
   - Minimum password length: 12 characters
   - Enforce complexity requirements
   - Rate limit login attempts (5 per minute)

3. **Session Management**
   - Generate cryptographically secure session IDs
   - Invalidate sessions on password change
   - Expire sessions after 7 days of inactivity
   - Log all authentication events

### API Security
1. **Input Validation**
   - Validate all user inputs with Pydantic models
   - Sanitize data before database insertion
   - Limit request body sizes (already 200MB for server actions)
   - Prevent SQL injection (use parameterized queries)

2. **Rate Limiting**
   - Global: 100 requests/minute per IP
   - Authenticated: 1000 requests/minute per user
   - WebSocket: 1 connection per user
   - Tool calls: 100/hour per user (configurable by tier)

3. **CORS**
   - Whitelist specific origins (no wildcards in production)
   - Credentials allowed only for trusted domains
   - Update `ALLOWED_ORIGINS` environment variable

### Data Protection
1. **Encryption**
   - TLS 1.3 for all traffic (enforce HTTPS)
   - Encrypt sensitive data at rest (database encryption)
   - Encrypt PII in Neo4j (if storing sensitive entities)

2. **Data Retention**
   - Conversation history: 90 days (configurable)
   - Usage logs: 1 year (compliance requirement)
   - Deleted user data: permanent deletion within 30 days (GDPR)

3. **Privacy**
   - No audio recordings stored (unless explicitly opted-in)
   - Anonymize analytics data
   - Allow users to delete all memory data
   - Provide data export functionality

### Infrastructure Security
1. **Container Security**
   - Use official base images
   - Scan for vulnerabilities (Trivy, Snyk)
   - Non-root users in containers
   - Read-only file systems where possible

2. **Secrets Management**
   - Never commit secrets to version control
   - Use environment variables (dev) or Vault (production)
   - Rotate API keys quarterly
   - Encrypt secrets at rest

3. **Network Security**
   - Internal service communication over private network
   - Firewall rules to restrict access
   - DDoS protection (Cloudflare or AWS Shield)

### Compliance
1. **GDPR**
   - User consent for data processing
   - Right to access data (memory export)
   - Right to deletion (hard delete from all databases)
   - Data portability (JSON export)

2. **PCI DSS** (via Stripe)
   - Never store payment card data
   - Use Stripe's secure checkout
   - Log payment events for auditing

3. **SOC 2** (future consideration)
   - Audit logging for all sensitive operations
   - Access controls and least privilege
   - Regular security assessments

---

## Testing Strategy

### Unit Tests
- **Backend**: pytest with coverage >80%
  - Auth service functions
  - Memory service functions
  - Tool orchestrator logic
  - Database query methods

- **Frontend**: Jest + React Testing Library
  - Component rendering
  - User interactions
  - State management
  - WebSocket message handling

### Integration Tests
- **API Tests**: pytest with TestClient
  - Authentication flow end-to-end
  - Subscription creation and webhook handling
  - Memory storage and retrieval
  - Tool execution

- **E2E Tests**: Playwright
  - User registration → login → subscribe → use Snappy Plus
  - Voice conversation with tool calling
  - Memory dashboard navigation
  - Subscription cancellation

### Performance Tests
- **Load Testing**: Locust or k6
  - 100 concurrent WebSocket connections
  - 1000 requests/second to API
  - Database query performance under load

- **Stress Testing**
  - Maximum users until degradation
  - Memory leak detection
  - Database connection pool exhaustion

### Security Tests
- **OWASP Top 10**
  - SQL injection attempts
  - XSS payloads
  - CSRF attacks
  - Authentication bypass

- **Penetration Testing**
  - Third-party security audit (optional)
  - Automated scanning with OWASP ZAP

---

## Deployment Strategy

### Development Environment
```yaml
# docker-compose.dev.yml additions
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: snappy
      POSTGRES_USER: snappy
      POSTGRES_PASSWORD: dev_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  neo4j:
    image: neo4j:5-enterprise
    environment:
      NEO4J_AUTH: neo4j/dev_password
      NEO4J_ACCEPT_LICENSE_AGREEMENT: "yes"
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    ports:
      - "7474:7474"  # Browser
      - "7687:7687"  # Bolt

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  celery_worker:
    build: ./backend
    command: celery -A app.tasks worker --loglevel=info
    depends_on:
      - redis
      - neo4j
      - postgres
    environment:
      - REDIS_URL=redis://redis:6379/0
      - NEO4J_URI=bolt://neo4j:7687
      - DATABASE_URL=postgresql://snappy:dev_password@postgres:5432/snappy

volumes:
  postgres_data:
  neo4j_data:
  neo4j_logs:
  redis_data:
```

### Staging Environment
- Deploy on cloud provider (AWS, GCP, or Azure)
- Use managed services:
  - RDS for PostgreSQL
  - Neo4j AuraDB (managed Neo4j)
  - ElastiCache for Redis
  - ECS or GKE for containers
- CI/CD pipeline:
  - GitHub Actions or GitLab CI
  - Automated tests on every PR
  - Deploy to staging on merge to `develop`
  - Manual approval for production

### Production Environment
- **Kubernetes Deployment**
  - Auto-scaling for backend pods (HPA)
  - Load balancer for WebSocket connections (sticky sessions)
  - Persistent volumes for stateful services
  - Secrets via Kubernetes Secrets or Vault

- **Monitoring**
  - Prometheus + Grafana dashboards
  - Alerts for error rates, latency, resource usage
  - OpenTelemetry for distributed tracing

- **Logging**
  - Centralized logging with Loki or ELK stack
  - Structured JSON logs
  - Log retention: 30 days

- **Backups**
  - PostgreSQL: daily automated backups, 30-day retention
  - Neo4j: daily backups to S3/GCS, 30-day retention
  - Disaster recovery plan with RTO < 4 hours

---

## Cost Estimation (Monthly)

### Infrastructure (Assuming 1000 active users, 50% on Snappy Plus)

| Service | Tier | Cost |
|---------|------|------|
| **PostgreSQL** | AWS RDS db.t4g.medium | $40 |
| **Neo4j** | AuraDB Professional (16GB RAM) | $280 |
| **Redis** | ElastiCache t4g.micro | $12 |
| **Backend** | 2 x ECS Fargate (2vCPU, 4GB) | $60 |
| **Frontend** | Vercel Pro | $20 |
| **Existing Services** | Qdrant, MinIO, ColPali (unchanged) | $100 (estimate) |
| **Load Balancer** | AWS ALB | $20 |
| **Monitoring** | Grafana Cloud Free Tier | $0 |
| **Backups** | S3 storage (100GB) | $2 |
| **OpenAI Realtime API** | 500 users × 2 hours/month × $0.06/min | $3,600 |
| **OpenAI Text API** | Existing usage (unchanged) | $200 (estimate) |
| **Stripe Fees** | 500 subs × $20 × 2.9% + $0.30 | $440 |
| **TOTAL** | | **$4,774** |

**Revenue**: 500 Snappy Plus subscribers × $20 = **$10,000**
**Gross Margin**: ~52% (before operating costs)

*Note: OpenAI Realtime API is the largest cost driver. Optimize by implementing push-to-talk, silence detection, and usage limits.*

---

## Success Metrics

### User Metrics
- **Conversion Rate**: Free → Snappy Plus (target: 5%)
- **Churn Rate**: Monthly subscription cancellations (target: <3%)
- **Engagement**: Average sessions per user per week (target: 5+)
- **Session Duration**: Average Snappy Plus session length (target: 10 minutes)

### Technical Metrics
- **Uptime**: 99.9% availability (43 minutes downtime/month max)
- **Latency**: P95 WebSocket message latency <500ms
- **Error Rate**: <0.1% of requests fail
- **Tool Call Success**: >95% successful tool executions

### Business Metrics
- **MRR Growth**: Month-over-month recurring revenue growth (target: 20%)
- **LTV:CAC Ratio**: Lifetime value to customer acquisition cost (target: 3:1)
- **Usage Within Limits**: <5% of users exceed tier limits

---

## Risk Mitigation

### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| OpenAI Realtime API downtime | Medium | High | Implement fallback to text chat, status page monitoring |
| Neo4j performance degradation at scale | Medium | Medium | Regular query optimization, connection pooling, read replicas |
| WebSocket connection instability | High | Medium | Automatic reconnection, exponential backoff, connection pooling |
| Memory extraction inaccuracy | Medium | Low | Fine-tune Graphiti prompts, manual correction UI |

### Business Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Low conversion rate | Medium | High | A/B test pricing, trial period, feature education |
| High OpenAI costs | High | High | Implement usage quotas, push-to-talk, optimize prompts |
| Competitor launches similar feature | Medium | Medium | Focus on UX differentiation, rapid iteration |
| GDPR compliance issues | Low | High | Legal review, privacy-first design, data deletion workflows |

### Operational Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Key developer leaves | Low | Medium | Documentation, knowledge sharing, code reviews |
| Security breach | Low | Critical | Security audits, penetration testing, incident response plan |
| Stripe payment failures | Low | Medium | Retry logic, user notifications, grace period |

---

## Next Steps

1. **Review and Approve**: Stakeholder review of this master plan
2. **Resource Allocation**: Assign developers to Phase 1 tasks
3. **Infrastructure Setup**: Provision development databases (PostgreSQL, Neo4j, Redis)
4. **Kickoff Meeting**: Align team on architecture, timelines, and responsibilities
5. **Begin Phase 1**: Start with authentication foundation

---

## Appendix

### Recommended Reading
- [OpenAI Realtime API Documentation](https://platform.openai.com/docs/guides/realtime)
- [Graphiti Framework Documentation](https://github.com/getzep/graphiti)
- [Neo4j Graph Data Science](https://neo4j.com/docs/graph-data-science/)
- [FastAPI-Users Documentation](https://fastapi-users.github.io/fastapi-users/)
- [NextAuth.js v5 (Auth.js)](https://authjs.dev/)

### Reference Architectures
- [Spotify's Conversational AI Architecture](https://engineering.atspotify.com/2023/10/how-spotify-built-a-conversational-ai-experience/)
- [Stripe Billing Best Practices](https://stripe.com/docs/billing/subscriptions/overview)
- [Neo4j Enterprise Architecture](https://neo4j.com/docs/operations-manual/current/clustering/)

### Code Repositories (Inspiration)
- [OpenAI Realtime Console](https://github.com/openai/openai-realtime-console)
- [Next.js 16 Examples](https://github.com/vercel/next.js/tree/canary/examples)
- [FastAPI-Users Example](https://github.com/fastapi-users/fastapi-users/tree/master/examples)

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Owner**: Snappy Plus Development Team
**Status**: Awaiting Approval
