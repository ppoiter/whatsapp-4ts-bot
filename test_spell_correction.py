#!/usr/bin/env python3

# Simple test script for the spell correction functionality
import sys
sys.path.append('.')

from utils.text_utils import parse_player_picks, correct_player_name

def test_spell_correction():
    print("Testing spell correction functionality...")
    
    # Test individual corrections
    test_cases = [
        ("halland", "Haaland"),
        ("Halland", "Haaland"), 
        ("HALLAND", "Haaland"),
        ("richalison", "Richarlison"),
        ("morgan rogers", "Rogers"),
        ("calvert-lewin", "DCL"),
        ("Salah", "Salah"),  # Should remain unchanged
        ("Unknown Player", "Unknown Player")  # Should remain unchanged
    ]
    
    print("\n1. Testing individual name corrections:")
    for input_name, expected in test_cases:
        result = correct_player_name(input_name)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"   {status} '{input_name}' -> '{result}' (expected: '{expected}')")
    
    # Test full message parsing
    print("\n2. Testing full message parsing:")
    
    test_messages = [
        {
            "message": "halland\nSalah\nrichalison\nmorgan rogers",
            "expected": ["Haaland", "Salah", "Richarlison", "Rogers"]
        },
        {
            "message": "CALVERT-LEWIN\nKane\nSon\nFoden", 
            "expected": ["DCL", "Kane", "Son", "Foden"]
        },
        {
            "message": "Normal Player\nAnother Player\nhalland\nLast Player",
            "expected": ["Normal Player", "Another Player", "Haaland", "Last Player"]
        }
    ]
    
    for i, test in enumerate(test_messages, 1):
        result = parse_player_picks(test["message"])
        status = "✅ PASS" if result == test["expected"] else "❌ FAIL"
        print(f"   Test {i}: {status}")
        print(f"      Input: {test['message'].replace(chr(10), ' | ')}")
        print(f"      Result: {result}")
        print(f"      Expected: {test['expected']}")
        print()

if __name__ == "__main__":
    test_spell_correction()