#!/usr/bin/env bash
# AIGBooks 端到端冒烟测试：跑通举报 → 聚合 → 搜索 → 投票 → RSS 全链路。
# 要求：AIGBOOKS_API 已启动（如 http://localhost:8000）

set -euo pipefail

BASE=${AIGBOOKS_API:-http://localhost:8000}
FP=${E2E_FP:-"e2e-test-$(uuidgen 2>/dev/null || date +%s)"}
ISBN="9787000000001"

echo "==== AIGBooks E2E ===="
echo "BASE=$BASE  FP=$FP"

# 1. POST /api/reports
echo ""
echo "1) POST /api/reports (new ISBN)"
RID=$(curl -sf -X POST "$BASE/api/reports" \
  -F "isbn=$ISBN" \
  -F "title=测试书 E2E" \
  -F "author=测试作者" \
  -F "description=这是一本测试书籍，用于 E2E 验证。" \
  -F "fingerprint=$FP" | jq -r '.id')
echo "   report_id=$RID"

# 2. POST /api/reports 同 ISBN 聚合
echo ""
echo "2) POST /api/reports (same ISBN → aggregate)"
COUNT=$(curl -sf -X POST "$BASE/api/reports" \
  -F "isbn=$ISBN" \
  -F "title=测试书 E2E" \
  -F "author=测试作者" \
  -F "description=第二条举报，应聚合并使 book.report_count = 2。" \
  -F "fingerprint=$FP" | jq '.book.report_count')
echo "   book.report_count=$COUNT"
[[ "$COUNT" == "2" ]] || { echo "❌ aggregation failed"; exit 1; }

# 3. GET /api/search?q=
echo ""
echo "3) GET /api/search?q=测试书"
HITS=$(curl -sf "$BASE/api/search?q=测试书" | jq '.reports | length')
echo "   hits=$HITS"
[[ "$HITS" -ge 2 ]] || { echo "❌ search failed"; exit 1; }

# 4. POST /api/reports/{id}/vote
echo ""
echo "4) POST /api/reports/$RID/vote"
UV=$(curl -sf -X POST "$BASE/api/reports/$RID/vote" \
  -H "X-Fingerprint: $FP" \
  -H "Content-Type: application/json" \
  -d '{"vote_type": 1, "fingerprint": "'"$FP"'"}' | jq '.upvote')
echo "   upvote=$UV"
[[ "$UV" == "1" ]] || { echo "❌ vote failed"; exit 1; }

# 5. GET /api/feed/reports.rss
echo ""
echo "5) GET /api/feed/reports.rss"
CT=$(curl -sf -I "$BASE/api/feed/reports.rss" | grep -i "^content-type:" | tr -d '\r' | awk '{print tolower($2)}')
echo "   content-type=$CT"
[[ "$CT" == "application/rss+xml;charset=utf-8" || "$CT" == "application/rss+xml; charset=utf-8" ]] || { echo "❌ RSS content-type failed"; exit 1; }

echo ""
echo "✅ E2E 全部通过"