r"""
LLM Orchestration: Prompt Templates, Server-Sent Events (SSE) Streaming, and Structured Outputs
================================================================================================
Description: Production LLM orchestration engine matching LangChain / LlamaIndex architectural
             standards. Demonstrates dynamic prompt templating with variable substitution,
             role-based message hierarchies (System, Human, AI), token-by-token Server-Sent Events
             (SSE) streaming generators, and guaranteed structured output extraction via Pydantic v2.
Enterprise Mapping:
- Prompt Templates: Replaces raw string concatenation or template literals (`${var}`) with
  reusable, parameterized prompt structures with validation guards. Directly matches LangChain.js
  `ChatPromptTemplate` and Vercel AI SDK templates in TypeScript.
- Server-Sent Events (SSE) Streaming: Asynchronous generator yields formatted event stream chunks
  (`data: {"token": "..."}\n\n`), feeding real-time typewriter UI in React/Vue/Angular frontend apps.
- Structured Output Parsing: Enforces strict JSON Schema compliance via Pydantic v2, transforming
  unstructured LLM completions into type-safe enterprise data contracts. Analogous to Zod schema
  parsing in TypeScript AI workflows.

Official Documentation References:
- LangChain Official Overview: https://python.langchain.com/docs/introduction/
- Prompt Templates: https://python.langchain.com/docs/concepts/prompt_templates/
- Structured Outputs: https://python.langchain.com/docs/how_to/structured_output/
- Server-Sent Events (W3C Standard): https://html.spec.whatwg.org/multipage/server-sent-events.html
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
import re
from typing import Any, AsyncGenerator, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


# ==============================================================================
# 1. Structured Output Enterprise Schema (Pydantic v2)
# ==============================================================================
class IncidentAnalysisReport(BaseModel):
    """
    Enterprise Data Contract extracted from unstructured LLM output.
    Guaranteed type-safe by Pydantic v2 runtime compilation.
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    incident_id: str = Field(..., description="Unique enterprise incident tracker identifier (e.g. INC-8921)")
    severity: Literal["SEV1_CRITICAL", "SEV2_MAJOR", "SEV3_MINOR"] = Field(
        ..., description="Standardized severity classification"
    )
    affected_components: list[str] = Field(
        ..., min_length=1, description="List of affected microservices, databases, or infrastructure units"
    )
    root_cause_summary: str = Field(
        ..., min_length=10, description="Concise technical explanation of fault origin"
    )
    remediation_steps: list[str] = Field(
        ..., min_length=1, description="Sequential corrective actions required for resolution"
    )
    estimated_rto_minutes: int = Field(
        default=60, ge=1, le=10080, description="Estimated Recovery Time Objective in minutes"
    )


# ==============================================================================
# 2. Dynamic Prompt Template Engine
# ==============================================================================
class MessageRole:
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatPromptTemplate:
    """
    Parameter-driven prompt template supporting system instructions,
    few-shot examples, and contextual slot filling.
    """

    def __init__(self, system_instruction: str, user_template: str) -> None:
        self.system_instruction: str = system_instruction.strip()
        self.user_template: str = user_template.strip()

    def format_messages(self, **kwargs: Any) -> list[ChatMessage]:
        """Interpolate variables into message sequence with missing-key validation."""
        # Find expected template parameters: {param_name}
        required_vars = set(re.findall(r"\{(\w+)\}", self.user_template))
        missing = required_vars - kwargs.keys()
        if missing:
            raise KeyError(f"Missing required prompt template parameters: {missing}")

        formatted_user = self.user_template.format(**kwargs)

        return [
            ChatMessage(role=MessageRole.SYSTEM, content=self.system_instruction),
            ChatMessage(role=MessageRole.USER, content=formatted_user),
        ]


# ==============================================================================
# 3. Enterprise LLM Orchestrator & SSE Token Streaming
# ==============================================================================
class LLMOrchestrationService:
    """
    LangChain-style LLM Client coordinating prompt formatting, token streaming,
    and structured output extraction. Features an integrated high-fidelity model
    runtime for deterministic, self-contained offline execution.
    """

    def __init__(self, model_name: str = "enterprise-gpt-4o") -> None:
        self.model_name: str = model_name

    async def stream_tokens(
        self, messages: list[ChatMessage], simulate_latency_sec: float = 0.01
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronous generator yielding Server-Sent Events (SSE) data chunks.
        Formats: `data: {"token": "...", "model": "..."}\n\n`
        """
        # Synthesize model completion based on user input
        user_msg = next((m.content for m in messages if m.role == MessageRole.USER), "")
        simulated_response = (
            f"Analysis of telemetry: Detected database deadlock on primary cluster. "
            f"Downstream service latency spiked to 2400ms. Automated circuit breaker tripped successfully."
        )

        # Stream individual word tokens
        tokens = re.findall(r"\S+|\s+", simulated_response)
        for token in tokens:
            await asyncio.sleep(simulate_latency_sec)
            sse_payload = {
                "token": token,
                "model": self.model_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            yield f"data: {json.dumps(sse_payload)}\n\n"

        # Signal completion
        yield "data: [DONE]\n\n"

    async def generate_structured_output(
        self, messages: list[ChatMessage], schema: type[IncidentAnalysisReport]
    ) -> IncidentAnalysisReport:
        """
        Invoke LLM with JSON schema enforcement, validating and parsing raw JSON
        into strong Pydantic v2 DTOs.
        """
        # In production, pass schema.model_json_schema() via tool_choice/response_format
        simulated_json = {
            "incident_id": "INC-9941",
            "severity": "SEV1_CRITICAL",
            "affected_components": [
                "billing-service",
                "payment-gateway-adapter",
                "postgres-primary",
            ],
            "root_cause_summary": "Exhaustion of database connection pool due to un-indexed query lock contention.",
            "remediation_steps": [
                "Execute emergency connection pool expansion (max_connections = 500)",
                "Deploy hotfix index on orders(user_id, status)",
                "Cycle unresponsive payment-gateway replicas",
            ],
            "estimated_rto_minutes": 25,
        }

        raw_json_str = json.dumps(simulated_json)

        # Enforce validation contract
        try:
            parsed_instance = schema.model_validate_json(raw_json_str)
            return parsed_instance
        except ValidationError as err:
            print(f"  [CRITICAL] LLM output failed schema contract: {err}")
            raise


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite
# ==============================================================================
async def main() -> None:
    print("=" * 70)
    print(" LEVEL 5: 03_LLM_ORCHESTRATION_LANGCHAIN - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    # 1. Prompt Template Compilation
    print("\n--- 1. Prompt Template Compilation ---")
    system_inst = "You are an Enterprise Site Reliability Engineer. Output analysis in structured format."
    user_tmpl = (
        "Analyze high-severity outage on cluster '{cluster_name}' affecting region '{region}'. "
        "Alert details: {alert_payload}"
    )
    prompt = ChatPromptTemplate(system_instruction=system_inst, user_template=user_tmpl)

    messages = prompt.format_messages(
        cluster_name="k8s-prod-us-east-1",
        region="us-east-1",
        alert_payload="504 Gateway Timeout spike > 20%",
    )
    print(f"  Compiled {len(messages)} role-based chat messages:")
    for msg in messages:
        print(f"    [{msg.role.upper()}]: {msg.content}")
    assert len(messages) == 2
    assert "k8s-prod-us-east-1" in messages[1].content

    # 2. Server-Sent Events (SSE) Streaming
    print("\n--- 2. Server-Sent Events (SSE) Token Streaming ---")
    orchestrator = LLMOrchestrationService(model_name="enterprise-gpt-4o")
    streamed_tokens: list[str] = []

    print("  Streaming Tokens: ", end="", flush=True)
    async for sse_chunk in orchestrator.stream_tokens(messages, simulate_latency_sec=0.005):
        if "[DONE]" in sse_chunk:
            print(" [STREAM_CLOSED]")
            break
        # Parse SSE data frame
        line = sse_chunk.strip()
        if line.startswith("data: "):
            chunk_data = json.loads(line[6:])
            tok = chunk_data["token"]
            streamed_tokens.append(tok)
            print(tok, end="", flush=True)

    assert len(streamed_tokens) > 5
    print(f"\n  [PASS] Streamed {len(streamed_tokens)} tokens via standard SSE protocol.")

    # 3. Pydantic v2 Structured Output Parsing
    print("\n--- 3. Pydantic v2 Structured Output Parsing ---")
    structured_report = await orchestrator.generate_structured_output(
        messages=messages, schema=IncidentAnalysisReport
    )

    print(f"  Incident ID:           {structured_report.incident_id}")
    print(f"  Severity:              {structured_report.severity}")
    print(f"  Affected Units:        {', '.join(structured_report.affected_components)}")
    print(f"  Root Cause Summary:    {structured_report.root_cause_summary}")
    print(f"  Remediation Actions:   {len(structured_report.remediation_steps)} steps defined")
    print(f"  Estimated RTO:         {structured_report.estimated_rto_minutes} minutes")

    assert structured_report.incident_id == "INC-9941"
    assert structured_report.severity == "SEV1_CRITICAL"
    assert len(structured_report.remediation_steps) == 3

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 03_llm_orchestration_langchain module executed cleanly.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
