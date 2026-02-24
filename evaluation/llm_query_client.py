#!/usr/bin/env python3
"""
Simple client for the IGVF Catalog llm-query endpoint.

Usage:
    python llm_query_client.py "Your question here"
    
Environment Variables:
    IGVF_LLM_QUERY_PASSWORD - Required password for the API
    IGVF_CATALOG_API_URL - Optional API base URL (default: https://api.catalogkg.igvf.org)
"""

import json
import os
import sys
import urllib.request
import urllib.error


def query_llm(question: str, verbose: bool = False) -> dict:
    """
    Send a question to the IGVF Catalog llm-query endpoint.
    
    Args:
        question: The question to ask
        verbose: Whether to request verbose output
        
    Returns:
        dict with 'success', 'answer' or 'error' keys
    """
    password = os.environ.get("IGVF_LLM_QUERY_PASSWORD", "")
    base_url = os.environ.get("IGVF_CATALOG_API_URL", "https://api.catalogkg.igvf.org")
    
    if not password:
        return {
            "success": False,
            "error": "IGVF_LLM_QUERY_PASSWORD environment variable is not set"
        }
    
    url = f"{base_url}/api/llm-query"
    
    payload = {
        "query": question,
        "password": password,
        "verbose": str(verbose).lower()
    }
    
    data = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            
            # Extract the answer from the response
            # The response structure may vary, try common patterns
            if isinstance(result, dict):
                answer = result.get("answer") or result.get("response") or result.get("result") or str(result)
            else:
                answer = str(result)
                
            return {
                "success": True,
                "answer": answer,
                "raw_response": result
            }
            
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
        except:
            pass
        return {
            "success": False,
            "error": f"HTTP {e.code}: {e.reason}",
            "details": error_body
        }
        
    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": f"Connection error: {e.reason}"
        }
        
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON response: {e}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {e}"
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python llm_query_client.py \"Your question here\"", file=sys.stderr)
        print("\nEnvironment Variables:", file=sys.stderr)
        print("  IGVF_LLM_QUERY_PASSWORD - Required password for the API", file=sys.stderr)
        print("  IGVF_CATALOG_API_URL - Optional API base URL", file=sys.stderr)
        sys.exit(1)
    
    question = sys.argv[1]
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    result = query_llm(question, verbose=verbose)
    
    # Output as JSON for easy parsing
    print(json.dumps(result, indent=2))
    
    # Exit with error code if failed
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
