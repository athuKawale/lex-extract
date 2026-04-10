import sys
import os
import warnings
from streamlit.web import cli as stcli

# Suppress annoying __path__ access warnings from certain internal libraries
warnings.filterwarnings("ignore", message=".*Accessing __path__ from.*")

def main():
    """
    Launcher for the LexExtract Streamlit application.
    This allows the application to be started using 'python main.py'.
    """
    # Get the path to the streamlit app script
    script_path = os.path.join(os.path.dirname(__file__), "frontend", "legal_extractor_app.py")
    
    # Configure arguments for streamlit run
    sys.argv = [
        "streamlit",
        "run",
        script_path,
        "--server.port=8501",
        "--server.address=0.0.0.0",
    ]
    
    # Execute streamlit
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
