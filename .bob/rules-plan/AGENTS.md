# AGENTS.md - Plan Mode

This file provides architectural planning guidance for Plan mode.

## Project Architecture Rules (Non-Obvious Only)

### Design Decisions (Intentional Constraints)

**Single-File Architecture**
- **Why**: Simplicity for hackathon demo - easy to understand, debug, and deploy
- **Trade-off**: Harder to test individual components, but acceptable for 500-line app
- **Do NOT refactor**: Splitting into modules violates core design principle

**Ephemeral Processing**
- **Why**: No database/storage complexity - stateless design
- **Trade-off**: No analysis history or caching, but keeps deployment simple
- **Implication**: Each analysis is independent - no user sessions needed

**Hardcoded Limits**
- **Why**: Prevent context window overflow and memory issues
- **Trade-off**: Large repos (>10MB code) won't fully analyze, but protects against crashes
- **Do NOT make configurable**: UI complexity not worth it for hackathon scope

### Hidden Architectural Patterns

**Error Handling Strategy**
- **Pattern**: Return tuples `(success: bool, result/error: str)` from all functions
- **Why**: Allows graceful degradation - UI can display errors without crashing
- **Critical**: Never use `raise` in functions called from Streamlit UI

**Cleanup Architecture**
- **Pattern**: `try/finally` with `shutil.rmtree(temp_dir)` in finally block
- **Why**: GitPython cloning can fail mid-process - must guarantee cleanup
- **Critical**: Temp directory deletion must happen even on exceptions

**Prompt Engineering Architecture**
- **Pattern**: System prompt embedded in `create_analysis_prompt()` function
- **Why**: Prompt is the "secret sauce" - keeping it in code ensures version control
- **Critical**: Prompt must explicitly instruct AI to reference actual code, not make generic observations

### Scalability Constraints (Intentional)

**Not Designed For:**
- Concurrent users (no session management)
- Large repositories (>10MB code limit)
- Private repositories (no auth implementation)
- Production deployment (no monitoring, logging, or error tracking)

**Designed For:**
- Single-user local deployment
- Small-to-medium public repos (<1000 files)
- Hackathon demo and interview prep use case
- Quick iteration and debugging

### Future Architecture Considerations

**If Scaling Up:**
- Add Redis caching for analyzed repositories
- Implement background job queue for long-running analyses
- Add user authentication and session management
- Split into microservices (API + UI + Worker)
- Add database for analysis history

**If Adding Features:**
- Keep single-file constraint OR fully refactor to modules (no half-measures)
- Add retry logic with exponential backoff for Watsonx API
- Implement streaming responses for better UX
- Add repository size pre-check before cloning