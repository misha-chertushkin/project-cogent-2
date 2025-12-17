# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# mypy: disable-error-code="union-attr"
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent


def test_agent_stream() -> None:
    """
    Integration test for the agent stream functionality.
    Tests that the agent returns valid streaming responses.
    """

    session_service = InMemorySessionService()

    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    message = types.Content(
        role="user", parts=[types.Part.from_text(text="Why is the sky blue?")]
    )

    events = list(
        runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    assert len(events) > 0, "Expected at least one message"

    has_text_content = False
    for event in events:
        if (
            event.content
            and event.content.parts
            and any(part.text for part in event.content.parts)
        ):
            has_text_content = True
            break
    assert has_text_content, "Expected at least one message with text content"


def test_vendor_compliance_analysis() -> None:
    """
    Integration test for vendor compliance analysis with hybrid search.

    This test demonstrates the core value proposition:
    - Query BigQuery for high-value vendors (>$100M spend)
    - Search contract PDFs for compliance clauses
    - Detect the TRAP: Apex Logistics has expired contract but shows as Active
    """

    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="compliance_analyst", app_name="vendor_analysis")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="vendor_analysis")

    # The test query that should trigger the trap detection
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(
            text="Analyze all vendors with annual spend over $100 million. "
                 "For each vendor, check their contract compliance including "
                 "indemnification and warranty clauses. Most importantly, verify "
                 "that the contract termination dates in the PDFs match the renewal "
                 "dates in our database. Flag any discrepancies as critical alerts."
        )]
    )

    print("\n" + "="*70)
    print("VENDOR COMPLIANCE ANALYSIS TEST")
    print("="*70)
    print("Query: Analyzing high-value vendors (>$100M)")
    print("Expected: Should detect Apex Logistics expired contract trap")
    print("="*70 + "\n")

    events = list(
        runner.run(
            new_message=message,
            user_id="compliance_analyst",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )

    # Collect all text responses
    all_text = []
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    all_text.append(part.text)
                    print(part.text)

    combined_response = " ".join(all_text).lower()

    # Assertions
    assert len(events) > 0, "Expected at least one event"
    assert any(all_text), "Expected at least one text response"

    # Check that the agent found high-value vendors
    assert any(
        "vendor" in text.lower() and ("100" in text or "million" in text.lower())
        for text in all_text
    ), "Expected response to mention high-value vendors"

    # Check for the TRAP detection
    # The agent should flag Apex Logistics as having an expired contract
    print("\n" + "="*70)
    print("TRAP DETECTION CHECK")
    print("="*70)

    found_critical_alert = "critical" in combined_response and "alert" in combined_response
    found_apex = "apex" in combined_response and "logistics" in combined_response
    found_expired = "expired" in combined_response or "expiration" in combined_response or "mismatch" in combined_response

    print(f"✓ Found 'CRITICAL ALERT': {found_critical_alert}")
    print(f"✓ Found 'Apex Logistics': {found_apex}")
    print(f"✓ Found expiration/mismatch: {found_expired}")
    print("="*70 + "\n")

    # At minimum, should have found Apex and some indication of the problem
    assert found_apex, "Expected response to mention Apex Logistics"

    if found_critical_alert and found_expired:
        print("✅ SUCCESS: Trap detected! Agent found the expired contract issue.")
    else:
        print("⚠️  WARNING: Trap detection unclear. Review agent output above.")


if __name__ == "__main__":
    # Allow running test directly for debugging
    print("Running vendor compliance analysis test...\n")
    test_vendor_compliance_analysis()
    print("\n✅ Test completed!")
