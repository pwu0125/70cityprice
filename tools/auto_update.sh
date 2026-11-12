#!/bin/bash
# ============================================================
# 70城房价数据自动更新脚本
# 用途: 每月自动从国家统计局抓取最新70城房价数据并更新CSV
# 用法: ./auto_update.sh                    # 交互模式（有输出到终端）
#        ./auto_update.sh --quiet            # 静默模式（仅日志）
#       crontab: 0 10 16 * * /path/to/auto_update.sh --quiet
# ============================================================
set -o pipefail

PROJECT_DIR="/Users/pyemini/projects/70cityprice"
PYTHON="/Users/pyemini/anaconda3/envs/xbxpy312/bin/python3"
LOGFILE="$PROJECT_DIR/logs/70cityprice_update_$(date +%Y%m).log"
mkdir -p "$PROJECT_DIR/logs"
NBS_PAGE_URL="https://www.stats.gov.cn/sj/zxfb/"
QUIET_MODE=false

[[ "$1" == "--quiet" ]] && QUIET_MODE=true

# ── logging helpers ────────────────────────────────────────
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOGFILE"
}
quiet_log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOGFILE"
}
if $QUIET_MODE; then
    _log() { quiet_log "$@"; }
else
    _log() { log "$@"; }
fi

_log "=========================================="
_log "70cityprice auto-update started"
_log "=========================================="

# ── Step 1: Fetch NBS release page ─────────────────────────
_log "📡 Fetching NBS release page: $NBS_PAGE_URL"

NBS_PAGE=$(curl -sL --max-time 30 \
    -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
    "$NBS_PAGE_URL" 2>> "$LOGFILE")

if [ -z "$NBS_PAGE" ]; then
    _log "⚠️  curl returned empty page, trying Python requests fallback..."
    NBS_PAGE=$($PYTHON -c "
import requests
try:
    r = requests.get('$NBS_PAGE_URL', timeout=30,
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'})
    r.raise_for_status()
    print(r.text)
except Exception as e:
    print(f'ERROR: {e}', file=__import__('sys').stderr)
    exit(1)
" 2>> "$LOGFILE")
fi

if [ -z "$NBS_PAGE" ]; then
    _log "❌ Failed to fetch NBS release page"
    exit 1
fi

_log "✅ Page fetched ($(echo "$NBS_PAGE" | wc -c) bytes)"

# ── Step 2: 定位最新的 70 城条目 ────────────────────────────
# 2026-11-12 实测（P5）：统计局的 /sj/zxfb/ 首页只列 15 条，70 城条目
# 发布后 3~5 天就被新发布挤出首页 → 只 grep 首页会造成「漏采即永久无法自动追补」
# （2026 年 7 月数据漏采、靠人工补录，即此机制）。
# 分页 index_N.html 每页约 1 个月，翻 3 页 ≈ 3 个月追补窗。
# 抓不到条目现在按异常上报（exit 3），不再与「官方未发布」混为一谈（D3）。

fetch_page() {
    # 抓取一页：curl 优先，空则回退 python requests
    local url="$1"
    local html
    html=$(curl -sL --max-time 30 \
        -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
        "$url" 2>> "$LOGFILE")
    if [ -z "$html" ]; then
        html=$(PAGE_URL="$url" $PYTHON -c "
import os
import requests
try:
    r = requests.get(os.environ['PAGE_URL'], timeout=30,
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'})
    r.raise_for_status()
    print(r.text)
except Exception as e:
    print(f'ERROR: {e}', file=__import__('sys').stderr)
    exit(1)
" 2>> "$LOGFILE")
    fi
    printf '%s' "$html"
}

extract_href() {
    # Input: HTML page
    # Output: first href value of a link containing "70个大中城市"
    # Try multiple patterns for different HTML markup styles

    local page="$1"
    local href=""

    # Pattern 1: title='...70个大中城市...'  (current NBS format)
    # First, find lines that contain both href= and 70个大中城市
    # Then extract href="..." from those lines
    href=$(echo "$page" \
        | grep '70个大中城市' \
        | grep -oE 'href="[^"]*"' \
        | head -1 \
        | sed 's/^href="//;s/"$//')

    # Pattern 2: fallback — try newer HTML with single-quoted href
    if [ -z "$href" ]; then
        href=$(echo "$page" \
            | grep '70个大中城市' \
            | grep -oE "href='[^']*'" \
            | head -1 \
            | sed "s/^href='//;s/'$//")
    fi

    # Pattern 3: text content "70个大中城市" in <a> body (no title attribute)
    if [ -z "$href" ]; then
        href=$(echo "$page" \
            | grep -oE '<a [^>]*href="[^"]*"[^>]*>.*70个大中城市' \
            | grep -oE 'href="[^"]*"' \
            | head -1 \
            | sed 's/^href="//;s/"$//')
    fi

    echo "$href"
}

PAGE_CANDIDATES=("$NBS_PAGE_URL" "${NBS_PAGE_URL}index_1.html" "${NBS_PAGE_URL}index_2.html" "${NBS_PAGE_URL}index_3.html")

RELATIVE_URL=""
HIT_PAGE=""
for i in 0 1 2 3; do
    PAGE_URL="${PAGE_CANDIDATES[$i]}"
    if [ "$i" -eq 0 ]; then
        PAGE_HTML="$NBS_PAGE"
        PAGE_LABEL="首页"
    else
        PAGE_HTML=$(fetch_page "$PAGE_URL")
        PAGE_LABEL="回退页 index_$i"
        if [ -z "$PAGE_HTML" ]; then
            _log "⚠️  ${PAGE_LABEL}（$PAGE_URL）抓取失败，跳过"
            continue
        fi
    fi
    RELATIVE_URL=$(extract_href "$PAGE_HTML")
    if [ -n "$RELATIVE_URL" ]; then
        HIT_PAGE="$i"
        _log "🔗 命中${PAGE_LABEL}：$RELATIVE_URL"
        break
    fi
    _log "🔎 ${PAGE_LABEL}无 70 城条目，继续回退"
done

if [ -z "$RELATIVE_URL" ]; then
    _log "❌ 未在首页及 index_1~index_3（近约 3 个月）找到 70 个大中城市条目——按异常上报"
    _log "   可能原因：页面格式变更 / 网络或反爬拦截 / 关键词口径变化"
    _log "   人工核查：$NBS_PAGE_URL"
    exit 3
fi
_log "📄 命中页序号：${HIT_PAGE}（0=首页，越大越久远）"

_log "🔗 Found relative URL: $RELATIVE_URL"

# ── Step 3: Resolve to full URL ────────────────────────────
# Handle various URL formats:
#   ./202605/t20260518_1963715.html  → relative to current page
#   ../../sj/zxfb/202605/...         → relative path
#   /sj/zxfb/202605/...              → absolute path
#   /xxgk/sjfb/zxfb2020/...          → alternate path
#   https://...                      → already absolute

if [[ "$RELATIVE_URL" == http* ]]; then
    FULL_URL="$RELATIVE_URL"
elif [[ "$RELATIVE_URL" == ./* ]]; then
    # ./202605/... → append to NBS page base URL
    FULL_URL="${NBS_PAGE_URL}${RELATIVE_URL#./}"
elif [[ "$RELATIVE_URL" == /* ]]; then
    # /sj/zxfb/... or /xxgk/...
    FULL_URL="https://www.stats.gov.cn${RELATIVE_URL}"
else
    # No leading ./ or / — treat as relative to page
    FULL_URL="${NBS_PAGE_URL}${RELATIVE_URL}"
fi

_log "🌐 Full URL: $FULL_URL"

# ── Step 4: Extract data month from URL ────────────────────
# URL contains date patterns like /202605/ or t20260518
# Data month = publish month - 1  (e.g. 202605 → data is 2026年4月)
MONTH_CODE=$(echo "$RELATIVE_URL" | grep -oE '20[0-9]{4}' | head -1 || echo "")

if [ -z "$MONTH_CODE" ]; then
    _log "⚠️  Could not extract month code from URL, will proceed anyway"
    DATA_MONTH="unknown"
else
    # Convert 202605 → 2026-04 (publish month 05 → data month 04)
    YEAR="${MONTH_CODE:0:4}"
    MONTH_NUM="${MONTH_CODE:4:2}"
    # Data month = publish month - 1, with year rollover
    if [ "$MONTH_NUM" == "01" ]; then
        DATA_MONTH=$((YEAR - 1))"-12"
    else
        DATA_MONTH="$YEAR-$(printf '%02d' $((10#$MONTH_NUM - 1)))"
    fi
fi

_log "📅 Data month: $DATA_MONTH (code: $MONTH_CODE)"

# ── Step 5: Idempotency check ─────────────────────────────
cd "$PROJECT_DIR"

if [ "$DATA_MONTH" != "unknown" ] && [ -f "70cityprice.csv" ]; then
    # Count records for this data month (DATE field is in format YYYY/M/D)
    # e.g. 2026-04 → check for "2026/4/1"
    CHECK_YEAR="${DATA_MONTH%-*}"
    CHECK_MONTH="${DATA_MONTH#*-}"
    # Remove leading zero for month (04 → 4)
    CHECK_MONTH=$((10#$CHECK_MONTH))
    DATE_PATTERN="${CHECK_YEAR}/${CHECK_MONTH}/1"

    EXISTING_COUNT=$(grep -c "\"$DATE_PATTERN\"" 70cityprice.csv 2>/dev/null || echo "0")
    if [ "$EXISTING_COUNT" -ge 100 ]; then
        _log "⏭️  Data for $DATA_MONTH already exists ($EXISTING_COUNT records), skipping"
        _log "✅ Done (idempotent skip)"
        exit 0
    fi
    _log "📊 Existing records for $DATA_MONTH: $EXISTING_COUNT (< 100, will update)"
fi

# ── Step 6: Run update ─────────────────────────────────────
_log "🚀 Running update script..."
cd "$PROJECT_DIR"

$PYTHON tools/update_70cityprice.py "$FULL_URL" >> "$LOGFILE" 2>&1
UPDATE_EXIT=$?

if [ $UPDATE_EXIT -ne 0 ]; then
    _log "❌ Update script failed with exit code $UPDATE_EXIT"
    _log "   Check log: $LOGFILE"
    exit $UPDATE_EXIT
fi

_log "✅ Update script completed"

# ── Step 7: Validate ───────────────────────────────────────
_log "🔍 Running validation..."
$PYTHON tools/validate_70cityprice.py >> "$LOGFILE" 2>&1
VALIDATE_EXIT=$?

if [ $VALIDATE_EXIT -ne 0 ]; then
    _log "❌ Validation failed with exit code $VALIDATE_EXIT"
    _log "   Check log: $LOGFILE"
    exit $VALIDATE_EXIT
fi

_log "✅ Validation passed"

# ── Done ───────────────────────────────────────────────────
_log "=========================================="
_log "✅ Auto-update completed successfully"
_log "   Data month: $DATA_MONTH"
_log "   Source URL: $FULL_URL"
_log "   Log file:   $LOGFILE"
_log "=========================================="
