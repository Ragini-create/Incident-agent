# triage-agent-graph Specification

## Purpose
Provides core state graph execution, system prompt reasoning, service health diagnostics, and runbook retrieval for autonomous incident triage.

## Requirements

### Requirement: Agent State & Systematic Diagnostic Prompting
The agent state graph SHALL manage conversation state (`messages`) and follow system prompt guidelines: inspect affected component health first, query remediation runbooks second, and synthesize findings into clear recommendations.

#### Scenario: Agent processes incident description
- **WHEN** an incident description is provided to the agent state graph
- **THEN** the model invokes diagnostic tools in systematic order and outputs a final diagnosis

### Requirement: Safe Service Health Inspection Tool
The system SHALL provide a `query_service_health` tool that accepts a service name and returns metrics or status strings for key microservices (`auth`, `database`, `payments`).

#### Scenario: Querying health for known service
- **WHEN** `query_service_health` is invoked with service_name "auth"
- **THEN** the tool returns the current status and metrics for the auth service

#### Scenario: Querying health for unknown service
- **WHEN** `query_service_health` is invoked with an unrecognised service name
- **THEN** the tool returns a descriptive "Service not found" response

### Requirement: Safe Runbook Retrieval Tool Integration
The system SHALL provide a `search_remediation_runbooks` tool that embeds query text using Gemini embeddings and searches `incident_docs` in Supabase pgvector for matching runbook content.

#### Scenario: Querying runbooks for matching alert
- **WHEN** `search_remediation_runbooks` is invoked with a query string
- **THEN** the tool performs vector similarity search and returns formatted runbook snippets

### Requirement: Safe Tool Routing and Graph Execution
The state graph SHALL route tool call requests from the model node to the safe tools execution node (`safe_tools`) and pass tool output back to the model node until generation reaches `__end__`.

#### Scenario: Safe tool invocation loop
- **WHEN** model output includes a tool call to `query_service_health` or `search_remediation_runbooks`
- **THEN** the router directs execution to `safe_tools`, executes the tool, and routes output back to the agent node
