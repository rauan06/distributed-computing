#!/bin/bash
# Local testing script for MapReduce job
# This tests the mapper and reducer pipeline locally before running on EMR

echo "=== Local MapReduce Test ==="
echo "Creating sample input file..."

# Create sample input
cat > sample_input.txt << 'EOF'
Hello world hello
MapReduce is a programming model
MapReduce processes big data
Hello big data world
EOF

echo "Sample input created:"
cat sample_input.txt
echo ""

echo "=== Testing Mapper ==="
cat sample_input.txt | python3 mapper.py
echo ""

echo "=== Testing Full Pipeline (Mapper -> Sort -> Reducer) ==="
cat sample_input.txt | python3 mapper.py | sort -k1,1 | python3 reducer.py
echo ""

echo "=== Expected Output ==="
echo "Word counts for the sample input should show:"
echo "- 'hello' appears 2 times"
echo "- 'world' appears 2 times"
echo "- 'mapreduce' appears 2 times"
echo "- 'big' appears 2 times"
echo "- 'data' appears 2 times"
echo ""

echo "Test complete!"