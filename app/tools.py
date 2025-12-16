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

"""Tools for the Vendor Spend Analysis Agent with Hybrid Search."""

import logging

logger = logging.getLogger(__name__)


def search_documents(
    search_query: str,
    max_results: int = 5,
) -> str:
    """
    Search documents using Vertex AI Search.

    This is a generic document search tool that queries the Vertex AI Search datastore
    for relevant information. It can be used to find information in any documents
    indexed in the datastore (e.g., contracts, policies, reports).

    Args:
        search_query: The search query to execute (e.g., "Acme Corp indemnification",
                     "termination date December 2024", "insurance requirements")
        max_results: Maximum number of results to return (default: 5)

    Returns:
        str: Formatted search results with document excerpts and snippets
    """
    from google.api_core.client_options import ClientOptions
    from google.cloud import discoveryengine_v1 as discoveryengine
    from app.config import DATA_STORE_REGION, VERTEX_AI_SEARCH_DATASTORE

    logger.info(f"Searching documents: {search_query}")

    try:
        client_options = ClientOptions(
            api_endpoint=f"{DATA_STORE_REGION}-discoveryengine.googleapis.com"
        )
        client = discoveryengine.SearchServiceClient(client_options=client_options)

        # Use the datastore directly (not an engine)
        serving_config = f"{VERTEX_AI_SEARCH_DATASTORE}/servingConfigs/default_config"

        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=search_query,
            page_size=max_results,
        )

        response = client.search(request)

        results = list(response.results)
        if not results:
            return f"No documents found matching: {search_query}"

        output_lines = [f"Document search results for: {search_query}\n"]

        for result in results:
            doc = result.document
            doc_id = doc.id if hasattr(doc, 'id') else 'unknown'
            output_lines.append(f"\nDocument: {doc_id}")

            # Extract snippets from derived_struct_data
            if hasattr(doc, 'derived_struct_data') and doc.derived_struct_data:
                derived = doc.derived_struct_data

                # Try to get extractive answers
                if 'extractive_answers' in derived:
                    for answer in derived['extractive_answers']:
                        content = answer.get('content', '')
                        if content:
                            output_lines.append(f"  {content}")

                # Try to get snippets
                elif 'snippets' in derived:
                    for snippet in derived['snippets']:
                        snippet_text = snippet.get('snippet', '')
                        if snippet_text:
                            output_lines.append(f"  {snippet_text}")

                # Fallback: show raw derived data preview
                else:
                    preview = str(derived)[:300]
                    output_lines.append(f"  Content: {preview}...")

        return "\n".join(output_lines)

    except Exception as e:
        error_msg = f"Error searching documents: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg
