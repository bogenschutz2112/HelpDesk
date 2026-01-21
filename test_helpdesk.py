#!/usr/bin/env python3
"""
Simple test script to verify AI Helpdesk MVP functionality.
This demonstrates the basic operations without needing Anthropic API key.
"""

import json
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from helpdesk.app import (
    read_markdown_files,
    simple_search,
    llm_complete,
    ensure_dirs,
    save_ticket_locally,
)

def test_knowledge_base():
    """Test KB loading and search."""
    print("=" * 60)
    print("TEST 1: Knowledge Base Loading and Search")
    print("=" * 60)
    
    docs = read_markdown_files()
    print(f"✓ Loaded {len(docs)} documents from KB")
    for doc in docs:
        print(f"  - {doc['title']} ({doc['path']})")
    
    # Test search
    query = "VPN not connecting"
    hits = simple_search(query, docs)
    print(f"\n✓ Search for '{query}' found {len(hits)} results")
    for hit in hits:
        print(f"  - {hit.title} (score: {hit.score})")
    
    return len(docs) > 0 and len(hits) > 0

def test_llm_complete():
    """Test LLM completion with heuristic fallback."""
    print("\n" + "=" * 60)
    print("TEST 2: LLM Completion (Heuristic Mode)")
    print("=" * 60)
    
    docs = read_markdown_files()
    query = "VPN won't connect"
    hits = simple_search(query, docs)
    
    system_prompt = "You are a helpful helpdesk assistant."
    result = llm_complete(system_prompt, query, hits)
    
    print(f"✓ Question: {query}")
    print(f"✓ Confidence: {result['confidence']}")
    print(f"✓ Escalate: {result['escalate']}")
    print(f"✓ Sources: {len(result['kb_sources'])} KB sources found")
    print(f"✓ Answer preview: {result['answer'][:100]}...")
    
    return result['confidence'] > 0 and len(result['kb_sources']) > 0

def test_ticket_creation():
    """Test ticket creation."""
    print("\n" + "=" * 60)
    print("TEST 3: Ticket Creation")
    print("=" * 60)
    
    ensure_dirs()
    
    ticket_data = {
        "summary": "Test ticket",
        "details": "This is a test ticket for validation",
        "user": {"id": "test123", "email": "test@example.com"},
        "labels": ["test", "validation"]
    }
    
    ticket = save_ticket_locally(ticket_data)
    print(f"✓ Created ticket #{ticket['id']}")
    print(f"  Summary: {ticket['summary']}")
    print(f"  User: {ticket['user']['id']}")
    
    return ticket['id'] > 0

def main():
    """Run all tests."""
    print("\n🚀 AI Helpdesk MVP - Test Suite\n")
    
    tests = [
        ("Knowledge Base", test_knowledge_base),
        ("LLM Completion", test_llm_complete),
        ("Ticket Creation", test_ticket_creation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ TEST FAILED: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
