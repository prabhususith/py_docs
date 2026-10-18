r"""
Autonomous Agent Orchestration: ReAct Loop, Tool Registry, and Multi-Step Execution
===================================================================================
Description: Production autonomous agent architecture implementing the ReAct
             (Reasoning + Acting) execution paradigm. Features a strongly typed tool registry
             with Pydantic v2 argument validation, autonomous step-by-step decision loops
             (Thought -> Action -> Action Input -> Observation -> Final Answer), recursion limits,
             and multi-hop execution across databases and external API tools.
Enterprise Mapping:
- ReAct Loop: Core agentic pattern in LangChain, LangGraph, CrewAI, and AutoGen.
  Decouples the reasoning engine from deterministic tool execution, replacing hard-coded
  procedural scripts with dynamic, goal-driven autonomy.
- Tool Registry: Analogous to OpenAPI / JSON Schema function definitions in OpenAI / Anthropic
  tool-calling APIs. Enforces strict input validation before executing database or network side-effects.
- Circuit Breaker / Recursion Limits: Protects cloud infrastructure against runaway token costs
  and infinite agent reasoning loops.

Official Documentation References:
- LangChain Custom Tools: https://python.langchain.com/docs/how_to/custom_tools/
- ReAct (Reasoning and Acting) Research Paper: https://arxiv.org/abs/2210.03629
- Tool Calling Concepts: https://python.langchain.com/docs/concepts/tool_calling/
- Pydantic Validation in Tools: https://docs.pydantic.dev/latest/concepts/models/
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
import re
from typing import Any, Callable, Coroutine, Final, NamedTuple

from pydantic import BaseModel, Field, ValidationError


# ==============================================================================
# 1. Tool Contracts and Typed Registry
# ==============================================================================
class ToolResult(NamedTuple):
    success: bool
    output: Any
    error: str | None = None


class BaseToolSchema(BaseModel):
    """Base schema for tool arguments."""
    pass


class QueryCustomerDatabaseInput(BaseToolSchema):
    customer_id: str = Field(..., description="Unique alphanumeric customer identifier", examples=["CUST-402"])


class CheckCreditRiskApiInput(BaseToolSchema):
    credit_score: int = Field(..., ge=300, le=850, description="FICO/Equifax credit score index")
    requested_loan_amount: float = Field(..., gt=0.0, description="Requested loan amount in USD")


class AutonomousTool:
    """Encapsulates a typed tool with schema validation and execution callable."""

    def __init__(
        self,
        name: str,
        description: str,
        args_schema: type[BaseModel],
        handler: Callable[..., Coroutine[Any, Any, ToolResult]],
    ) -> None:
        self.name: str = name
        self.description: str = description
        self.args_schema: type[BaseModel] = args_schema
        self.handler: Callable[..., Coroutine[Any, Any, ToolResult]] = handler

    async def execute(self, raw_input_kwargs: dict[str, Any]) -> ToolResult:
        """Validate input parameters against Pydantic schema before invocation."""
        try:
            validated_args = self.args_schema.model_validate(raw_input_kwargs)
            return await self.handler(**validated_args.model_dump())
        except ValidationError as val_err:
            return ToolResult(success=False, output=None, error=f"Schema validation failed: {val_err}")
        except Exception as exc:
            return ToolResult(success=False, output=None, error=f"Execution error: {exc}")


class ToolRegistry:
    """Central repository managing available agent tools."""

    def __init__(self) -> None:
        self._tools: dict[str, AutonomousTool] = {}

    def register(self, tool: AutonomousTool) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> AutonomousTool | None:
        return self._tools.get(name)

    def describe_tools(self) -> str:
        """Format tools description for LLM prompt context."""
        descriptions = []
        for t in self._tools.values():
            schema_json = json.dumps(t.args_schema.model_json_schema()["properties"])
            descriptions.append(f"- Tool: `{t.name}`: {t.description}\n  Schema: {schema_json}")
        return "\n".join(descriptions)


# ==============================================================================
# 2. Mock Production Tools (Database & External Credit API)
# ==============================================================================
# Mock database records
_MOCK_CUSTOMER_DB: Final[dict[str, dict[str, Any]]] = {
    "CUST-402": {
        "name": "Evelyn Vance",
        "account_standing": "ACTIVE_GOOD",
        "credit_score": 785,
        "existing_debt": 4200.00,
        "annual_income": 145000.00,
    },
    "CUST-901": {
        "name": "Marcus Kane",
        "account_standing": "SUSPENDED",
        "credit_score": 520,
        "existing_debt": 89000.00,
        "annual_income": 35000.00,
    },
}


async def tool_query_customer_db(customer_id: str) -> ToolResult:
    """Tool: Queries internal core banking database."""
    await asyncio.sleep(0.01)  # Simulate DB latency
    record = _MOCK_CUSTOMER_DB.get(customer_id.upper())
    if not record:
        return ToolResult(success=False, output=None, error=f"Customer ID '{customer_id}' not found.")
    return ToolResult(success=True, output=record)


async def tool_check_credit_risk_api(credit_score: int, requested_loan_amount: float) -> ToolResult:
    """Tool: Evaluates credit risk using external underwriting scoring engine."""
    await asyncio.sleep(0.01)  # Simulate network API latency
    if credit_score >= 720:
        risk_rating = "LOW_RISK"
        max_approved = requested_loan_amount
        approved = True
    elif credit_score >= 620:
        risk_rating = "MODERATE_RISK"
        max_approved = requested_loan_amount * 0.75
        approved = True
    else:
        risk_rating = "HIGH_RISK"
        max_approved = 0.0
        approved = False

    return ToolResult(
        success=True,
        output={
            "risk_rating": risk_rating,
            "approved": approved,
            "max_approved_amount": max_approved,
            "underwriting_verdict": "RECOMMENDED" if approved else "DECLINED",
        },
    )


# ==============================================================================
# 3. Autonomous ReAct Agent Loop Engine
# ==============================================================================
class AgentStep(NamedTuple):
    thought: str
    action: str
    action_input: dict[str, Any]
    observation: str


class AutonomousReActAgent:
    """
    Autonomous ReAct Agent executing multi-step goals.
    Maintains memory of reasoning steps and enforces loop safety limits.
    """

    def __init__(self, registry: ToolRegistry, max_iterations: int = 5) -> None:
        self.registry: ToolRegistry = registry
        self.max_iterations: int = max_iterations

    async def execute_goal(self, goal: str) -> str:
        """
        Execute ReAct loop:
        Repeats: Thought -> Action -> Action Input -> Observation
        Until agent reaches 'Final Answer:' or exhausts iteration limit.
        """
        print(f"\n[Agent Initialized] Goal: '{goal}'")
        history: list[AgentStep] = []
        iteration = 0

        # Deterministic simulation of ReAct multi-step reasoning
        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n--- ReAct Cycle #{iteration} ---")

            # 1. Step Decision Engine (Simulates LLM next-step prediction based on history)
            thought, action, action_input = self._simulate_llm_reasoning_step(goal, history)

            print(f"Thought: {thought}")

            # Check for terminal condition
            if action == "FINAL_ANSWER":
                final_answer = str(action_input.get("answer", ""))
                print(f"\n[Agent Completed Goal]\nFinal Answer:\n{final_answer}")
                return final_answer

            print(f"Action: {action}")
            print(f"Action Input: {json.dumps(action_input)}")

            # 2. Tool Lookup & Execution
            tool = self.registry.get_tool(action)
            if not tool:
                obs = f"Error: Tool '{action}' is not registered."
            else:
                tool_res = await tool.execute(action_input)
                obs = json.dumps(tool_res.output) if tool_res.success else f"Error: {tool_res.error}"

            print(f"Observation: {obs}")

            # 3. Append to step history
            history.append(
                AgentStep(
                    thought=thought,
                    action=action,
                    action_input=action_input,
                    observation=obs,
                )
            )

        raise RuntimeError(f"Agent reached maximum iteration limit ({self.max_iterations}) without terminal answer.")

    def _simulate_llm_reasoning_step(
        self, goal: str, history: list[AgentStep]
    ) -> tuple[str, str, dict[str, Any]]:
        """Simulate LLM deciding next action based on prior observations."""
        if not history:
            return (
                "To evaluate the loan application, I first need to retrieve the customer's financial profile from the database.",
                "query_customer_database",
                {"customer_id": "CUST-402"},
            )

        if len(history) == 1:
            # First tool returned customer profile
            obs_data = json.loads(history[0].observation)
            credit_score = obs_data["credit_score"]
            return (
                f"Customer record acquired: {obs_data['name']} has credit score {credit_score}. "
                f"I now need to submit this score to the credit risk API for a $50,000 loan request.",
                "check_credit_risk_api",
                {"credit_score": credit_score, "requested_loan_amount": 50000.0},
            )

        if len(history) == 2:
            # Second tool returned risk rating
            risk_data = json.loads(history[1].observation)
            cust_data = json.loads(history[0].observation)
            return (
                "Both database profile and underwriting risk calculations have been acquired. "
                "I am ready to synthesize the final decision.",
                "FINAL_ANSWER",
                {
                    "answer": (
                        f"Loan Assessment for {cust_data['name']} (ID: CUST-402):\n"
                        f"- Credit Score: {cust_data['credit_score']} ({risk_data['risk_rating']})\n"
                        f"- Verdict: {risk_data['underwriting_verdict']}\n"
                        f"- Approved Amount: ${risk_data['max_approved_amount']:,.2f}\n"
                        f"- Annual Income: ${cust_data['annual_income']:,.2f}"
                    )
                },
            )

        return ("Loop fallback.", "FINAL_ANSWER", {"answer": "Completed."})


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite
# ==============================================================================
async def main() -> None:
    print("=" * 70)
    print(" LEVEL 5: 04_AUTONOMOUS_AGENT_TOOL_CALLING - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    # 1. Setup Tool Registry
    registry = ToolRegistry()
    registry.register(
        AutonomousTool(
            name="query_customer_database",
            description="Query banking database for account standing, credit score, and income.",
            args_schema=QueryCustomerDatabaseInput,
            handler=tool_query_customer_db,
        )
    )
    registry.register(
        AutonomousTool(
            name="check_credit_risk_api",
            description="Evaluate credit risk and determine maximum approved loan threshold.",
            args_schema=CheckCreditRiskApiInput,
            handler=tool_check_credit_risk_api,
        )
    )

    print("\n--- 1. Registered Tools Specification ---")
    print(registry.describe_tools())

    # 2. Schema Validation Test on Tool
    print("\n--- 2. Tool Pydantic Schema Validation Guard ---")
    bad_tool = registry.get_tool("check_credit_risk_api")
    assert bad_tool is not None
    # Invalid credit score (exceeds max 850)
    invalid_result = await bad_tool.execute({"credit_score": 9999, "requested_loan_amount": 1000.0})
    print(f"  Handled Invalid Input: {invalid_result.error}")
    assert invalid_result.success is False
    assert "Schema validation failed" in str(invalid_result.error)

    # 3. Autonomous Multi-Step Execution
    print("\n--- 3. Autonomous Multi-Step ReAct Execution ---")
    agent = AutonomousReActAgent(registry=registry, max_iterations=5)
    final_result = await agent.execute_goal("Assess loan eligibility for customer CUST-402 requesting $50,000")

    assert "Evelyn Vance" in final_result
    assert "LOW_RISK" in final_result
    assert "$50,000.00" in final_result
    assert "RECOMMENDED" in final_result

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 04_autonomous_agent_tool_calling module executed cleanly.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
