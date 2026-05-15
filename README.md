# 🚀 GitReady

**AI-Powered Interview Preparation Tool**

GitReady analyzes any public GitHub repository to generate comprehensive interview preparation materials using IBM Watsonx.ai. Built for the IBM Bob Hackathon.

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