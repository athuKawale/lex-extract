import os
import sys
import json
from dotenv import load_dotenv

# Add project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.graph import graph

load_dotenv()

def main():
    print("Starting PDF Extraction Workflow!")
    
    pdf_path = os.getenv("PDF_PATH", "input/POC_TEST_SPA.pdf")
    
    # Define inputs for the state
    inputs = {
        "pdf_path": pdf_path,
        "pdf_text": "",
        "extracted_fields": {},
        "fields_to_retry": [],
        "retry_count": 0,
        "final_output": {},
        "messages": [],
        "attributes_to_extract": {
             "Party Name": "Name of the entity or individual",
             "Effective Date": "The date when the agreement takes effect",
             "Governing Law": "State or jurisdiction whose laws govern the agreement"
        }
    }
    
    # Run the graph
    try:
        final_state = graph.invoke(inputs)
        
        print("\n=== FINAL EXTRACTED JSON ===")
        print(json.dumps(final_state.get("final_output", {}), indent=2))
        
        # Save output to a file
        with open("output.json", "w") as f:
            json.dump(final_state.get("final_output", {}), f, indent=2)
            
        print("\nResults saved to output.json")
        
    except Exception as e:
        print(f"\nWorkflow failed: {e}")

if __name__ == "__main__":
    main()
