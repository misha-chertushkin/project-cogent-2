#!/usr/bin/env python3
"""Verbose test script to see all agent events including tool calls."""

import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from app.agent import root_agent


async def main():
    """Run the agent with verbose output."""
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="vendor_analysis", user_id="test_analyst", session_id="demo_session"
    )

    runner = Runner(
        agent=root_agent, app_name="vendor_analysis", session_service=session_service
    )

    query = """Analyze vendors with spend over $100M. For EACH vendor, check contract expiration."""

    print("=" * 70)
    print("VERBOSE AGENT TEST")
    print("=" * 70)

    async for event in runner.run_async(
        user_id="test_analyst",
        session_id="demo_session",
        new_message=genai_types.Content(
            role="user", parts=[genai_types.Part.from_text(text=query)]
        ),
    ):
        print(f"\n[Event from: {event.author}]")

        # Check for function calls (tool use)
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call:
                    print(f"  TOOL CALL: {part.function_call.name}")
                    print(f"  Args: {dict(part.function_call.args)}")
                elif part.function_response:
                    print(f"  TOOL RESPONSE: {part.function_response.name}")
                    response_text = str(part.function_response.response)
                    print(f"  Result: {response_text[:200]}...")
                elif part.text:
                    print(f"  Text: {part.text[:200]}...")

        if event.is_final_response():
            print("\n" + "=" * 70)
            print("FINAL RESPONSE:")
            print("=" * 70)
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text)

    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
