#!/usr/bin/env bash
# AIGBooks 接口清单：直接从 FastAPI 自动生成的 /openapi.json 解析。
#
# 用法：
#   AIGBOOKS_API=http://localhost:8000 ./scripts/api-list.sh
#
# 输出：METHOD  PATH  TAG  SUMMARY（一行一条）。
# 依赖：curl, jq。

set -euo pipefail

BASE=${AIGBOOKS_API:-http://localhost:8000}

echo "==== AIGBooks API 清单（来源: $BASE/openapi.json） ===="
echo ""

curl -sf "$BASE/openapi.json" | jq -r '
  .paths | to_entries[] as $path
    | $path.value | to_entries[] as $op
    | [$op.key | ascii_upcase,
       $path.key,
       ($op.value.tags // [""] | join(",")),
       ($op.value.summary // "")]
    | @tsv
' | column -t -s $'\t'

echo ""
echo "（含业务 /api/*、FastAPI 自动生成 /openapi.json /docs /redoc）"