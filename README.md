# MCP Memos Server

A Model Context Protocol (MCP) server that provides AI agents with access to your [Memos](https://usememos.com/) instance. This server allows AI models to read, write, search, and organize your memos through a standardized interface.

## Features

### 🔧 Tools (Actions)
- **create_memo** - Create new memos with content, tags, and visibility settings
- **get_memo** - Retrieve specific memos by ID
- **update_memo** - Modify existing memo content and settings
- **delete_memo** - Remove memos from your instance
- **search_memos** - Search through memo content with text queries
- **get_memos_by_date** - Find memos created on specific dates
- **get_memos_by_date_range** - Get memos within date ranges
- **list_recent_memos** - Access your most recent memos

### 📚 Resources (Data Access)
- `memo://recent` - Access recent memos
- `memo://search/{query}` - Search results for specific queries
- `memo://date/{YYYY-MM-DD}` - Memos from specific dates
- `memo://memo/{memo_id}` - Individual memo content

## Prerequisites

- A running Memos server (self-hosted or cloud)
- A Memos API key (generated in Settings → Access Tokens)
- Docker (optional, but recommended)
- Python 3.11+ (if running without Docker)

## Quick Start with Docker

1. **Clone or create the project directory:**
   ```bash
   git clone <repository> mcp-memos-server
   cd mcp-memos-server
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` with your Memos configuration:**
   ```bash
   # Required settings
   MEMOS_URL=https://your-memos-server.com
   MEMOS_API_KEY=your_api_key_here
   
   # Optional settings
   DEFAULT_VISIBILITY=PRIVATE
   MAX_SEARCH_RESULTS=50
   TIMEOUT=30
   ```

4. **Run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

5. **Test the connection:**
   ```bash
   docker-compose logs mcp-memos-server
   ```

## Installation without Docker

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export MEMOS_URL="https://your-memos-server.com"
   export MEMOS_API_KEY="your_api_key_here"
   ```

3. **Run the server:**
   ```bash
   python server.py
   ```

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MEMOS_URL` | Base URL of your Memos server | `https://memos.example.com` |
| `MEMOS_API_KEY` | API key from Memos Settings → Access Tokens | `memos_xxx...` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_VISIBILITY` | `PRIVATE` | Default visibility for new memos (`PRIVATE`, `PROTECTED`, `PUBLIC`) |
| `MAX_SEARCH_RESULTS` | `50` | Maximum number of search results to return |
| `TIMEOUT` | `30` | HTTP request timeout in seconds |

### Getting Your Memos API Key

1. Open your Memos web interface
2. Go to Settings → Access Tokens
3. Create a new access token
4. Copy the generated token (starts with `memos_`)

## Using with Claude Desktop

Add this to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "memos": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--env-file", "/path/to/your/.env",
        "mcp-memos-server"
      ]
    }
  }
}
```

Or if running locally:

```json
{
  "mcpServers": {
    "memos": {
      "command": "python",
      "args": ["/path/to/mcp-memos-server/server.py"],
      "env": {
        "MEMOS_URL": "https://your-memos-server.com",
        "MEMOS_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Usage Examples

### Creating Memos
```
AI: I'll create a memo about today's meeting notes.
Tool: create_memo
Args: {
  "content": "# Team Meeting - 2024-01-15\n\n- Discussed Q1 goals\n- Assigned tasks for sprint\n- Next meeting: Jan 22",
  "visibility": "PRIVATE",
  "tags": ["meeting", "team", "Q1"]
}
```

### Searching Memos
```
AI: Let me search for memos about "project planning"
Tool: search_memos
Args: {
  "query": "project planning",
  "limit": 10
}
```

### Finding Memos by Date
```
AI: Show me all memos from yesterday
Tool: get_memos_by_date
Args: {
  "date_str": "2024-01-14",
  "limit": 20
}
```

### Accessing Resources
```
AI: Let me check your recent memos
Resource: memo://recent

AI: I'll search for memos about "vacation"
Resource: memo://search/vacation
```

## API Documentation

### Tools

#### `create_memo`
Creates a new memo in your Memos instance.

**Parameters:**
- `content` (string, required): Memo content (Markdown supported)
- `visibility` (string, optional): `PRIVATE`, `PROTECTED`, or `PUBLIC`
- `tags` (array, optional): List of tags to add

**Returns:** Success message with memo ID

#### `search_memos`
Searches through your memos by content.

**Parameters:**
- `query` (string, required): Search query
- `limit` (integer, optional): Max results (default: 20)

**Returns:** List of matching memos

#### `get_memos_by_date`
Gets memos created on a specific date.

**Parameters:**
- `date_str` (string, required): Date in `YYYY-MM-DD` format
- `limit` (integer, optional): Max results (default: 20)

**Returns:** List of memos from that date

### Resources

Resources provide read-only access to your memo data:

- `memo://recent` - Recent memos
- `memo://search/{query}` - Search results
- `memo://date/{YYYY-MM-DD}` - Memos by date
- `memo://memo/{memo_id}` - Specific memo

## Troubleshooting

### Connection Issues
- Verify `MEMOS_URL` is correct (no trailing slash)
- Check that your API key is valid and has proper permissions
- Ensure your Memos server is accessible from the MCP server

### Docker Issues
- Check logs: `docker-compose logs mcp-memos-server`
- Verify environment variables: `docker-compose config`
- Restart containers: `docker-compose restart`

### Permission Errors
- Ensure your API key has read/write permissions
- Check that your user account has access to the memos you're trying to access

## Development

### Running Tests
```bash
python test_server.py
```

### Debugging
Enable debug logging by setting the environment variable:
```bash
export MCP_LOG_LEVEL=DEBUG
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Security Notes

- API keys are sensitive - never commit them to version control
- Use environment variables or secure secret management
- The Docker container runs as a non-root user for security
- All communication with Memos uses HTTPS (if your server supports it)

## Support

For issues and feature requests:
1. Check the troubleshooting section
2. Look for existing issues in the repository
3. Create a new issue with detailed information about your setup and the problem