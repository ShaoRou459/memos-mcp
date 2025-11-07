"""Memos API client for MCP server."""

import httpx
import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from dateutil.parser import parse as parse_date
from config import MemosConfig


class MemosAPIError(Exception):
    """Custom exception for Memos API errors."""
    pass


class MemosClient:
    """Client for interacting with Memos API."""
    
    def __init__(self, config: MemosConfig, api_key: Optional[str] = None):
        self.config = config
        self.base_url = str(config.memos_url).rstrip('/')
        # Use provided API key or fall back to config
        self.api_key = api_key or config.memos_api_key
        self.timeout = config.timeout
        
        if not self.api_key:
            raise ValueError("API key must be provided either in config or as parameter")
        
        # Set up HTTP client
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Memos API."""
        url = f"{self.base_url}/api/v1/{endpoint.lstrip('/')}"
        
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            else:
                return {"data": response.text}
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            raise MemosAPIError(error_msg) from e
        except Exception as e:
            raise MemosAPIError(f"Request failed: {str(e)}") from e
    
    async def create_memo(
        self, 
        content: str, 
        visibility: str = "PRIVATE",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new memo."""
        payload = {
            "content": content,
            "visibility": visibility.upper()
        }
        
        # Add tags to content if provided
        if tags:
            # Memos typically handles tags as part of the content with #tag format
            tag_string = " " + " ".join(f"#{tag}" for tag in tags)
            payload["content"] += tag_string
        
        return await self._request("POST", "memos", json=payload)
    
    async def get_memo(self, memo_id: str) -> Dict[str, Any]:
        """Get a specific memo by ID."""
        return await self._request("GET", f"memos/{memo_id}")
    
    async def update_memo(
        self, 
        memo_id: str, 
        content: str, 
        visibility: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing memo."""
        payload = {"content": content}
        
        if visibility:
            payload["visibility"] = visibility.upper()
        
        return await self._request("PATCH", f"memos/{memo_id}", json=payload)
    
    async def delete_memo(self, memo_id: str) -> bool:
        """Delete a memo."""
        await self._request("DELETE", f"memos/{memo_id}")
        return True
    
    async def list_memos(
        self, 
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        creator: Optional[str] = None
    ) -> Dict[str, Any]:
        """List memos with optional pagination."""
        params = {}
        
        if limit:
            params["pageSize"] = str(limit)
        if offset:
            params["pageToken"] = str(offset)
        if creator:
            params["creator"] = creator
        
        endpoint = "memos"
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            endpoint += f"?{query_string}"
        
        return await self._request("GET", endpoint)
    
    async def search_memos(
        self, 
        query: str, 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search memos by content."""
        # Get all memos first (Memos API might not have direct search)
        response = await self.list_memos(limit=limit or self.config.max_search_results)
        memos = response.get("memos", [])
        
        # Filter memos that contain the search query
        search_results = []
        query_lower = query.lower()
        
        for memo in memos:
            content = memo.get("content", "").lower()
            if query_lower in content:
                search_results.append(memo)
        
        return search_results
    
    async def get_memos_by_date(
        self, 
        target_date: date,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get memos created on a specific date."""
        # Get memos and filter by creation date
        response = await self.list_memos(limit=limit or self.config.max_search_results)
        memos = response.get("memos", [])
        
        filtered_memos = []
        
        for memo in memos:
            created_time = memo.get("createTime")
            if created_time:
                try:
                    # Parse the creation time and compare dates
                    created_date = parse_date(created_time).date()
                    if created_date == target_date:
                        filtered_memos.append(memo)
                except Exception:
                    continue
        
        return filtered_memos
    
    async def get_memos_by_date_range(
        self, 
        start_date: date,
        end_date: date,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get memos created within a date range."""
        response = await self.list_memos(limit=limit or self.config.max_search_results)
        memos = response.get("memos", [])
        
        filtered_memos = []
        
        for memo in memos:
            created_time = memo.get("createTime")
            if created_time:
                try:
                    created_date = parse_date(created_time).date()
                    if start_date <= created_date <= end_date:
                        filtered_memos.append(memo)
                except Exception:
                    continue
        
        return filtered_memos
    
    async def get_recent_memos(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent memos."""
        response = await self.list_memos(limit=limit)
        return response.get("memos", [])

    async def get_memos_paginated(
        self,
        page_size: int = 20,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get memos with pagination support, sorted chronologically.

        Args:
            page_size: Number of memos to return per page
            page_token: Token for pagination (from previous response)

        Returns:
            Dict containing:
                - memos: List of memo objects
                - nextPageToken: Token for next page (if available)
        """
        response = await self.list_memos(limit=page_size, offset=page_token)

        # Extract memos and sort them by creation time (oldest first for chronological iteration)
        memos = response.get("memos", [])

        # Sort by createTime
        sorted_memos = sorted(
            memos,
            key=lambda m: parse_date(m.get("createTime", "1970-01-01T00:00:00Z"))
        )

        # Get next page token from response
        next_token = response.get("nextPageToken")

        return {
            "memos": sorted_memos,
            "nextPageToken": next_token,
            "totalCount": len(sorted_memos)
        }