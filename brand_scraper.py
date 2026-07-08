"""
brand_scraper.py — Instagram competitor data layer for the Brand Analyser.

Sources (via Apify):
  1. Each brand's OWN account posts  -> their deliberate strategy (formats,
     launches, claims, cadence, reels vs static, collabs they run).
  2. Influencer profiles for the collab handles found in those posts -> tier
     (nano/micro/macro/mega) and niche. Capped + deduped + cached to protect
     the Apify free-tier budget.

Everything is normalised into plain dicts and snapshotted per run so week-over-
week "what's new" builds up over time. Falls back to mock data with no key.
"""

from __future__ import annotations

import os
import json
import time
import hashlib
import pathlib
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

APIFY_KEY = os.getenv("APIFY_KEY", "")

CACHE = pathlib.Path("scraper/cache/brand_media")
CACHE.mkdir(parents=True, exist_ok=True)
SNAP = pathlib.Path("scraper/cache/brand_media/snapshots")
SNAP.mkdir(parents=True, exist_ok=True)

# ── Tracked accounts (Deconstruct is the baseline) ────────────────────────────
BRANDS = [
    {"name": "Deconstruct",  "handle": "deconstruct_skincare", "is_baseline": True},
    {"name": "Minimalist",   "handle": "beminimalist__",       "is_baseline": False},
    {"name": "Foxtale",      "handle": "foxtaleskin",          "is_baseline": False},
    {"name": "The Derma Co", "handle": "thedermacoindia",      "is_baseline": False},
    {"name": "Re'equil",     "handle": "reequil",              "is_baseline": False},
    {"name": "Dot & Key",    "handle": "dotandkey.skincare",   "is_baseline": False},
]
HANDLE_TO_BRAND = {str(b["handle"]).lower(): str(b["name"]) for b in BRANDS}

# Brand-specific hashtags creators use when posting ABOUT a brand. ONLY
# unambiguous, skincare-specific tags — generic words like #deconstruct (a
# demolition/architecture term) or #minimalist (design) are deliberately excluded
# to avoid false positives. A skincare-context gate (below) is a further safety net.
BRAND_HASHTAGS = {
    "Deconstruct":  ["deconstructskincare", "deconstructindia"],
    "Minimalist":   ["minimalistskincare", "beminimalist"],
    "Foxtale":      ["foxtaleskincare", "foxtaleskin"],
    "The Derma Co": ["thedermaco", "thedermacoindia"],
    "Re'equil":     ["reequil", "reequilskincare"],
    "Dot & Key":    ["dotandkeyskincare", "dotandkey"],
}

# a post must show skincare context to count (kills off-topic false positives)
_SKINCARE_CONTEXT = (
    "skincare", "skin", "serum", "sunscreen", "spf", "moistur", "cleanser", "toner",
    "acne", "pigment", "niacinamide", "retinol", "hyaluronic", "salicylic", "derma",
    "beauty", "glow", "facewash", "face wash", "vitaminc", "vitamin c", "routine",
    "dermat", "skincareroutine", "skincaretips",
)


def _has_skincare_context(caption, hashtags, matched_tag=""):
    if any(t in (matched_tag or "") for t in ("skincare", "skin", "derma")):
        return True
    blob = (str(caption) + " " + " ".join(str(h) for h in (hashtags or []))).lower()
    return any(term in blob for term in _SKINCARE_CONTEXT)

_COLLAB_MARKERS = ("#ad", "#sponsored", "#collab", "#partner", "paid partnership",
                   "#collaboration", "in collaboration", "#brandpartner")


def _client():
    from apify_client import ApifyClient
    return ApifyClient(APIFY_KEY)


def _media_type(item) -> str:
    """Map an Instagram post to reel / carousel / image (static)."""
    if item.get("productType") == "clips" or item.get("type") == "Video":
        return "reel"
    if item.get("type") == "Sidecar":
        return "carousel"
    return "image"


def normalize_post(item, brand_name) -> dict:
    caption = item.get("caption", "") or ""
    hashtags = item.get("hashtags", []) or []
    mentions = item.get("mentions", []) or []
    tagged = [t.get("username", "") if isinstance(t, dict) else str(t)
              for t in (item.get("taggedUsers", []) or [])]
    coauthors = [c.get("username", "") if isinstance(c, dict) else str(c)
                 for c in (item.get("coauthorProducers", []) or [])]

    cap_low = caption.lower()
    is_collab = bool(item.get("isSponsored") or coauthors
                     or any(m in cap_low for m in _COLLAB_MARKERS))

    music = ""
    mi = item.get("musicInfo") or {}
    if isinstance(mi, dict):
        music = mi.get("song_name", "") or mi.get("artist_name", "")

    return {
        "brand": brand_name,
        "url": item.get("url", ""),
        "type": _media_type(item),
        "caption": caption,
        "hashtags": hashtags,
        "mentions": mentions,
        "tagged": [u for u in (tagged + coauthors) if u],
        "likes": item.get("likesCount", 0) or 0,
        "comments": item.get("commentsCount", 0) or 0,
        "views": item.get("videoViewCount", item.get("videoPlayCount", 0)) or 0,
        "timestamp": item.get("timestamp", ""),
        "is_collab": is_collab,
        "music": music,
        "thumbnail": item.get("displayUrl", ""),
        "owner": item.get("ownerUsername", ""),
    }


def fetch_account_posts(days_back=25, max_posts=40, handles=None, progress_cb=None):
    """
    Fetch recent posts for each tracked account in ONE Apify run.
    Returns {brand_name: [normalized_post, ...]}. Uses cache (<6h) to avoid re-spend.
    """
    handles = handles or [b["handle"] for b in BRANDS]
    cache_key = hashlib.md5(f"posts_{'_'.join(handles)}_{days_back}_{max_posts}".encode()).hexdigest()
    cache_file = CACHE / f"{cache_key}.json"
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) / 3600 < 6:
        print("[brand] using cached account posts")
        return json.loads(cache_file.read_text(encoding="utf-8"))

    if not APIFY_KEY:
        print("[brand] no APIFY_KEY — using mock posts")
        return _mock_posts()

    try:
        client = _client()
        if progress_cb:
            progress_cb(0, 1, f"Scraping {len(handles)} accounts via Apify…")

        def _run(urls):
            run = client.actor("apify/instagram-scraper").call(run_input={
                "directUrls": [f"https://www.instagram.com/{h}/" for h in urls],
                "resultsType": "posts", "resultsLimit": max_posts,
                "onlyPostsNewerThan": f"{days_back} days", "addParentData": False,
            })
            assert run is not None
            return list(client.dataset(run.default_dataset_id).iterate_items())

        by_brand: dict[str, list] = {str(b["name"]): [] for b in BRANDS}

        def _ingest(items):
            for it in items:
                brand = HANDLE_TO_BRAND.get(str(it.get("ownerUsername", "")).lower())
                if brand:
                    by_brand[brand].append(normalize_post(it, brand))

        _ingest(_run(handles))
        # Instagram throttles individual profiles intermittently — retry the
        # accounts that came back empty (once) so one flaky profile isn't lost.
        empty = [str(b["handle"]) for b in BRANDS
                 if str(b["handle"]) in handles and not by_brand.get(str(b["name"]))]
        if empty:
            print(f"[brand] retrying empty accounts: {empty}")
            time.sleep(3)
            _ingest(_run(empty))

        still_empty = [k for k, v in by_brand.items() if not v]
        cache_file.write_text(json.dumps(by_brand, indent=2, ensure_ascii=False), encoding="utf-8")
        print("[brand] fetched posts: " + ", ".join(f"{k}={len(v)}" for k, v in by_brand.items()))
        if still_empty:
            print(f"[brand] no data this run for: {still_empty} (Instagram throttling — retry later)")
        return by_brand
    except Exception as e:
        print(f"[brand] Apify error: {e}")
        return _mock_posts()


def fetch_influencer_profiles(usernames, cap=60):
    """
    Fetch follower count + category for influencer handles (deduped, capped, cached).
    Returns {username: {"followers": int, "tier": str, "category": str, "full_name": str}}.
    """
    usernames = list(dict.fromkeys(u.lstrip("@") for u in usernames if u))[:cap]
    if not usernames:
        return {}

    out = {}
    remaining = []
    for u in usernames:  # per-influencer cache (survives across brands/runs)
        f = CACHE / f"infl_{hashlib.md5(u.lower().encode()).hexdigest()}.json"
        if f.exists() and (time.time() - f.stat().st_mtime) / 3600 < 168:  # 7 days
            out[u] = json.loads(f.read_text(encoding="utf-8"))
        else:
            remaining.append(u)

    if remaining and APIFY_KEY:
        try:
            client = _client()
            run = client.actor("apify/instagram-profile-scraper").call(
                run_input={"usernames": remaining})
            assert run is not None
            for it in client.dataset(run.default_dataset_id).iterate_items():
                u = it.get("username", "")
                if not u:
                    continue
                followers = it.get("followersCount", 0) or 0
                rec = {"followers": followers, "tier": tier_of(followers),
                       "category": it.get("businessCategoryName", it.get("category", "")) or "",
                       "full_name": it.get("fullName", "")}
                out[u] = rec
                (CACHE / f"infl_{hashlib.md5(u.lower().encode()).hexdigest()}.json").write_text(
                    json.dumps(rec, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"[brand] influencer profile fetch error: {e}")
    return out


def tier_of(followers) -> str:
    f = followers or 0
    if f >= 1_000_000:
        return "mega"
    if f >= 100_000:
        return "macro"
    if f >= 10_000:
        return "micro"
    return "nano"


def collab_influencers(by_brand):
    """
    Discover the creators each brand features — the core of the tool.

    Brands partner with influencers by tagging/mentioning them, and often WITHOUT
    an #ad label, so we look at tagged + mentioned accounts across ALL posts
    (not just flagged collabs), exclude the tracked brands themselves, and rank by
    frequency with a weight boost for explicit-collab posts.
    Returns {brand: [handle, ...]} best-first. Downstream profiling reveals which
    are genuine creators vs other brands/locations.
    """
    brand_handles = {str(b["handle"]).lower() for b in BRANDS}
    # marketplaces / retailers / generic accounts that aren't influencers
    _NON_INFLUENCER = ("amazon", "flipkart", "myntra", "nykaa", "purplle", "tira",
                       "meesho", "ajio", "official", "store", "shop", "beauty.in")

    def _skip(u):
        return u in brand_handles or any(tok in u for tok in _NON_INFLUENCER)

    out = {}
    for brand, posts in by_brand.items():
        freq = {}
        for p in posts:
            weight = 2 if p.get("is_collab") else 1
            partners = list(p.get("tagged", [])) + list(p.get("mentions", []))
            for u in partners:
                uu = str(u).lstrip("@").lower()
                if uu and not _skip(uu):
                    freq[uu] = freq.get(uu, 0) + weight
        out[brand] = [h for h, _ in sorted(freq.items(), key=lambda kv: -kv[1])]
    return out


def fetch_hashtag_creators(days_back=25, per_hashtag=40, top_n=20, progress_cb=None):
    """
    Discover the BIGGEST creator bracket: people who post about a brand using its
    keywords/hashtags in the caption (without tagging it).

    For each brand we keep only the TOP `top_n` HIGHEST-PERFORMING posts (by
    engagement) from the last `days_back` days whose caption/hashtags actually
    carry the brand keyword, then return their authors ranked by that performance.
    {brand: [(handle, engagement), ...]} best-first.
    """
    hashtags = sorted({h for hs in BRAND_HASHTAGS.values() for h in hs})
    tag_to_brands = {}
    for brand, hs in BRAND_HASHTAGS.items():
        for h in hs:
            tag_to_brands.setdefault(h.lower(), []).append(brand)

    brand_handles = {str(b["handle"]).lower() for b in BRANDS}
    _NON_INFLUENCER = ("amazon", "flipkart", "myntra", "nykaa", "purplle", "tira",
                       "meesho", "ajio", "official", "store", "shop")

    cache_key = hashlib.md5(f"htcre_{'_'.join(hashtags)}_{days_back}_{per_hashtag}_{top_n}".encode()).hexdigest()
    cache_file = CACHE / f"htcreators_{cache_key}.json"
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) / 3600 < 6:
        print("[brand] using cached hashtag creators")
        return json.loads(cache_file.read_text(encoding="utf-8"))

    if not APIFY_KEY:
        return {b: [] for b in BRAND_HASHTAGS}

    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    brand_posts = {b: [] for b in BRAND_HASHTAGS}  # {brand: [(engagement, author)]}
    try:
        client = _client()
        if progress_cb:
            progress_cb(0, 1, f"Finding top creators via {len(hashtags)} brand keywords…")
        run = client.actor("apify/instagram-hashtag-scraper").call(run_input={
            "hashtags": hashtags, "resultsLimit": per_hashtag,
        })
        assert run is not None
        for it in client.dataset(run.default_dataset_id).iterate_items():
            owner = str(it.get("ownerUsername", "")).lower()
            if not owner or owner in brand_handles or any(t in owner for t in _NON_INFLUENCER):
                continue
            ts = it.get("timestamp", "")
            if ts:
                try:
                    if datetime.fromisoformat(ts.replace("Z", "+00:00")) < cutoff:
                        continue
                except Exception:
                    pass
            caption = it.get("caption", "")
            post_hashtags = [str(t).lower() for t in (it.get("hashtags", []) or [])]
            post_tags = set(post_hashtags)
            # views is the ranking signal (methodology: highest-viewed videos)
            views = it.get("videoViewCount", it.get("videoPlayCount", 0)) or 0
            for tag in post_tags:
                for brand in tag_to_brands.get(tag, []):
                    if not _has_skincare_context(caption, post_hashtags, tag):
                        continue  # disambiguate: must be a skincare post
                    brand_posts[brand].append((views, owner))

        out = {}
        for brand, posts in brand_posts.items():
            posts.sort(key=lambda x: -x[0])             # highest VIEWS first
            best = {}                                   # dedup author -> best views
            for views, owner in posts[:max(top_n * 3, 60)]:
                best[owner] = max(best.get(owner, 0), views)
            out[brand] = sorted(best.items(), key=lambda kv: -kv[1])[:top_n]
        cache_file.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
        print("[brand] top hashtag creators (by views): " +
              ", ".join(f"{b}={len(v)}" for b, v in out.items()))
        return out
    except Exception as e:
        print(f"[brand] hashtag creator fetch error: {e}")
        return {b: [] for b in BRAND_HASHTAGS}


def fetch_influencer_posts(usernames, n=6, cap=40, days_back=90):
    """
    Fetch each influencer's own recent posts so we can characterise WHAT they post
    (content style, sector). Deduped, capped, and cached 7 days to protect credits.
    Returns {username: [normalized_post, ...]}.
    """
    usernames = list(dict.fromkeys(u.lstrip("@") for u in usernames if u))[:cap]
    if not usernames:
        return {}

    out, remaining = {}, []
    for u in usernames:
        f = CACHE / f"inflposts_{hashlib.md5(u.lower().encode()).hexdigest()}.json"
        if f.exists() and (time.time() - f.stat().st_mtime) / 3600 < 168:
            out[u] = json.loads(f.read_text(encoding="utf-8"))
        else:
            remaining.append(u)

    if remaining and APIFY_KEY:
        try:
            client = _client()
            run = client.actor("apify/instagram-scraper").call(run_input={
                "directUrls": [f"https://www.instagram.com/{u}/" for u in remaining],
                "resultsType": "posts", "resultsLimit": n,
                "onlyPostsNewerThan": f"{days_back} days", "addParentData": False,
            })
            assert run is not None
            grouped: dict[str, list] = {u: [] for u in remaining}
            for it in client.dataset(run.default_dataset_id).iterate_items():
                owner = str(it.get("ownerUsername", ""))
                if owner in grouped:
                    grouped[owner].append(normalize_post(it, owner))
            for u, posts in grouped.items():
                out[u] = posts
                (CACHE / f"inflposts_{hashlib.md5(u.lower().encode()).hexdigest()}.json").write_text(
                    json.dumps(posts, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"[brand] influencer posts fetch error: {e}")
    return out


def validate_handles(handles=None):
    """Cheap check: pull 1 post per account, report which handles returned data."""
    handles = handles or [b["handle"] for b in BRANDS]
    if not APIFY_KEY:
        return {h: "no APIFY_KEY" for h in handles}
    try:
        client = _client()
        run = client.actor("apify/instagram-scraper").call(run_input={
            "directUrls": [f"https://www.instagram.com/{h}/" for h in handles],
            "resultsType": "posts", "resultsLimit": 1, "addParentData": False,
        })
        assert run is not None
        got = set()
        for it in client.dataset(run.default_dataset_id).iterate_items():
            got.add(str(it.get("ownerUsername", "")).lower())
        return {h: ("OK" if h.lower() in got else "NO DATA — check handle") for h in handles}
    except Exception as e:
        return {h: f"error: {e}" for h in handles}


# ── snapshots (free week-over-week history) ───────────────────────────────────
def save_snapshot(payload):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    (SNAP / f"run_{stamp}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_snapshots():
    runs = []
    for f in sorted(SNAP.glob("run_*.json"), reverse=True):
        try:
            runs.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return runs


# ── mock fallback (offline/dev) ───────────────────────────────────────────────
def _mock_posts():
    demo = {}
    for b in BRANDS:
        demo[b["name"]] = [{
            "brand": b["name"], "url": f"https://instagram.com/p/mock_{i}",
            "type": ["reel", "carousel", "image"][i % 3],
            "caption": f"{b['name']} sample post about niacinamide #skincare #ad",
            "hashtags": ["skincare", "niacinamide"], "mentions": ["@some_influencer"],
            "tagged": ["some_influencer"], "likes": 500 + i * 40, "comments": 20 + i,
            "views": 8000 if i % 3 == 0 else 0, "timestamp": "2026-06-20T10:00:00Z",
            "is_collab": i % 3 == 0, "music": "", "thumbnail": "", "owner": b["handle"],
        } for i in range(6)]
    return demo
