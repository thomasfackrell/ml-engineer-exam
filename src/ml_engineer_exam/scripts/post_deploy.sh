#!/bin/bash
# post_deploy.sh - Verifies the live production API after a successful deployment.

URL=$1

if [ -z "$URL" ]; then
  echo "Error: No API URL provided."
  echo "Usage: ./post_deploy.sh <API_URL>"
  exit 1
fi

echo "========================================================"
echo "🚀 STARTING PRODUCTION SMOKE TEST"
echo "Target URL: $URL"
echo "========================================================"

# We iterate through all 3 models to ensure the live Lambda 
# can lazily load and execute each one correctly.
models=("linear" "ridge" "random_forest")

for model in "${models[@]}"; do
  echo "--- Testing Model: $model ---"
  uv run python tests/verify_inference.py --url "$URL" --model "$model"
  if [ $? -ne 0 ]; then
    echo "❌ Smoke test failed for model: $model"
    exit 1
  fi
done

echo "========================================================"
echo "✅ ALL PRODUCTION SMOKE TESTS PASSED!"
echo "========================================================"
