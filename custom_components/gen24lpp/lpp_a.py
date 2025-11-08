"""http request handler."""

import hashlib
import os

import aiohttp

LPP_ON = {
    "exportLimits": {
        "activePower": {
            "hardLimit": {"powerLimit": 0},
            "softLimit": {"enabled": True, "powerLimit": 5000},
            "activated": True,
            "networkMode": "limitLocal",
        },
        "failSafeModeEnabled": True,
        "autodetectedControlledDevices": {},
        "staticControlledDevices": {},
    },
    "visualization": {
        "wattPeakReferenceValue": 11000,
        "exportLimits": {"activePower": {}},
    },
}

LPP_OFF = {
    "exportLimits": {
        "activePower": {
            "hardLimit": {"powerLimit": 0},
            "softLimit": {"enabled": False, "powerLimit": 0},
            "activated": False,
            "networkMode": "limitLocal",
        },
        "failSafeModeEnabled": False,
        "autodetectedControlledDevices": {},
        "staticControlledDevices": {},
    },
    "visualization": {"exportLimits": {"activePower": {}}},
}


class FroniusGEN24:
    """Fronius GEN24 LPP HTTP Request Handler mit Digest-Auth."""

    def __init__(self, host: str, user: str, password: str):
        self.host = host
        self.user = user.lower()
        self.password = password
        self.session = None
        self.realm = None
        self.nonce = None
        self.qop = None
        self.opaque = None
        self.algorithm = "MD5"
        self.nc = 0
        self.lpp_on = LPP_ON
        self.lpp_off = LPP_OFF

        self.http_request_path_praefix = "/api/"
        self.login_path = "/api/commands/Login"
        self.timeofuse_path = "/api/config/timeofuse"
        self.powerlimit_path = "/api/config/limit_settings/powerLimits"

    async def init_session(self):
        """Initialisiert aiohttp ClientSession."""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Schließt die aiohttp-Session."""
        if self.session:
            await self.session.close()

    async def _get_auth_params(self, url: str):
        """Fordert 401 an, um die Digest-Parameter zu bekommen."""
        async with self.session.get(
            url
        ) as r:  # <-- geändert: async context mit aiohttp
            if r.status != 401:
                raise Exception(f"Erwartet 401, aber {r.status}")
            header = r.headers.get("WWW-Authenticate") or r.headers.get(
                "X-WWW-Authenticate"
            )
            if not header:
                raise Exception("Kein WWW-Authenticate-Header gefunden")

            params = {}
            for item in header.replace("Digest ", "").split(","):
                if "=" in item:
                    k, v = item.strip().split("=", 1)
                    params[k] = v.strip('"')

            self.realm = params.get("realm")
            self.nonce = params.get("nonce")
            self.qop = params.get("qop")
            self.opaque = params.get("opaque")
            self.algorithm = params.get("algorithm", "MD5")

    def _hash(self, data: str) -> str:
        if self.algorithm.upper() in ["SHA-256", "SHA256"]:
            return hashlib.sha256(data.encode()).hexdigest()
        else:
            return hashlib.md5(data.encode()).hexdigest()

    def _build_auth_header(self, method: str, uri: str):
        self.nc += 1
        nc_value = f"{self.nc:08x}"
        cnonce = hashlib.md5(os.urandom(8)).hexdigest()

        ha1 = self._hash(f"{self.user}:{self.realm}:{self.password}")
        ha2 = self._hash(f"{method}:{uri}")
        response = self._hash(
            f"{ha1}:{self.nonce}:{nc_value}:{cnonce}:{self.qop}:{ha2}"
        )

        header = (
            f'Digest username="{self.user}", realm="{self.realm}", '
            f'nonce="{self.nonce}", uri="{uri}", '
            f'response="{response}", qop={self.qop}, '
            f'nc={nc_value}, cnonce="{cnonce}"'
        )
        if self.opaque:
            header += f', opaque="{self.opaque}"'
        return header

    async def _request(
        self, method: str, uri: str, headers=None, data=None, params=None
    ):
        """Asynchrone HTTP-Anfrage mit Digest-Auth."""
        url = f"http://{self.host}{uri}"
        if headers is None:
            headers = {}

        # Ersten Auth-Header bauen
        headers["Authorization"] = self._build_auth_header(method, uri)

        async with self.session.request(
            method, url, headers=headers, params=params, data=data
        ) as r:
            if r.status == 401:
                # Wenn 401: Auth-Parameter neu holen
                await self._get_auth_params(url)
                headers["Authorization"] = self._build_auth_header(method, uri)
                async with self.session.request(
                    method, url, headers=headers, params=params, data=data
                ) as r2:
                    r2.raise_for_status()
                    return await r2.text()
            r.raise_for_status()
            return await r.text()

    async def send_request(
        self,
        path,
        method="GET",
        payload=None,
        params=None,
        headers=None,
        add_praefix=False,
    ):
        await self.init_session()

        if headers is None:
            headers = {}
        if add_praefix:
            path = self.http_request_path_praefix + path

        try:
            result = await self._request(
                method, path, headers=headers, data=payload, params=params
            )
            return result
        except Exception as e:
            # Ensure we close the session on error to avoid "Unclosed client session"
            await self.close()

    async def login(self):
        """Asynchroner Login über Digest-Auth."""

        uri = self.login_path
        await self.init_session()
        try:
            await self._request("GET", uri, params={"user": self.user})
            return True

        except Exception as e:
            return False

        finally:
            # Always close the session after attempting login to avoid leaks
            await self.close()
