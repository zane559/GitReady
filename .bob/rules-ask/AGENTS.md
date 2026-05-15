# AGENTS.md - Ask Mode

This file provides documentation and question-answering guidance for Ask mode.

## Project Documentation Context (Non-Obvious Only)

### Architecture Understanding
- **Single-file by design**: The entire application is intentionally in one file (`app.py`) for simplicity - this is NOT technical debt
- **No database**: All processing is ephemeral - repositories are cloned, analyzed, and deleted with no persistence
- **Stateless design**: Each analysis is independent - no user sessions or history tracking

### Hidden Documentation Locations
- **Prompt engineering**: The critical system prompt is embedded in `create_analysis_prompt()` function - this is the "secret sauce" for quality results
- **File filtering logic**: SUPPORTED_EXTENSIONS and IGNORE_DIRS constants define what gets analyzed - these are tuned for common codebases
- **Size limits**: MAX_FILE_SIZE (1MB) and MAX_TOTAL_SIZE (10MB) are hardcoded - not configurable via UI

### Common User Questions

**Q: Why does it skip some files?**
A: Three reasons: (1) Binary files detected by `is_text_file()`, (2) Files in IGNORE_DIRS, (3) Files exceeding size limits

**Q: Can it analyze private repositories?**
A: No - GitPython cloning requires public repos or SSH keys (not implemented)

**Q: Why does analysis take so long?**
A: Repository cloning + file reading + Watsonx.ai API call (which processes entire codebase) - typically 30-90 seconds

**Q: Can I use different AI models?**
A: Model ID is hardcoded to `"ibm/granite-13b-chat-v2"` - changing requires testing parameter compatibility

### Non-Obvious Limitations
- **No streaming**: Watsonx.ai response is all-or-nothing - no progressive display
- **No caching**: Same repository analyzed twice will re-clone and re-process everything
- **Windows-specific**: Path handling uses `pathlib.Path` specifically for Windows compatibility
- **Credential exposure**: Environment variables are the ONLY supported auth method - no UI input for security

### Technical Debt (Intentional)
- **No retry logic**: API failures are terminal - user must re-run
- **No progress tracking**: File reading shows no progress - only spinner
- **No partial results**: If analysis fails, nothing is saved
- **No repository validation**: Only checks URL format, not actual accessibility until clone attempt