#!/bin/bash
# Monitor embedding generation progress

echo "==================================================================="
echo "EMBEDDING GENERATION MONITOR"
echo "==================================================================="
echo ""

# Check if process is running
PID=$(ps aux | grep "generate_lecture_segment_embeddings.py" | grep -v grep | awk '{print $2}' | head -1)

if [ -z "$PID" ]; then
    echo "❌ Process not running"
    exit 1
fi

# Get process info
UPTIME=$(ps -p $PID -o etime= | xargs)
CPU=$(ps -p $PID -o %cpu= | xargs)
MEM=$(ps -p $PID -o %mem= | xargs)

echo "📊 Process Status:"
echo "   PID: $PID"
echo "   Runtime: $UPTIME"
echo "   CPU: $CPU%"
echo "   Memory: $MEM%"
echo ""

# Check if output file exists
if [ -f "lecture_segments_embeddings.json" ]; then
    SIZE=$(ls -lh lecture_segments_embeddings.json | awk '{print $5}')
    echo "📁 Output File:"
    echo "   File: lecture_segments_embeddings.json"
    echo "   Size: $SIZE"
    echo ""

    # Estimate progress (rough)
    BYTES=$(stat -f%z lecture_segments_embeddings.json 2>/dev/null || stat -c%s lecture_segments_embeddings.json 2>/dev/null)
    EXPECTED=650000000  # ~620MB expected
    PERCENT=$((BYTES * 100 / EXPECTED))
    echo "   Progress: ~$PERCENT% (estimated)"
else
    echo "📁 Output File: Not created yet (still processing)"
fi

echo ""
echo "⏱️  Total chunks: 59,685"
echo "   Estimated completion: ~20-25 minutes total"
echo ""
echo "To check again: bash monitor_embeddings.sh"
echo "==================================================================="
