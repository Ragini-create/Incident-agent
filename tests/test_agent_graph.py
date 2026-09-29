import unittest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, SystemMessage

from agent import (
    extract_text,
    query_service_health,
    route_tools,
    workflow,
    AgentState,
    END,
)


class TestAgentGraphAndTools(unittest.TestCase):

    def test_extract_text_utility(self):
        self.assertEqual(extract_text("Flat string"), "Flat string")
        self.assertEqual(
            extract_text([{"text": "Hello "}, {"text": "World"}]),
            "Hello World"
        )
        self.assertEqual(extract_text(None), "")

    def test_query_service_health_known_services(self):
        auth_status = query_service_health.invoke({"service_name": "auth"})
        self.assertIn("Auth Service: DEGRADED", auth_status)

        db_status = query_service_health.invoke({"service_name": "database"})
        self.assertIn("Primary Postgres: HEALTHY", db_status)

        payment_status = query_service_health.invoke({"service_name": "payments"})
        self.assertIn("Stripe Gateway: HEALTHY", payment_status)

    def test_query_service_health_unknown_service(self):
        unknown_status = query_service_health.invoke({"service_name": "unknown_microservice"})
        self.assertIn("Service 'unknown_microservice' not found", unknown_status)

    def test_route_tools_end(self):
        state: AgentState = {
            "messages": [HumanMessage(content="Hello"), AIMessage(content="How can I help?")]
        }
        self.assertEqual(route_tools(state), END)

    def test_route_tools_safe_tools(self):
        msg = AIMessage(
            content="",
            tool_calls=[{"name": "query_service_health", "args": {"service_name": "auth"}, "id": "call_1"}]
        )
        state: AgentState = {"messages": [msg]}
        self.assertEqual(route_tools(state), "safe_tools")

    def test_route_tools_sensitive_tools(self):
        msg = AIMessage(
            content="",
            tool_calls=[{"name": "escalate_ticket", "args": {"ticket_title": "Auth outage", "severity": "HIGH"}, "id": "call_2"}]
        )
        state: AgentState = {"messages": [msg]}
        self.assertEqual(route_tools(state), "sensitive_tools")

    @patch("agent.llm")
    def test_uncheckpointed_graph_execution_direct_response(self, mock_llm):
        mock_llm.invoke.return_value = AIMessage(content="Auth service is operational.")

        app = workflow.compile()
        inputs = {"messages": [HumanMessage(content="What is auth status?")]}
        output = app.invoke(inputs)

        messages = output["messages"]
        self.assertTrue(len(messages) >= 2)
        self.assertEqual(messages[-1].content, "Auth service is operational.")
        mock_llm.invoke.assert_called_once()

    @patch("agent.llm")
    def test_uncheckpointed_graph_execution_with_safe_tool(self, mock_llm):
        # Step 1: Model requests tool call to query_service_health
        tool_call_msg = AIMessage(
            content="",
            tool_calls=[{"name": "query_service_health", "args": {"service_name": "auth"}, "id": "call_auth_1"}]
        )
        # Step 2: Model returns final diagnosis after tool output
        final_msg = AIMessage(content="Auth service is DEGRADED due to token refresh latency.")

        mock_llm.invoke.side_effect = [tool_call_msg, final_msg]

        app = workflow.compile()
        inputs = {"messages": [HumanMessage(content="Check auth service latency")]}
        output = app.invoke(inputs)

        messages = output["messages"]
        self.assertGreaterEqual(len(messages), 3)

        # Check tool message was injected
        tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
        self.assertEqual(len(tool_msgs), 1)
        self.assertIn("Auth Service: DEGRADED", tool_msgs[0].content)

        # Final message content check
        self.assertEqual(messages[-1].content, "Auth service is DEGRADED due to token refresh latency.")


if __name__ == "__main__":
    unittest.main()
