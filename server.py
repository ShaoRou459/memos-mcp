"""MCP Server for Memos - Provides access to Memos via Model Context Protocol."""

import asyncio
import json
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from dateutil.parser import parse as parse_date

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from mcp.server.models import InitializationOptions

from config import get_config, validate_config
from memos_client import MemosClient, MemosAPIError


# Initialize configuration
config = get_config()

# Create FastMCP server
mcp = FastMCP("memos-server")

# Global client instance
_client: Optional[MemosClient] = None


async def get_client() -> MemosClient:
    """Get or create Memos client instance."""
    global _client
    if _client is None:
        _client = MemosClient(config)
    return _client


def format_memo_for_display(memo: Dict[str, Any]) -> str:
    """Format memo data for readable display."""
    content = memo.get("content", "")
    created_time = memo.get("createTime", "")
    name = memo.get("name", "")
    visibility = memo.get("visibility", "")
    
    # Parse creation time for better formatting
    try:
        if created_time:
            dt = parse_date(created_time)
            created_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            created_str = "Unknown"
    except:
        created_str = created_time
    
    return f"""**Memo ID**: {name}
**Created**: {created_str}
**Visibility**: {visibility}
**Content**:
{content}

---"""


# TOOLS (Actions that can be performed)

@mcp.tool()
async def create_memo(
    content: str, 
    visibility: str = "PRIVATE",
    tags: Optional[List[str]] = None
) -> str:
    """Create a new memo in Memos.
    
    Args:
        content: The memo content (markdown supported)
        visibility: Memo visibility (PRIVATE, PROTECTED, PUBLIC)
        tags: Optional list of tags to add to the memo
    """
    try:
        async with await get_client() as client:
            result = await client.create_memo(content, visibility, tags)
            memo_id = result.get("name", "unknown")
            return f"✅ Successfully created memo: {memo_id}"
    except MemosAPIError as e:
        return f"❌ Failed to create memo: {e}"
    except Exception as e:
        return f"❌ Error creating memo: {e}"


@mcp.tool()
async def get_memo(memo_id: str) -> str:
    """Get a specific memo by its ID.
    
    Args:
        memo_id: The ID of the memo to retrieve
    """
    try:
        async with await get_client() as client:
            memo = await client.get_memo(memo_id)
            return format_memo_for_display(memo)
    except MemosAPIError as e:
        return f"❌ Failed to get memo: {e}"
    except Exception as e:
        return f"❌ Error getting memo: {e}"


@mcp.tool()
async def update_memo(
    memo_id: str,
    content: str,
    visibility: Optional[str] = None
) -> str:
    """Update an existing memo.
    
    Args:
        memo_id: The ID of the memo to update
        content: The new content for the memo
        visibility: Optional new visibility setting
    """
    try:
        async with await get_client() as client:
            await client.update_memo(memo_id, content, visibility)
            return f"✅ Successfully updated memo: {memo_id}"
    except MemosAPIError as e:
        return f"❌ Failed to update memo: {e}"
    except Exception as e:
        return f"❌ Error updating memo: {e}"


@mcp.tool()
async def delete_memo(memo_id: str) -> str:
    """Delete a memo by its ID.
    
    Args:
        memo_id: The ID of the memo to delete
    """
    try:
        async with await get_client() as client:
            await client.delete_memo(memo_id)
            return f"✅ Successfully deleted memo: {memo_id}"
    except MemosAPIError as e:
        return f"❌ Failed to delete memo: {e}"
    except Exception as e:
        return f"❌ Error deleting memo: {e}"


@mcp.tool()
async def search_memos(
    query: str, 
    limit: Optional[int] = 20
) -> str:
    """Search memos by content.
    
    Args:
        query: Search query to find in memo content
        limit: Maximum number of results to return (default: 20)
    """
    try:
        async with await get_client() as client:
            memos = await client.search_memos(query, limit)
            
            if not memos:
                return f"🔍 No memos found matching '{query}'"
            
            result = [f"🔍 Found {len(memos)} memo(s) matching '{query}':\n"]
            for memo in memos:
                result.append(format_memo_for_display(memo))
            
            return "\n".join(result)
    except MemosAPIError as e:
        return f"❌ Failed to search memos: {e}"
    except Exception as e:
        return f"❌ Error searching memos: {e}"


@mcp.tool()
async def get_memos_by_date(
    date_str: str,
    limit: Optional[int] = 20
) -> str:
    """Get memos created on a specific date.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        limit: Maximum number of results to return (default: 20)
    """
    try:
        # Parse the date
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        async with await get_client() as client:
            memos = await client.get_memos_by_date(target_date, limit)
            
            if not memos:
                return f"📅 No memos found for {date_str}"
            
            result = [f"📅 Found {len(memos)} memo(s) for {date_str}:\n"]
            for memo in memos:
                result.append(format_memo_for_display(memo))
            
            return "\n".join(result)
    except ValueError:
        return "❌ Invalid date format. Please use YYYY-MM-DD"
    except MemosAPIError as e:
        return f"❌ Failed to get memos by date: {e}"
    except Exception as e:
        return f"❌ Error getting memos by date: {e}"


@mcp.tool()
async def get_memos_by_date_range(
    start_date: str,
    end_date: str,
    limit: Optional[int] = 20
) -> str:
    """Get memos created within a date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        limit: Maximum number of results to return (default: 20)
    """
    try:
        # Parse the dates
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        async with await get_client() as client:
            memos = await client.get_memos_by_date_range(start, end, limit)
            
            if not memos:
                return f"📅 No memos found between {start_date} and {end_date}"
            
            result = [f"📅 Found {len(memos)} memo(s) between {start_date} and {end_date}:\n"]
            for memo in memos:
                result.append(format_memo_for_display(memo))
            
            return "\n".join(result)
    except ValueError:
        return "❌ Invalid date format. Please use YYYY-MM-DD"
    except MemosAPIError as e:
        return f"❌ Failed to get memos by date range: {e}"
    except Exception as e:
        return f"❌ Error getting memos by date range: {e}"


@mcp.tool()
async def list_recent_memos(limit: Optional[int] = 10) -> str:
    """Get the most recent memos.
    
    Args:
        limit: Number of recent memos to return (default: 10)
    """
    try:
        async with await get_client() as client:
            memos = await client.get_recent_memos(limit or 10)
            
            if not memos:
                return "📝 No memos found"
            
            result = [f"📝 {len(memos)} most recent memo(s):\n"]
            for memo in memos:
                result.append(format_memo_for_display(memo))
            
            return "\n".join(result)
    except MemosAPIError as e:
        return f"❌ Failed to get recent memos: {e}"
    except Exception as e:
        return f"❌ Error getting recent memos: {e}"


# RESOURCES (Data that can be read)

@mcp.resource("memo://recent")
async def get_recent_memos_resource() -> str:
    """Get recent memos as a resource."""
    try:
        async with await get_client() as client:
            memos = await client.get_recent_memos(10)
            
            if not memos:
                return "No recent memos found"
            
            result = []
            for memo in memos:
                result.append(format_memo_for_display(memo))
            
            return "\n".join(result)
    except Exception as e:
        return f"Error loading recent memos: {e}"


@mcp.resource("memo://search/{query}")
async def search_memos_resource(query: str) -> str:
    """Search memos as a resource."""
    try:
        async with await get_client() as client:
            memos = await client.search_memos(query, 20)
            
            if not memos:
                return f"No memos found matching '{query}'"
            
            result = [f"Search results for '{query}':\n"]
            for memo in memos:
                result.append(format_memo_for_display(memo))
            
            return "\n".join(result)
    except Exception as e:
        return f"Error searching memos: {e}"


@mcp.resource("memo://date/{date_str}")
async def get_memos_by_date_resource(date_str: str) -> str:
    """Get memos by date as a resource."""
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        async with await get_client() as client:
            memos = await client.get_memos_by_date(target_date, 20)
            
            if not memos:
                return f"No memos found for {date_str}"
            
            result = [f"Memos for {date_str}:\n"]
            for memo in memos:
                result.append(format_memo_for_display(memo))
            
            return "\n".join(result)
    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD"
    except Exception as e:
        return f"Error getting memos by date: {e}"


@mcp.resource("memo://memo/{memo_id}")
async def get_memo_resource(memo_id: str) -> str:
    """Get a specific memo as a resource."""
    try:
        async with await get_client() as client:
            memo = await client.get_memo(memo_id)
            return format_memo_for_display(memo)
    except Exception as e:
        return f"Error getting memo: {e}"


if __name__ == "__main__":
    # Validate configuration before starting
    if not validate_config():
        print("❌ Configuration is invalid. Please check your MEMOS_URL and MEMOS_API_KEY environment variables.")
        exit(1)
    
    print("🚀 Starting MCP Memos Server...")
    print(f"📡 Connecting to Memos server: {config.memos_url}")
    
    # Run the server
    mcp.run()