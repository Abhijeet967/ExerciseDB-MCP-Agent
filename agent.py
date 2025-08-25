from uagents import Agent
from uagents_adapter import MCPServerAdapter
from server import mcp  # Import the FastMCP server instance from server.py
import os
load_dotenv()

# Create an MCP adapter with your ExerciseDB MCP server
mcp_adapter = MCPServerAdapter(
    mcp_server=mcp,  # (FastMCP) Your ExerciseDB MCP server instance
    asi1_api_key= os.getenv("ASI1_API_KEY"),  # (str) Your ASI:One API key
    model="asi1-mini"  # (str) Model to use: "asi1-mini", "asi1-extended", or "asi1-fast"
)

# Create a uAgent
agent = Agent()

# Include protocols from the adapter
for protocol in mcp_adapter.protocols:
    agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    # Run the MCP adapter with the agent
    mcp_adapter.run(agent)