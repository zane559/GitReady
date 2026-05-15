# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Overview

GitReady is a single-file Streamlit application (`app.py`) that analyzes GitHub repositories using IBM Watsonx.ai to generate interview preparation materials.

## Non-Obvious Project-Specific Rules

### Architecture Constraints
- **Single-file design**: ALL application logic must remain in `app.py` - do not split into modules or separate files
- **Temporary storage**: Repository cloning uses `tempfile.mkdtemp()` which must be cleaned up in `finally` blocks to prevent disk space issues
- **Context window management**: IBM Granite models have token limits - code aggregation in `format_code_for_analysis()` must be monitored for size

### Critical Implementation Details
- **File reading encoding**: Must try UTF-8 first, then fallback to latin-1 with `errors='ignore'` to handle diverse codebases
- **Binary file detection**: Use `is_text_file()` function which attempts to read first 512 bytes - checking extensions alone is insufficient
- **GitPython depth parameter**: Always use `depth=1` in `Repo.clone_from()` for faster cloning and reduced disk usage
- **Streamlit state management**: Avoid using `st.session_state` for repository data as it persists across reruns and causes memory issues

### IBM Watsonx.ai Integration
- **Model ID**: Must use `"ibm/granite-13b-chat-v2"` - other Granite models may not support the required parameters
- **Credentials structure**: Watsonx requires both `credentials` dict (url, apikey) AND separate `project_id` parameter
- **Prompt engineering**: The system prompt in `create_analysis_prompt()` is critical - it must explicitly instruct the AI to reference actual code, not make generic observations
- **Token limits**: MAX_NEW_TOKENS is set to 4000 - increasing beyond this may cause API failures

### File Processing Rules
- **MAX_FILE_SIZE**: 1MB per file limit prevents memory issues with large files
- **MAX_TOTAL_SIZE**: 10MB total prevents context window overflow
- **IGNORE_DIRS**: Must include common dependency folders (node_modules, venv, etc.) to avoid processing thousands of irrelevant files
- **Path handling**: Use `Path.relative_to()` for display paths to avoid exposing temp directory structure

### Error Handling Patterns
- **Repository cloning**: Must catch generic `Exception` as GitPython raises various error types
- **Cleanup guarantee**: Use `try/finally` pattern to ensure `shutil.rmtree(temp_dir)` runs even on errors
- **Streamlit error display**: Use `st.error()` for user-facing errors, not `raise` statements which crash the app

### Testing Considerations
- **Local testing**: Requires actual IBM Watsonx.ai credentials - no mock mode available
- **Repository testing**: Use small public repos (< 100 files) for faster iteration
- **Windows path handling**: Use `Path` objects throughout to handle Windows backslashes correctly

## Commands

### Run Application
```bash
streamlit run app.py
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Set Environment Variables (Windows PowerShell)
```powershell
$env:WATSONX_API_KEY="your_key"
$env:WATSONX_PROJECT_ID="your_project_id"
```

## Code Style

- **Imports**: Standard library first, then third-party (streamlit, git, ibm_watsonx_ai)
- **Constants**: ALL_CAPS at module level (SUPPORTED_EXTENSIONS, IGNORE_DIRS, etc.)
- **Functions**: Descriptive names with docstrings, return tuples of (success: bool, result/error: str)
- **Error messages**: User-friendly with emoji prefixes (❌, ⚠️, ✅) for Streamlit display
- **Comments**: Explain WHY not WHAT - focus on non-obvious decisions

## Known Gotchas

1. **PowerShell && operator**: Use semicolons (`;`) instead of `&&` for command chaining in PowerShell
2. **Git authentication**: HTTPS URLs require credentials - SSH may be easier for repeated pushes
3. **Streamlit reruns**: Every UI interaction reruns the entire script - use conditionals to prevent re-processing
4. **Watsonx rate limits**: API may throttle requests - add retry logic if needed for production use
5. **Large repositories**: Repos with >1000 files may hit size limits - consider adding file count warnings