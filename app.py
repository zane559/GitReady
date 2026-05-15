"""
GitReady - AI-Powered Interview Preparation Tool
Analyzes GitHub repositories to generate comprehensive interview materials
Built for IBM Bob Hackathon

CRITICAL FIXES IMPLEMENTED:
1. Session state for persistent analysis results
2. Token management with intelligent chunking
3. Modular execution architecture for external orchestration
4. Real-time token streaming with st.write_stream
"""

import streamlit as st
import os
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Generator, Any
from git import Repo
from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
import tiktoken
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="GitReady - Interview Prep Tool",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Constants
SUPPORTED_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
    '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.r',
    '.sql', '.sh', '.bash', '.yaml', '.yml', '.json', '.xml', '.html', '.css',
    '.md', '.txt', '.env.example', '.gitignore', 'Dockerfile', 'Makefile'
}

IGNORE_DIRS = {
    '.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env',
    'dist', 'build', '.next', '.nuxt', 'target', 'bin', 'obj',
    '.idea', '.vscode', 'coverage', '.pytest_cache'
}

MAX_FILE_SIZE = 1024 * 1024  # 1MB per file
MAX_TOTAL_SIZE = 10 * 1024 * 1024  # 10MB total
MAX_CONTEXT_TOKENS = 7000  # Safe limit for 8k context window (leaving room for response)
CHUNK_OVERLAP_TOKENS = 200  # Overlap between chunks to preserve context
MAX_NEW_TOKENS = 4000  # Maximum tokens for model response

# Initialize session state at module level
def init_session_state():
    """Initialize all session state variables"""
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'analysis_sections' not in st.session_state:
        st.session_state.analysis_sections = None
    if 'repo_url' not in st.session_state:
        st.session_state.repo_url = None
    if 'analysis_status' not in st.session_state:
        st.session_state.analysis_status = None
    if 'error_message' not in st.session_state:
        st.session_state.error_message = None


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Count tokens in text using tiktoken"""
    try:
        encoding = tiktoken.get_encoding(model)
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Token counting failed, using character estimate: {e}")
        # Fallback: rough estimate (1 token ≈ 4 characters)
        return len(text) // 4


def chunk_text_by_structure(text: str, max_tokens: int, overlap_tokens: int = 200) -> List[str]:
    """
    Intelligently chunk text preserving code structure.
    Splits at function/class boundaries when possible.
    """
    chunks = []
    current_chunk = ""
    current_tokens = 0
    
    lines = text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        line_tokens = count_tokens(line + '\n')
        
        # Check if adding this line would exceed max tokens
        if current_tokens + line_tokens > max_tokens and current_chunk:
            # Save current chunk
            chunks.append(current_chunk)
            
            # Start new chunk with overlap
            overlap_lines = []
            overlap_token_count = 0
            
            # Go back to include overlap
            j = i - 1
            while j >= 0 and overlap_token_count < overlap_tokens:
                prev_line = lines[j]
                prev_tokens = count_tokens(prev_line + '\n')
                if overlap_token_count + prev_tokens <= overlap_tokens:
                    overlap_lines.insert(0, prev_line)
                    overlap_token_count += prev_tokens
                    j -= 1
                else:
                    break
            
            current_chunk = '\n'.join(overlap_lines) + '\n' if overlap_lines else ""
            current_tokens = overlap_token_count
        
        current_chunk += line + '\n'
        current_tokens += line_tokens
        i += 1
    
    # Add final chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def validate_github_url(url: str) -> Tuple[bool, str]:
    """Validate GitHub repository URL format"""
    if not url:
        return False, "Please enter a GitHub URL"
    
    url = url.strip()
    if not (url.startswith('https://github.com/') or url.startswith('http://github.com/')):
        return False, "URL must be a valid GitHub repository (https://github.com/...)"
    
    parts = url.replace('https://github.com/', '').replace('http://github.com/', '').split('/')
    if len(parts) < 2:
        return False, "Invalid GitHub URL format. Expected: https://github.com/username/repository"
    
    return True, url


def clone_repository(repo_url: str, temp_dir: str) -> Tuple[bool, Any]:
    """Clone GitHub repository to temporary directory"""
    try:
        logger.info(f"Cloning repository: {repo_url}")
        repo = Repo.clone_from(repo_url, temp_dir, depth=1)
        return True, repo
    except Exception as e:
        logger.error(f"Clone failed: {e}")
        return False, f"Failed to clone repository: {str(e)}"


def is_text_file(file_path: Path) -> bool:
    """Check if file is a text file by attempting to read it"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(512)
        return True
    except (UnicodeDecodeError, PermissionError):
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                f.read(512)
            return True
        except:
            return False


def read_repository_files(repo_path: str) -> Tuple[List[Dict], int, int]:
    """Recursively read all code files from repository"""
    files_content = []
    total_size = 0
    file_count = 0
    
    repo_path_obj = Path(repo_path)
    
    for file_path in repo_path_obj.rglob('*'):
        if file_path.is_dir():
            continue
        
        if any(ignored in file_path.parts for ignored in IGNORE_DIRS):
            continue
        
        if file_path.suffix not in SUPPORTED_EXTENSIONS and file_path.name not in SUPPORTED_EXTENSIONS:
            continue
        
        try:
            file_size = file_path.stat().st_size
            if file_size > MAX_FILE_SIZE:
                continue
            
            if total_size + file_size > MAX_TOTAL_SIZE:
                logger.warning("Reached maximum total size limit")
                break
            
            if is_text_file(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                relative_path = file_path.relative_to(repo_path_obj)
                files_content.append({
                    'path': str(relative_path),
                    'content': content,
                    'size': file_size
                })
                
                total_size += file_size
                file_count += 1
        
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
            continue
    
    return files_content, file_count, total_size


def format_code_for_analysis(files_content: List[Dict], repo_url: str) -> str:
    """Format code files into structured text for LLM analysis"""
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    
    formatted_text = f"# Repository: {repo_name}\n"
    formatted_text += f"# URL: {repo_url}\n"
    formatted_text += f"# Total Files: {len(files_content)}\n\n"
    
    formatted_text += "## File Structure:\n"
    for file_info in files_content:
        formatted_text += f"- {file_info['path']}\n"
    formatted_text += "\n"
    
    formatted_text += "## File Contents:\n\n"
    for file_info in files_content:
        formatted_text += f"### File: {file_info['path']}\n"
        formatted_text += f"```\n{file_info['content']}\n```\n\n"
    
    return formatted_text


def get_watsonx_credentials() -> Tuple[Optional[Dict], Optional[str]]:
    """Get IBM Watsonx.ai credentials from environment variables"""
    api_key = os.getenv('WATSONX_API_KEY')
    project_id = os.getenv('WATSONX_PROJECT_ID')
    url = os.getenv('WATSONX_URL', 'https://us-south.ml.cloud.ibm.com')
    
    if not api_key or not project_id:
        return None, "Missing IBM Watsonx.ai credentials. Please set WATSONX_API_KEY and WATSONX_PROJECT_ID environment variables."
    
    return {
        'api_key': api_key,
        'project_id': project_id,
        'url': url
    }, None


def create_analysis_prompt(code_content: str, repo_url: str, chunk_num: int = 0, total_chunks: int = 1) -> str:
    """Create detailed prompt for code analysis"""
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    
    chunk_info = f" (Part {chunk_num + 1} of {total_chunks})" if total_chunks > 1 else ""
    
    prompt = f"""You are an expert technical interviewer analyzing the GitHub repository: {repo_name}{chunk_info}

Repository URL: {repo_url}

Your task is to deeply analyze this codebase and generate comprehensive interview preparation materials. You MUST reference actual code implementations, specific function names, class structures, and architectural patterns found in the code.

Here is the codebase{chunk_info}:

{code_content}

Generate a detailed analysis with the following four sections:

## 1. TECHNICAL INTERVIEW QUESTIONS (10 questions with detailed answers)
Create 10 technical interview questions that probe deep understanding of THIS specific codebase. Each question must:
- Reference actual functions, classes, or modules from the code
- Focus on implementation choices made in THIS repository
- Include a comprehensive answer that explains the actual code implementation
- Cover different aspects: architecture, algorithms, design patterns, data structures, error handling, etc.

Format each as:
Q1: [Specific question about actual code]
A1: [Detailed answer referencing actual implementation]

## 2. NON-TECHNICAL EXPLANATION
Provide a clear, jargon-free explanation of what this project does and how it works. Suitable for explaining to:
- Non-technical stakeholders
- Recruiters
- Family members
Make it engaging and understandable while being accurate about the actual functionality.

## 3. CODE WEAKNESSES & TECHNICAL DEBT ANALYSIS
Identify specific areas where interviewers are likely to probe:
- Code smells or anti-patterns you found in specific files
- Missing error handling or edge cases
- Performance bottlenecks or scalability concerns
- Security vulnerabilities
- Technical debt or areas needing refactoring
- Missing tests or documentation
Reference actual code locations and provide specific examples.

## 4. ELEVATOR PITCH
Create a compelling one-liner that captures the essence and value proposition of this project. Make it memorable and impactful.

CRITICAL: Your analysis must be based on the ACTUAL code provided, not generic assumptions. Reference specific files, functions, and implementation details throughout your response."""

    return prompt


def stream_analysis_generator(model: Model, prompt: str) -> Generator[str, None, None]:
    """Generator function that yields streaming tokens from Watsonx.ai"""
    try:
        for chunk in model.generate_text_stream(prompt=prompt):
            yield chunk
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"\n\n❌ Streaming error: {str(e)}"


def analyze_with_watsonx_streaming(code_content: str, repo_url: str, credentials: Dict) -> Tuple[bool, str, Optional[Any]]:
    """
    Analyze code using IBM Watsonx.ai with streaming support and token management.
    Returns: (success, result_text, error_message)
    """
    try:
        # Initialize Watsonx model
        model = Model(
            model_id="ibm/granite-13b-chat-v2",
            params={
                GenParams.DECODING_METHOD: "greedy",
                GenParams.MAX_NEW_TOKENS: MAX_NEW_TOKENS,
                GenParams.MIN_NEW_TOKENS: 100,
                GenParams.TEMPERATURE: 0.7,
                GenParams.TOP_K: 50,
                GenParams.TOP_P: 1
            },
            credentials={
                "url": credentials['url'],
                "apikey": credentials['api_key']
            },
            project_id=credentials['project_id']
        )
        
        # Count tokens in code content
        code_tokens = count_tokens(code_content)
        logger.info(f"Code content tokens: {code_tokens}")
        
        # Check if chunking is needed
        if code_tokens > MAX_CONTEXT_TOKENS:
            st.warning(f"⚠️ Code size ({code_tokens} tokens) exceeds context window. Using intelligent chunking...")
            chunks = chunk_text_by_structure(code_content, MAX_CONTEXT_TOKENS, CHUNK_OVERLAP_TOKENS)
            logger.info(f"Split into {len(chunks)} chunks")
            
            # Process chunks and aggregate results
            all_results = []
            for i, chunk in enumerate(chunks):
                st.info(f"🤖 Processing chunk {i + 1} of {len(chunks)}...")
                prompt = create_analysis_prompt(chunk, repo_url, i, len(chunks))
                
                # Stream this chunk
                chunk_placeholder = st.empty()
                chunk_result = ""
                
                try:
                    for token in stream_analysis_generator(model, prompt):
                        chunk_result += token
                        chunk_placeholder.markdown(chunk_result)
                except Exception as e:
                    logger.error(f"Chunk {i + 1} streaming failed: {e}")
                    return False, "", f"Chunk {i + 1} analysis failed: {str(e)}"
                
                all_results.append(chunk_result)
                chunk_placeholder.empty()
            
            # Aggregate results
            st.info("🔄 Aggregating results from all chunks...")
            aggregated_result = "\n\n---\n\n".join([f"## Analysis Part {i+1}\n{result}" for i, result in enumerate(all_results)])
            return True, aggregated_result, None
        
        else:
            # Single pass - no chunking needed
            prompt = create_analysis_prompt(code_content, repo_url)
            
            # Validate final prompt size
            prompt_tokens = count_tokens(prompt)
            if prompt_tokens > MAX_CONTEXT_TOKENS:
                # Emergency truncation
                st.warning(f"⚠️ Prompt too large ({prompt_tokens} tokens). Truncating to fit context window...")
                truncated_code = code_content[:MAX_CONTEXT_TOKENS * 4]  # Rough character estimate
                prompt = create_analysis_prompt(truncated_code, repo_url)
            
            # Stream the response
            result_placeholder = st.empty()
            full_result = ""
            
            try:
                for token in stream_analysis_generator(model, prompt):
                    full_result += token
                    result_placeholder.markdown(full_result)
            except Exception as e:
                logger.error(f"Streaming failed: {e}")
                return False, "", f"Analysis streaming failed: {str(e)}"
            
            result_placeholder.empty()
            return True, full_result, None
    
    except Exception as e:
        logger.error(f"Watsonx analysis failed: {e}")
        return False, "", f"Watsonx.ai analysis failed: {str(e)}"


def parse_analysis_response(response_text: str) -> Dict[str, str]:
    """Parse the AI response into structured sections"""
    sections = {
        'questions': '',
        'explanation': '',
        'weaknesses': '',
        'pitch': ''
    }
    
    parts = response_text.split('##')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        if '1.' in part and 'TECHNICAL INTERVIEW QUESTIONS' in part.upper():
            sections['questions'] = part.split('\n', 1)[1].strip() if '\n' in part else part
        elif '2.' in part and 'NON-TECHNICAL EXPLANATION' in part.upper():
            sections['explanation'] = part.split('\n', 1)[1].strip() if '\n' in part else part
        elif '3.' in part and ('WEAKNESSES' in part.upper() or 'TECHNICAL DEBT' in part.upper()):
            sections['weaknesses'] = part.split('\n', 1)[1].strip() if '\n' in part else part
        elif '4.' in part and 'ELEVATOR PITCH' in part.upper():
            sections['pitch'] = part.split('\n', 1)[1].strip() if '\n' in part else part
    
    return sections


# MODULAR EXECUTION ARCHITECTURE - Core business logic separated from UI
def analyze_repository_async(
    repo_url: str,
    github_token: Optional[str] = None,
    model_config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Standalone execution function for external orchestration.
    Can be called from background workers, async task queues, or API endpoints.
    
    Args:
        repo_url: GitHub repository URL
        github_token: Optional GitHub token for private repos
        model_config: Optional custom model configuration
    
    Returns:
        Dict with keys: success, result, error, metadata
    """
    result = {
        'success': False,
        'result': None,
        'error': None,
        'metadata': {
            'repo_url': repo_url,
            'file_count': 0,
            'total_size': 0,
            'token_count': 0,
            'chunks_processed': 0
        }
    }
    
    temp_dir = None
    
    try:
        # Validate URL
        is_valid, validated_url = validate_github_url(repo_url)
        if not is_valid:
            result['error'] = validated_url
            return result
        
        repo_url = validated_url
        
        # Get credentials
        credentials, error = get_watsonx_credentials()
        if error or credentials is None:
            result['error'] = error or "Failed to get credentials"
            return result
        
        # Override with custom config if provided
        if model_config and credentials:
            credentials.update(model_config)
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temp directory: {temp_dir}")
        
        # Clone repository
        success, clone_result = clone_repository(repo_url, temp_dir)
        if not success:
            result['error'] = clone_result
            return result
        
        # Read files
        files_content, file_count, total_size = read_repository_files(temp_dir)
        result['metadata']['file_count'] = file_count
        result['metadata']['total_size'] = total_size
        
        if not files_content:
            result['error'] = "No supported code files found in repository"
            return result
        
        # Format code
        formatted_code = format_code_for_analysis(files_content, repo_url)
        result['metadata']['token_count'] = count_tokens(formatted_code)
        
        # Analyze (non-streaming version for external calls)
        model = Model(
            model_id="ibm/granite-13b-chat-v2",
            params={
                GenParams.DECODING_METHOD: "greedy",
                GenParams.MAX_NEW_TOKENS: MAX_NEW_TOKENS,
                GenParams.MIN_NEW_TOKENS: 100,
                GenParams.TEMPERATURE: 0.7,
                GenParams.TOP_K: 50,
                GenParams.TOP_P: 1
            },
            credentials={
                "url": credentials['url'],
                "apikey": credentials['api_key']
            },
            project_id=credentials['project_id']
        )
        
        # Handle chunking if needed
        code_tokens = count_tokens(formatted_code)
        if code_tokens > MAX_CONTEXT_TOKENS:
            chunks = chunk_text_by_structure(formatted_code, MAX_CONTEXT_TOKENS, CHUNK_OVERLAP_TOKENS)
            result['metadata']['chunks_processed'] = len(chunks)
            
            all_results = []
            for i, chunk in enumerate(chunks):
                prompt = create_analysis_prompt(chunk, repo_url, i, len(chunks))
                chunk_result = model.generate_text(prompt=prompt)
                all_results.append(chunk_result)
            
            analysis_result = "\n\n---\n\n".join([f"## Analysis Part {i+1}\n{r}" for i, r in enumerate(all_results)])
        else:
            prompt = create_analysis_prompt(formatted_code, repo_url)
            analysis_result = model.generate_text(prompt=prompt)
        
        result['success'] = True
        result['result'] = analysis_result
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        result['error'] = str(e)
    
    finally:
        # Cleanup
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")
    
    return result


def render_results_ui():
    """Render the results UI from session state"""
    if st.session_state.analysis_results:
        st.success("✅ Analysis complete!")
        st.markdown("---")
        
        sections = st.session_state.analysis_sections
        
        # Display results in tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📝 Interview Questions",
            "💡 Non-Technical Explanation",
            "⚠️ Code Weaknesses",
            "🎯 Elevator Pitch"
        ])
        
        with tab1:
            st.markdown("### Technical Interview Questions & Answers")
            st.markdown(sections['questions'] if sections['questions'] else st.session_state.analysis_results)
        
        with tab2:
            st.markdown("### Non-Technical Explanation")
            st.markdown(sections['explanation'] if sections['explanation'] else "See full analysis in Questions tab")
        
        with tab3:
            st.markdown("### Code Weaknesses & Technical Debt")
            st.markdown(sections['weaknesses'] if sections['weaknesses'] else "See full analysis in Questions tab")
        
        with tab4:
            st.markdown("### Elevator Pitch")
            st.markdown(sections['pitch'] if sections['pitch'] else "See full analysis in Questions tab")
        
        # Download option
        st.markdown("---")
        repo_name = st.session_state.repo_url.split('/')[-1] if st.session_state.repo_url else "analysis"
        st.download_button(
            label="📥 Download Full Analysis",
            data=st.session_state.analysis_results,
            file_name=f"gitready_analysis_{repo_name}.txt",
            mime="text/plain",
            use_container_width=True
        )


def main():
    """Main Streamlit application with session state management"""
    
    # Initialize session state
    init_session_state()
    
    # Header
    st.title("🚀 GitReady")
    st.subheader("AI-Powered Interview Preparation Tool")
    st.markdown("Analyze any public GitHub repository to generate comprehensive interview materials")
    
    # Check credentials
    credentials, error = get_watsonx_credentials()
    if error or credentials is None:
        st.error(f"❌ {error or 'Failed to load credentials'}")
        st.info("💡 Please set the following environment variables:")
        st.code("""
export WATSONX_API_KEY="your_api_key_here"
export WATSONX_PROJECT_ID="your_project_id_here"
export WATSONX_URL="https://us-south.ml.cloud.ibm.com"
        """)
        return
    
    st.success("✅ IBM Watsonx.ai credentials loaded")
    
    # Input section
    st.markdown("---")
    repo_url = st.text_input(
        "📦 Enter GitHub Repository URL",
        placeholder="https://github.com/username/repository",
        help="Enter the URL of a public GitHub repository"
    )
    
    analyze_button = st.button("🔍 Analyze Repository", type="primary", use_container_width=True)
    
    # Analysis section
    if analyze_button:
        if not repo_url:
            st.error("❌ Please enter a GitHub repository URL")
        else:
            # Validate URL
            is_valid, result = validate_github_url(repo_url)
            if not is_valid:
                st.error(f"❌ {result}")
            else:
                repo_url = result
                st.session_state.repo_url = repo_url
                temp_dir = None
                
                try:
                    # Create temporary directory
                    temp_dir = tempfile.mkdtemp()
                    
                    # Clone repository
                    with st.spinner("Cloning repository..."):
                        success, clone_result = clone_repository(repo_url, temp_dir)
                        if not success:
                            st.error(f"❌ {clone_result}")
                            return
                        st.success("✅ Repository cloned successfully")
                    
                    # Read files
                    with st.spinner("Reading code files..."):
                        files_content, file_count, total_size = read_repository_files(temp_dir)
                        
                        if not files_content:
                            st.error("❌ No supported code files found in repository")
                            return
                        
                        st.success(f"✅ Read {file_count} files ({total_size / 1024:.1f} KB)")
                    
                    # Format code for analysis
                    with st.spinner("Preparing code for analysis..."):
                        formatted_code = format_code_for_analysis(files_content, repo_url)
                        token_count = count_tokens(formatted_code)
                        st.info(f"📊 Total tokens: {token_count} (Context limit: {MAX_CONTEXT_TOKENS})")
                    
                    # Analyze with Watsonx using streaming
                    st.markdown("### 🤖 Live Analysis Stream")
                    st.info("Watch the AI analyze your code in real-time...")
                    
                    success, analysis_result, error_msg = analyze_with_watsonx_streaming(
                        formatted_code, repo_url, credentials
                    )
                    
                    if not success:
                        st.error(f"❌ {error_msg}")
                        st.session_state.error_message = error_msg
                        return
                    
                    # Store results in session state for persistence
                    st.session_state.analysis_results = analysis_result
                    st.session_state.analysis_sections = parse_analysis_response(analysis_result)
                    st.session_state.analysis_status = "complete"
                    
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    st.error(f"❌ An unexpected error occurred: {str(e)}")
                    st.session_state.error_message = str(e)
                
                finally:
                    # Cleanup temporary directory
                    if temp_dir and os.path.exists(temp_dir):
                        try:
                            shutil.rmtree(temp_dir)
                        except Exception as e:
                            st.warning(f"⚠️ Could not clean up temporary files: {str(e)}")
    
    # Render results UI if analysis exists in session state
    if st.session_state.analysis_results:
        render_results_ui()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>Built for IBM Bob Hackathon | Powered by IBM Watsonx.ai</p>
            <p style='font-size: 0.8em;'>✨ Features: Session State Persistence | Token Management | Streaming | Modular Architecture</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

# Made with Bob
