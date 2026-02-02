#!/usr/bin/env python3
"""
Mapper for Word Count MapReduce Job
Reads input from stdin and emits (word, 1) pairs
"""

import sys
import re

def main():
    """
    Read from stdin, tokenize words, and emit (word, 1) for each word
    """
    for line in sys.stdin:
        # Remove leading/trailing whitespace
        line = line.strip()
        
        # Convert to lowercase and split into words
        # Using regex to split on non-alphanumeric characters
        words = re.findall(r'\b[a-z]+\b', line.lower())
        
        # Emit each word with count of 1
        for word in words:
            if word:  # Skip empty strings
                # Output format: word\t1
                print(f"{word}\t1")

if __name__ == "__main__":
    main()