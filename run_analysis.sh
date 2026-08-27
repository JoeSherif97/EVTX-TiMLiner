#!/bin/bash
# EVTX Timeline Analyzer - One-Command Analysis
# Usage: ./run_analysis.sh <path_to_evtx_file>

echo "========================================="
echo "🔍 EVTX Timeline Analyzer"
echo "========================================="

if [ -z "$1" ]; then
    echo "❌ Please provide a file path"
    echo "Usage: ./run_analysis.sh path/to/file.evtx"
    exit 1
fi

FILE=$1

if [ ! -f "$FILE" ]; then
    echo "❌ File not found: $FILE"
    exit 1
fi

echo "📁 Analyzing: $FILE"
echo ""

# Run the analysis
python3 analyze_evtx.py "$FILE" --json

# Generate visualization
python3 visualize_chain.py "$FILE"

echo ""
echo "✅ Analysis complete!"
echo "📄 Report: $(dirname "$FILE")/$(basename "$FILE" .evtx)_report.txt"
echo "📊 Graph: $(dirname "$FILE")/$(basename "$FILE" .evtx)_chain.png"
echo "📋 JSON: $(dirname "$FILE")/$(basename "$FILE" .evtx)_data.json"
