# AGENTS.md - Code Mode

This file provides coding-specific guidance for agents working in Code mode.

## Project Coding Rules (Non-Obvious Only)

### Single-File Architecture Enforcement
- **Never split app.py**: All new features must be added as functions within app.py, not as separate modules
- **Import consolidation**: New dependencies must be added at the top of app.py following the existing pattern (stdlib → third-party)

### File Processing Gotchas
- **Encoding fallback chain**: When reading files, MUST try UTF-8 first, then latin-1 with `errors='ignore'` - some repos have mixed encodings
- **Binary detection**: `is_text_file()` reads first 512 bytes to detect binary files - don't rely solely on extensions as some binary files have text-like extensions
- **Path objects required**: Always use `Path` objects from `pathlib` for file operations - string paths break on Windows with backslashes

### Watsonx.ai API Constraints
- **Model ID is hardcoded**: `"ibm/granite-13b-chat-v2"` is the only tested model - changing this may break parameter compatibility
- **Credentials structure**: Must pass both `credentials` dict AND separate `project_id` parameter - common mistake is to include project_id in credentials dict
- **Token limit enforcement**: MAX_NEW_TOKENS=4000 is a hard limit - exceeding causes API errors, not truncation
- **Prompt structure**: The system prompt in `create_analysis_prompt()` must explicitly instruct AI to reference actual code - generic prompts produce useless results

### Streamlit State Management
- **Avoid st.session_state for repo data**: Repository content persists across reruns causing memory bloat - use local variables only
- **Error display pattern**: Use `st.error()` for user-facing errors, never `raise` exceptions which crash the entire app
- **Spinner context**: All long operations must be wrapped in `with st.spinner()` for user feedback

### Cleanup Patterns
- **try/finally mandatory**: Repository cloning MUST use try/finally to ensure `shutil.rmtree(temp_dir)` runs even on errors
- **Exception catching**: GitPython raises various exception types - catch generic `Exception` not specific git exceptions

### Size Limits (Critical)
- **MAX_FILE_SIZE = 1MB**: Individual files larger than this are silently skipped - no error shown to user
- **MAX_TOTAL_SIZE = 10MB**: Total code size limit to prevent context window overflow - processing stops when reached
- **IGNORE_DIRS**: Must include all common dependency folders - missing one can cause processing of thousands of files

## Testing Requirements

- **Credentials required**: No mock mode exists - must have real IBM Watsonx.ai credentials to test
- **Small repos for testing**: Use repos with <100 files for faster iteration during development
- **Windows path testing**: Test with repos that have deep directory structures to catch Path handling issues