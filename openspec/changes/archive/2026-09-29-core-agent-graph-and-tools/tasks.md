# Tasks

## 1. Agent Graph Node & Safe Tools Refactoring

- [x] 1.1 Verify and refine `agent.py` state graph nodes (`agent`, `safe_tools`), systematic system prompt, safe tool definitions (`query_service_health`, `search_remediation_runbooks`), and content extraction helper (`extract_text`). Verify graph structure compiles correctly.

## 2. Agent Graph Unit & Tool Routing Testing

- [x] 2.1 Create `tests/test_agent_graph.py` containing unit tests with mocked LLM responses, verifying direct answer graph routing, health check tool routing, and runbook search tool execution offline via `python -m unittest tests/test_agent_graph.py`.
