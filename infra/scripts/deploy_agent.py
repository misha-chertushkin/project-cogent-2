import vertexai
from vertexai.preview import reasoning_engines
from app.agent import vendor_compliance_agent 
from app import config

def deploy():
    # Initialize Vertex AI with your config values
    vertexai.init(project=config.PROJECT_ID, location=config.LOCATION)

    # The requirements must match what's in your pyproject.toml/requirements.txt
    # for the Reasoning Engine to recreate the environment correctly.
    remote_agent = reasoning_engines.ReasoningEngine.create(
        vendor_compliance_agent(
            project_id=config.PROJECT_ID,
            dataset_id=config.BIGQUERY_DATASET_ID,
            datastore_id=config.DATASTORE_ID
        ),
        requirements=[
            "google-cloud-aiplatform[reasoningengine,langchain]",
            "google-cloud-bigquery",
            "google-cloud-discoveryengine",
            "pydantic>=2.0.0"
        ],
        display_name="Vendor Spend Compliance Agent",
        description="Analyzes BQ spend and VAIS contracts to detect discrepancies like the Apex Trap.",
    )
    
    print(f"\n✅ Deployment Successful!")
    print(f"Resource Name: {remote_agent.resource_name}")

if __name__ == "__main__":
    deploy()