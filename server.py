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

# Global client instance and API key storage
_client: Optional[MemosClient] = None
_user_api_key: Optional[str] = None


async def get_client(api_key: Optional[str] = None) -> MemosClient:
    """Get or create Memos client instance.
    
    Args:
        api_key: Optional API key to use. If not provided, uses global user API key or config.
    """
    global _client, _user_api_key
    
    # Determine which API key to use
    effective_api_key = api_key or _user_api_key
    
    # If we have a new API key or no client yet, create a new client
    if _client is None or (effective_api_key and _client.api_key != effective_api_key):
        _client = MemosClient(config, effective_api_key)
    
    return _client


def check_api_key_set() -> Optional[str]:
    """Check if API key is set and return error message if not."""
    global _user_api_key
    if not _user_api_key and not config.memos_api_key:
        return "❌ No API key configured. Please use the 'set_api_key' tool first to provide your Memos API key."
    return None


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
async def set_api_key(api_key: str) -> str:
    """Set the API key for connecting to Memos server.
    
    This must be called first before using any other memo operations.
    Get your API key from Memos Settings → Access Tokens.
    
    Args:
        api_key: Your Memos API key (starts with 'memos_')
    """
    global _user_api_key, _client
    
    # Validate API key format (basic check)
    if not api_key or not isinstance(api_key, str):
        return "❌ Invalid API key format"
    
    # Store the API key
    _user_api_key = api_key
    
    # Reset client so it gets recreated with new API key
    if _client:
        await _client.client.aclose()
        _client = None
    
    # Test the connection
    try:
        async with await get_client() as client:
            # Try to list memos to test connection
            await client.list_memos(limit=1)
            return "✅ API key set successfully and connection verified"
    except Exception as e:
        _user_api_key = None  # Clear invalid key
        return f"❌ Failed to connect with provided API key: {e}"


# MEMO MANAGEMENT TOOLS

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
    # Check if API key is configured
    api_key_error = check_api_key_set()
    if api_key_error:
        return api_key_error
    
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
    # Check if API key is configured
    api_key_error = check_api_key_set()
    if api_key_error:
        return api_key_error
    
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
    # Check if API key is configured
    api_key_error = check_api_key_set()
    if api_key_error:
        return api_key_error
    
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
    # Check if API key is configured
    api_key_error = check_api_key_set()
    if api_key_error:
        return api_key_error
    
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
    # Check if API key is configured
    api_key_error = check_api_key_set()
    if api_key_error:
        return api_key_error
    
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
    # Check if API key is configured
    api_key_error = check_api_key_set()
    if api_key_error:
        return api_key_error
    
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
    # Check if API key is configured
    api_key_error = check_api_key_set()
    if api_key_error:
        return api_key_error
    
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
    # Check if API key is configured
    api_key_error = check_api_key_set()
    if api_key_error:
        return api_key_error

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


@mcp.tool()
async def iterate_memos_chronologically(
    page_size: Optional[int] = 20,
    page_token: Optional[str] = None
) -> str:
    """Iterate through all memos in chronological order (by date added/created).

    This tool supports pagination, allowing you to iterate through all memos
    systematically. Memos are sorted from oldest to newest by creation time.

    Args:
        page_size: Number of memos to return per page (default: 20, max: 100)
        page_token: Token from previous response to get next page (optional)
    """
    # Check if API key is configured
    api_key_error = check_api_key_set()
    if api_key_error:
        return api_key_error

    # Validate page size
    if page_size and page_size > 100:
        page_size = 100

    try:
        async with await get_client() as client:
            response = await client.get_memos_paginated(
                page_size=page_size or 20,
                page_token=page_token
            )

            memos = response.get("memos", [])
            next_token = response.get("nextPageToken")

            if not memos:
                return "📝 No more memos found"

            result = [f"📅 Showing {len(memos)} memo(s) in chronological order:\n"]

            for memo in memos:
                result.append(format_memo_for_display(memo))

            # Add pagination info
            if next_token:
                result.append(f"\n📄 More memos available. Use page_token='{next_token}' to get the next page.")
            else:
                result.append("\n✅ End of memos reached.")

            return "\n".join(result)
    except MemosAPIError as e:
        return f"❌ Failed to iterate memos: {e}"
    except Exception as e:
        return f"❌ Error iterating memos: {e}"


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
    # Validate configuration before starting (API key is now optional)
    if not validate_config():
        print("❌ Configuration is invalid. Please check your MEMOS_URL environment variable.")
        print("📝 Note: API key can now be provided by users at runtime using the 'set_api_key' tool.")
        exit(1)
    
    print("🚀 Starting MCP Memos Server...")
    print(f"📡 Memos server URL: {config.memos_url}")
    if config.memos_api_key:
        print("✅ API key found in configuration")
    else:
        print("📝 API key not set - users can provide it using the 'set_api_key' tool")
    
    # Run the server
    mcp.run()