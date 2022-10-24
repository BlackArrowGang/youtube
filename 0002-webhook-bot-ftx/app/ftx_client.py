import hmac
import os
import time
import urllib.parse
from typing import Any, Dict, Optional

from requests import Request, Response, Session

# This is the documentation of the API on FTX:
# https://docs.ftx.com/#overview

# Start trading on FTX NOW with our offcial link:
# https://ftx.com/referrals#a=BLACKARROWGANG

class FtxClient:
    _ENDPOINT = "https://ftx.com/api/"

    def __init__(self, subaccount_name=None) -> None:
        self._session = Session()
        self._api_key = os.environ.get("FTX_KEY")
        self._api_secret = os.environ.get("FTX_SECRET")
        self._subaccount_name = subaccount_name

    def _sign_request(self, request: Request) -> None:
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        signature_payload = f"{ts}{prepared.method}{prepared.path_url}".encode()
        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(
            self._api_secret.encode(), signature_payload, "sha256"
        ).hexdigest()
        request.headers["FTX-KEY"] = self._api_key
        request.headers["FTX-SIGN"] = signature
        request.headers["FTX-TS"] = str(ts)
        if self._subaccount_name:
            request.headers["FTX-SUBACCOUNT"] = urllib.parse.quote(
                self._subaccount_name
            )

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("GET", path, params=params)

    def _post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("POST", path, json=params)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        request = Request(method, self._ENDPOINT + path, **kwargs)
        self._sign_request(request)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    def _process_response(self, response: Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if not data["success"]:
                raise Exception(data["error"])
            return data["result"]

    def get_total_usd_balance(self) -> float:
        total_usd = 0.0
        balances = self._get("wallet/balances")
        for balance in balances:
            total_usd += balance["usdValue"]
        return total_usd

    def place_order(
        self,
        market: str,
        side: str,
        price: float,
        size: float,
        type: str = "limit",
        reduce_only: bool = False,
        ioc: bool = False,
        post_only: bool = False,
        client_id: str = None,
        reject_after_ts: float = None,
    ) -> dict:
        return self._post(
            "orders",
            {
                "market": market,
                "side": side,
                "price": price,
                "size": size,
                "type": type,
                "reduceOnly": reduce_only,
                "ioc": ioc,
                "postOnly": post_only,
                "clientId": client_id,
                "rejectAfterTs": reject_after_ts,
            },
        )
