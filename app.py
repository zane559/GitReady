"""
GitReady - AI-Powered Interview Preparation Tool
Analyzes GitHub repositories to generate comprehensive interview materials
Built for IBM Bob Hackathon
"""

import streamlit as st
import os
import tempfile
import shutil
from pathlib import Path
from git import Repo
from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
import json

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


def validate_github_url(url):
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


def clone_repository(repo_url, temp_dir):
    """Clone GitHub repository to temporary directory"""
    try:
        st.info(f"🔄 Cloning repository...")
        repo = Repo.clone_from(repo_url, temp_dir, depth=1)
        return True, repo
    except Exception as e:
        return False, f"Failed to clone repository: {str(e)}"


def is_text_file(file_path):
    """Check if file is a text file by attempting to read it"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(512)  # Read first 512 bytes
        return True
    except (UnicodeDecodeError, PermissionError):
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                f.read(512)
            return True
        except:
            return False


def read_repository_files(repo_path):
    """Recursively read all code files from repository"""
    files_content = []
    total_size = 0
    file_count = 0
    
    repo_path = Path(repo_path)
    
    for file_path in repo_path.rglob('*'):
        # Skip directories and ignored directories
        if file_path.is_dir():
            continue
        
        if any(ignored in file_path.parts for ignored in IGNORE_DIRS):
            continue
        
        # Check file extension or name
        if file_path.suffix not in SUPPORTED_EXTENSIONS and file_path.name not in SUPPORTED_EXTENSIONS:
            continue
        
        # Check file size
        try:
            file_size = file_path.stat().st_size
            if file_size > MAX_FILE_SIZE:
                continue
            
            if total_size + file_size > MAX_TOTAL_SIZE:
                st.warning(f"⚠️ Reached maximum total size limit. Some files may be skipped.")
                break
            
            # Try to read as text file
            if is_text_file(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                relative_path = file_path.relative_to(repo_path)
                files_content.append({
                    'path': str(relative_path),
                    'content': content,
                    'size': file_size
                })
                
                total_size += file_size
                file_count += 1
        
        except Exception as e:
            continue
    
    return files_content, file_count, total_size


def format_code_for_analysis(files_content, repo_url):
    """Format code files into structured text for LLM analysis"""
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    
    formatted_text = f"# Repository: {repo_name}\n"
    formatted_text += f"# URL: {repo_url}\n"
    formatted_text += f"# Total Files: {len(files_content)}\n\n"
    
    # Group files by directory for better organization
    files_by_dir = {}
    for file_info in files_content:
        dir_name = str(Path(file_info['path']).parent)
        if dir_name not in files_by_dir:
            files_by_dir[dir_name] = []
        files_by_dir[dir_name].append(file_info)
    
    # Add file structure overview
    formatted_text += "## File Structure:\n"
    for file_info in files_content:
        formatted_text += f"- {file_info['path']}\n"
    formatted_text += "\n"
    
    # Add file contents
    formatted_text += "## File Contents:\n\n"
    for file_info in files_content:
        formatted_text += f"### File: {file_info['path']}\n"
        formatted_text += f"```\n{file_info['content']}\n```\n\n"
    
    return formatted_text


def get_watsonx_credentials():
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


def create_analysis_prompt(code_content, repo_url):
    """Create detailed prompt for code analysis"""
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    
    prompt = f"""You are an expert technical interviewer analyzing the GitHub repository: {repo_name}

Repository URL: {repo_url}

Your task is to deeply analyze this codebase and generate comprehensive interview preparation materials. You MUST reference actual code implementations, specific function names, class structures, and architectural patterns found in the code.

Here is the complete codebase:

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


def analyze_with_watsonx(code_content, repo_url, credentials):
    """Analyze code using IBM Watsonx.ai"""
    try:
        # Initialize Watsonx model
        model = Model(
            model_id="ibm/granite-13b-chat-v2",
            params={
                GenParams.DECODING_METHOD: "greedy",
                GenParams.MAX_NEW_TOKENS: 4000,
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
        
        # Create prompt
        prompt = create_analysis_prompt(code_content, repo_url)
        
        # Generate analysis
        st.info("🤖 Analyzing code with IBM Watsonx.ai...")
        response = model.generate_text(prompt=prompt)
        
        return True, response
    
    except Exception as e:
        return False, f"Watsonx.ai analysis failed: {str(e)}"


def parse_analysis_response(response_text):
    """Parse the AI response into structured sections"""
    sections = {
        'questions': '',
        'explanation': '',
        'weaknesses': '',
        'pitch': ''
    }
    
    # Split by section headers
    parts = response_text.split('##')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        if '1.' in part and 'TECHNICAL INTERVIEW QUESTIONS' in part.upper():
            sections['questions'] = part.split('\n', 1)[1].strip() if '\n' in part else part
        elif '2.' in part and 'NON-TECHNICAL EXPLANATION' in part.upper():
            sections['explanation'] = part.split('\n', 1)[1].strip() if '\n' in part else part
        elif '3.' in part and 'WEAKNESSES' in part.upper() or 'TECHNICAL DEBT' in part.upper():
            sections['weaknesses'] = part.split('\n', 1)[1].strip() if '\n' in part else part
        elif '4.' in part and 'ELEVATOR PITCH' in part.upper():
            sections['pitch'] = part.split('\n', 1)[1].strip() if '\n' in part else part
    
    return sections


def main():
    """Main Streamlit application"""
    
    # Header
    st.title("🚀 GitReady")
    st.subheader("AI-Powered Interview Preparation Tool")
    st.markdown("Analyze any public GitHub repository to generate comprehensive interview materials")
    
    # Check credentials
    credentials, error = get_watsonx_credentials()
    if error:
        st.error(f"❌ {error}")
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
            return
        
        # Validate URL
        is_valid, result = validate_github_url(repo_url)
        if not is_valid:
            st.error(f"❌ {result}")
            return
        
        repo_url = result
        temp_dir = None
        
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            
            # Clone repository
            with st.spinner("Cloning repository..."):
                success, result = clone_repository(repo_url, temp_dir)
                if not success:
                    st.error(f"❌ {result}")
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
            
            # Analyze with Watsonx
            with st.spinner("Analyzing with IBM Watsonx.ai... This may take a minute..."):
                success, analysis_result = analyze_with_watsonx(formatted_code, repo_url, credentials)
                
                if not success:
                    st.error(f"❌ {analysis_result}")
                    return
            
            # Parse and display results
            st.success("✅ Analysis complete!")
            st.markdown("---")
            
            sections = parse_analysis_response(analysis_result)
            
            # Display results in tabs
            tab1, tab2, tab3, tab4 = st.tabs([
                "📝 Interview Questions",
                "💡 Non-Technical Explanation",
                "⚠️ Code Weaknesses",
                "🎯 Elevator Pitch"
            ])
            
            with tab1:
                st.markdown("### Technical Interview Questions & Answers")
                st.markdown(sections['questions'] if sections['questions'] else analysis_result)
            
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
            st.download_button(
                label="📥 Download Full Analysis",
                data=analysis_result,
                file_name=f"gitready_analysis_{repo_url.split('/')[-1]}.txt",
                mime="text/plain"
            )
        
        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {str(e)}")
        
        finally:
            # Cleanup temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    st.warning(f"⚠️ Could not clean up temporary files: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>Built for IBM Bob Hackathon | Powered by IBM Watsonx.ai</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

# Made with Bob
