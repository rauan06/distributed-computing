#!/usr/bin/env python3
"""
Reducer for Word Count MapReduce Job
Reads (word, count) pairs from stdin and aggregates counts for each word
"""

import sys
from collections import defaultdict

def main():
    """
    Read from stdin, aggregate counts by word, and emit (word, total_count)
    """
    word_counts = defaultdict(int)
    
    for line in sys.stdin:
        # Remove leading/trailing whitespace
        line = line.strip()
        
        # Parse the key-value pair
        try:
            word, count = line.split('\t', 1)
            count = int(count)
            word_counts[word] += count
        except ValueError:
            # Skip malformed lines
            continue
    
    # Emit the aggregated counts
    for word, count in sorted(word_counts.items()):
        print(f"{word}\t{count}")

if __name__ == "__main__":
    main()