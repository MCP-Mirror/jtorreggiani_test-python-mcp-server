import pytest
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import ListResourcesResult, TextContent, TextResourceContents
from pydantic import AnyUrl


test_dir = os.path.dirname(os.path.abspath(__file__))

@pytest.mark.asyncio(loop_scope='function')
async def test_client_server_interactions():
    """Fixture that starts the actual server and provides a connected session"""
    server_params = StdioServerParameters(
        command=f"{test_dir}/server.py",
        args=[],
        env=None
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            list_resources_result = await session.list_resources()
            assert list_resources_result == ListResourcesResult(nextCursor=None, resources=[])

            list_tools_result = await session.list_tools()
            assert list_tools_result.tools[0].name == 'add-note'

            get_prompt_result = await session.get_prompt(name="summarize-notes")
            assert get_prompt_result.description == "Summarize the current notes"

            list_prompts_result = await session.list_prompts()
            assert list_prompts_result.prompts[0].name == 'summarize-notes'

            call_tool_result = await session.call_tool("add-note", arguments={
                "name": "example_note",
                "content": "Example content"
            })

            tool_content = call_tool_result.content[0]
            if isinstance(tool_content, TextContent):
                assert tool_content.text == "Added note 'example_note' with content: Example content"

            list_resources_result = await session.list_resources()
            resource_uri = list_resources_result.resources[0].uri
            assert resource_uri == AnyUrl("note://internal/example_note")

            read_resource_result = await session.read_resource(resource_uri)
            if isinstance(read_resource_result.contents[0], TextResourceContents):
                assert read_resource_result.contents[0].text== 'Example content'