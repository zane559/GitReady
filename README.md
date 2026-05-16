# 🚀 GitReady

**AI-Powered Interview Preparation Tool**

GitReady analyzes any public GitHub repository to generate comprehensive interview preparation materials using IBM Watsonx.ai. Built entirely with **IBM Bob IDE** for the IBM Bob Hackathon.

## 🤖 Built with IBM Bob IDE

**This entire application was designed, developed, and refined using IBM Bob IDE** - IBM's AI-powered development assistant. Bob served as the primary development tool, handling everything from initial architecture decisions to final code implementation.

### How Bob Built GitReady

IBM Bob IDE was instrumental in every phase of development:

1. **Architecture Design**
   - Bob analyzed the requirements and recommended a single-file Streamlit architecture for simplicity
   - Suggested optimal file processing patterns to handle diverse codebases
   - Designed the four-tab output structure for interview preparation materials

2. **Watsonx.ai Integration**
   - Bob researched and implemented the IBM Watsonx.ai Python SDK integration
   - Crafted specialized prompts for each analysis type (technical questions, weaknesses, elevator pitch)
   - Configured optimal model parameters (temperature, token limits) for consistent results
   - Implemented proper error handling for API calls and credential management

3. **Code Implementation**
   - Generated the complete `app.py` with all core functionality
   - Implemented repository cloning with GitPython and proper cleanup patterns
   - Built file filtering logic to handle binary files and ignore dependency directories
   - Created the Streamlit UI with tabs, error states, and download functionality

4. **Prompt Engineering**
   - Designed the `create_analysis_prompt()` function with context-aware instructions
   - Ensured prompts explicitly reference actual code to avoid generic responses
   - Optimized prompt structure to work within Granite model token limits

5. **Testing & Refinement**
   - Debugged encoding issues with diverse repository file types
   - Fixed Windows path handling using `pathlib.Path` objects
   - Optimized file size limits to prevent memory issues
   - Added comprehensive error messages for better user experience

### Bob's Development Workflow

```
User Request → Bob Analysis → Code Generation → Testing → Refinement
     ↓              ↓              ↓              ↓          ↓
  "Build an    Researched     Generated      Identified   Fixed bugs,
   interview   Watsonx.ai     complete       edge cases   optimized
   prep tool"  SDK & best     app.py with    (encoding,   performance
               practices      all features   paths)
```

### Key Bob-Generated Components

- **Repository Analysis Engine**: Bob designed the file traversal logic that handles 20+ programming languages
- **AI Prompt Templates**: Bob crafted four specialized prompts optimized for Granite models
- **Error Handling**: Bob implemented comprehensive try/except patterns with user-friendly messages
- **Cleanup Logic**: Bob ensured proper temporary directory cleanup using try/finally blocks

### Bob Session Exports

All development sessions with Bob are documented in the `bob_sessions/` folder, showing:
- Initial project setup and architecture decisions
- Iterative refinements and bug fixes
- Prompt engineering iterations
- Testing and optimization steps

**IBM Bob IDE transformed a concept into a production-ready application in record time**, demonstrating the power of AI-assisted development for hackathon projects.

## 🎯 Features

GitReady takes a GitHub repository URL and generates:

1. **10 Technical Interview Questions** - Deep-dive questions with detailed answers based on actual code implementation
2. **Non-Technical Explanation** - Clear, jargon-free project description suitable for non-developers
3. **Code Weaknesses Analysis** - Identification of technical debt, vulnerabilities, and areas interviewers might probe
4. **Elevator Pitch** - A compelling one-liner that captures the project's essence

## 🛠️ Technology Stack

- **Frontend**: Streamlit (Python web framework)
- **AI Engine**: IBM Watsonx.ai with Granite models
- **Repository Analysis**: GitPython
- **Language**: Python 3.8+

## 📋 Prerequisites

- Python 3.8 or higher
- IBM Watsonx.ai account with API credentials
- Git installed on your system

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/zane559/GitReady.git
cd GitReady
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure IBM Watsonx.ai Credentials

Set the following environment variables with your IBM Watsonx.ai credentials:

**Windows (PowerShell):**
```powershell
$env:WATSONX_API_KEY="your_api_key_here"
$env:WATSONX_PROJECT_ID="your_project_id_here"
$env:WATSONX_URL="https://us-south.ml.cloud.ibm.com"
```

**Windows (Command Prompt):**
```cmd
set WATSONX_API_KEY=your_api_key_here
set WATSONX_PROJECT_ID=your_project_id_here
set WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

**Linux/Mac:**
```bash
export WATSONX_API_KEY="your_api_key_here"
export WATSONX_PROJECT_ID="your_project_id_here"
export WATSONX_URL="https://us-south.ml.cloud.ibm.com"
```

**Alternative: Using .env file (recommended)**

Create a `.env` file in the project root:
```
WATSONX_API_KEY=your_api_key_here
WATSONX_PROJECT_ID=your_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

### 4. Run the Application

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

## 📖 Usage

1. **Enter GitHub URL**: Paste the URL of any public GitHub repository
2. **Click Analyze**: The app will clone the repository and analyze the code
3. **View Results**: Browse through the four tabs:
   - 📝 Interview Questions
   - 💡 Non-Technical Explanation
   - ⚠️ Code Weaknesses
   - 🎯 Elevator Pitch
4. **Download**: Save the complete analysis as a text file

## 🎨 Application Architecture

```
GitReady/
├── app.py              # Main Streamlit application (single file)
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### Key Components (all in app.py):

- **Repository Cloning**: Uses GitPython to clone repos to temporary directories
- **Code Ingestion**: Recursively reads text/code files, filters binary files
- **AI Analysis**: Connects to IBM Watsonx.ai Granite models with specialized prompts
- **UI/UX**: Clean Streamlit interface with error handling and loading states
- **Cleanup**: Automatic temporary directory cleanup

## 🔒 Security & Privacy

- Only analyzes **public** GitHub repositories
- Temporary files are automatically deleted after analysis
- No code is stored permanently
- API credentials are loaded from environment variables

## ⚙️ Configuration

### Supported File Types

The application analyzes common code file extensions:
- Python (.py)
- JavaScript/TypeScript (.js, .jsx, .ts, .tsx)
- Java (.java)
- C/C++ (.c, .cpp, .h, .hpp)
- C# (.cs)
- Go (.go)
- Rust (.rs)
- Ruby (.rb)
- PHP (.php)
- Swift (.swift)
- Kotlin (.kt)
- Scala (.scala)
- And more...

### Ignored Directories

The following directories are automatically skipped:
- `.git`, `node_modules`, `__pycache__`
- `.venv`, `venv`, `env`
- `dist`, `build`, `.next`, `.nuxt`
- `target`, `bin`, `obj`
- `.idea`, `.vscode`, `coverage`

## 🐛 Troubleshooting

### "Missing IBM Watsonx.ai credentials"
- Ensure environment variables are set correctly
- Verify your API key and Project ID are valid
- Check that the Watsonx URL is correct for your region

### "Failed to clone repository"
- Verify the GitHub URL is correct and public
- Check your internet connection
- Ensure Git is installed on your system

### "No supported code files found"
- The repository might only contain binary files or unsupported formats
- Check if the repository has actual code files

### Import Errors
- Run `pip install -r requirements.txt` again
- Ensure you're using Python 3.8 or higher

## 🤝 Contributing

This project was built for the IBM Bob Hackathon. Contributions, issues, and feature requests are welcome!

## 📝 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

Built with ❤️ for the IBM Bob Hackathon

## 🙏 Acknowledgments

- IBM Watsonx.ai for providing the AI analysis capabilities
- Streamlit for the excellent web framework
- GitPython for repository management

---

**Note**: This tool is designed for interview preparation and educational purposes. Always respect repository licenses and usage terms.