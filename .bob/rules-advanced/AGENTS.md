# AGENTS.md - Advanced Mode

This file provides advanced mode-specific guidance for agents with access to MCP and Browser tools.

## Project Advanced Rules (Non-Obvious Only)

### Architecture Constraints (Same as Code Mode)
- **Single-file design**: ALL application logic must remain in `app.py` - do not split into modules
- **Temporary storage**: Repository cloning uses `tempfile.mkdtemp()` - cleanup in `finally` blocks is mandatory
- **Context window management**: IBM Granite models have token limits - monitor code aggregation size

### Advanced Tool Usage

#### MCP Integration Opportunities
- **API documentation lookup**: Use MCP to fetch latest IBM Watsonx.ai API documentation when troubleshooting
- **Dependency version checking**: Query package registries for compatible versions of streamlit, gitpython, ibm-watsonx-ai
- **Repository analysis**: Use MCP to analyze example repositories before testing GitReady on them

#### Browser Tool Usage
- **IBM Cloud console**: Access IBM Watsonx.ai console to verify project IDs and model availability
- **GitHub API**: Check repository accessibility and size before cloning
- **Documentation**: Reference official Streamlit and IBM Watsonx.ai docs for advanced features

### Critical Implementation Details (Same as Code Mode)
- **File reading encoding**: UTF-8 first, then latin-1 with `errors='ignore'`
- **Binary file detection**: `is_text_file()` reads first 512 bytes
- **GitPython depth parameter**: Always use `depth=1` for faster cloning
- **Streamlit state management**: Avoid `st.session_state` for repository data

### Watsonx.ai API Constraints
- **Model ID**: `"ibm/granite-13b-chat-v2"` is hardcoded - other models may not work
- **Credentials structure**: Both `credentials` dict AND separate `project_id` parameter required
- **Token limits**: MAX_NEW_TOKENS=4000 is a hard limit
- **Prompt engineering**: System prompt must explicitly instruct AI to reference actual code

### Testing with Advanced Tools
- **Use Browser to verify**: Check GitHub repo accessibility before testing
- **Use MCP for debugging**: Query API documentation when encountering Watsonx errors
- **Credential validation**: Use Browser to verify IBM Cloud project settings