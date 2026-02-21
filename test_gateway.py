#!/usr/bin/env python3
"""
Test script for Hailo Ollama Gateway validation.

Tests basic chat, streaming, and tool calling support without requiring
a full Strands agent implementation.

Usage:
  1. Start the gateway: python hailo_ollama_gateway.py (from gateway directory)
  2. Run this script: python test_gateway.py
"""

import requests
import json
import sys
import time

# Configuration
GATEWAY_PORT = 11434
GATEWAY_URL = f"http://localhost:{GATEWAY_PORT}"
TIMEOUT = 120

def check_gateway_running():
    """Verify gateway is accessible"""
    print("\n[PRE-CHECK] Verifying gateway is running...")
    try:
        response = requests.get(f"{GATEWAY_URL}/docs", timeout=2)
        print("✓ Gateway is running on port 11434")
        return True
    except requests.exceptions.RequestException:
        print("✗ Gateway is not running")
        print("\nStart the gateway with:")
        print("  cd /path/to/ollama_gateway")
        print("  export HAILO_HEF_PATH=/path/to/qwen2_1.5b.hef")
        print("  python hailo_ollama_gateway.py")
        return False

def test_basic_chat():
    """Test basic chat without tools"""
    print("\n[TEST 1] Basic chat request (no tools)...")
    try:
        response = requests.post(
            f"{GATEWAY_URL}/api/chat",
            json={
                "model": "qwen2:1.5b",
                "messages": [
                    {"role": "user", "content": "Hello, what is 2+2?"}
                ],
                "stream": False
            },
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            result = response.json()
            print("✓ Basic chat request succeeded")
            print(f"  Status: {response.status_code}")
            print(f"  Response keys: {list(result.keys())}")
            if "message" in result:
                content = result["message"].get("content", "")[:100]
                print(f"  First 100 chars: {content}...")
            return True
        else:
            print(f"✗ HTTP {response.status_code}")
            print(f"  Error: {response.text[:200]}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_streaming():
    """Test streaming response"""
    print("\n[TEST 2] Streaming chat request...")
    try:
        response = requests.post(
            f"{GATEWAY_URL}/api/chat",
            json={
                "model": "qwen2:1.5b",
                "messages": [
                    {"role": "user", "content": "Say hello"}
                ],
                "stream": True
            },
            timeout=TIMEOUT,
            stream=True
        )
        if response.status_code == 200:
            print("✓ Streaming request succeeded")
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        chunk_count += 1
                    except json.JSONDecodeError:
                        pass
            print(f"  Received {chunk_count} response chunks")
            return True
        else:
            print(f"✗ HTTP {response.status_code}")
            print(f"  Error: {response.text[:200]}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_with_tools():
    """Test chat with tools (the critical test)"""
    print("\n[TEST 3] Chat request WITH tools field (CRITICAL)...")
    try:
        response = requests.post(
            f"{GATEWAY_URL}/api/chat",
            json={
                "model": "qwen2:1.5b",
                "messages": [
                    {"role": "user", "content": "What's the weather?"}
                ],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "description": "Get the weather for a location",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "location": {
                                        "type": "string",
                                        "description": "City name"
                                    }
                                },
                                "required": ["location"]
                            }
                        }
                    }
                ],
                "stream": False
            },
            timeout=TIMEOUT
        )

        if response.status_code == 200:
            result = response.json()
            print("✓ Tools field ACCEPTED (no HTTP 500 error!)")
            print(f"  Status: {response.status_code}")
            print(f"  Response keys: {list(result.keys())}")

            # Check if model attempted to call a tool
            message = result.get("message", {})
            if "tool_calls" in message or "tools" in result:
                print("  → Model generated tool calls")
            else:
                print("  → Model generated text response (not attempting to call tools)")

            return True
        elif response.status_code == 500:
            print("✗ HTTP 500 error - gateway doesn't handle tools field")
            print(f"  Error: {response.text[:300]}")
            return False
        else:
            print(f"✗ HTTP {response.status_code}")
            print(f"  Error: {response.text[:200]}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_model_list():
    """Test model listing endpoint"""
    print("\n[TEST 4] Model listing endpoint...")
    try:
        response = requests.get(
            f"{GATEWAY_URL}/api/tags",
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            result = response.json()
            print("✓ Model list endpoint works")
            models = result.get("models", [])
            print(f"  Available models: {len(models)}")
            for model in models:
                print(f"    - {model.get('name', 'unknown')}")
            return True
        else:
            print(f"✗ HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def main():
    print("=" * 70)
    print("HAILO OLLAMA GATEWAY - VALIDATION TEST SUITE")
    print("=" * 70)

    # Pre-check
    if not check_gateway_running():
        sys.exit(1)

    # Run tests
    results = {}
    results["model_list"] = test_model_list()
    results["basic_chat"] = test_basic_chat()
    results["streaming"] = test_streaming()
    results["tools"] = test_with_tools()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name:20} {status}")

    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"\nResult: {passed_count}/{total_count} tests passed")

    if results["tools"]:
        print("\n✓✓✓ GATEWAY SUPPORTS TOOLS! Ready for Strands integration.")
        sys.exit(0)
    else:
        print("\n✗✗✗ TOOLS NOT WORKING. Need to investigate further.")
        sys.exit(1)

if __name__ == "__main__":
    main()
