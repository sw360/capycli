import logging
from datetime import datetime
from typing import Any

import jwt
from sw360 import SW360Keycloak
from requests.auth import AuthBase
from requests.models import PreparedRequest, Response

from capycli import get_logger
from capycli.common.print import print_yellow

LOG = get_logger(__name__)


class KeycloakAuth(AuthBase):
    def __init__(self, url: str, client_id: str, client_secret: str, write_access: bool, initial_token: str) -> None:
        self.kc = SW360Keycloak(url)
        self.client_id = client_id
        self.client_secret = client_secret
        self.write_access = write_access
        self.token = initial_token

    def _refresh_token(self) -> bool:
        try:
            new_token = self.kc.get_keycloak_token(self.client_id, self.client_secret, self.write_access)
            if new_token:
                self.token = new_token
                if LOG.isEnabledFor(logging.DEBUG):
                    LOG.debug("SW360 Keycloak token refreshed successfully.")
                return True
            else:
                print_yellow("  Failed to refresh token: empty token returned")
        except Exception:
            print_yellow("  Failed to refresh token. Check credentials and server status.")
        return False

    def is_token_expiring_soon(self) -> bool:
        try:
            decoded = jwt.decode(  # type: ignore
                self.token, algorithms=["HS256"], options={"verify_signature": False})
            if "exp" in decoded:
                exp = datetime.fromtimestamp(int(decoded["exp"]))
                # refresh if less than 5 minutes remaining
                return (exp - datetime.now()).total_seconds() < 300
        except Exception:
            pass
        return False

    def __call__(self, r: PreparedRequest) -> PreparedRequest:
        # Refresh token shortly before expiry
        if self.token and self.is_token_expiring_soon():
            self._refresh_token()

        if self.token:
            r.headers['Authorization'] = 'Bearer ' + self.token

        r.register_hook('response', self.handle_401)  # type: ignore
        return r

    def handle_401(self, r: Response, **kwargs: Any) -> Response:
        if r.status_code == 401 and not getattr(r.request, '_sw360_retried', False):
            # Only retry safe, idempotent methods to prevent duplicating operations
            if r.request and r.request.method not in ["GET", "HEAD", "OPTIONS"]:
                return r

            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug("Received 401 Unauthorized, attempting token refresh...")

            if self._refresh_token():
                # Consume content of response so we can reuse the connection
                _ = r.content
                r.close()

                # Create a new request based on the old one
                assert r.request is not None

                new_req = r.request.copy()
                new_req.headers['Authorization'] = 'Bearer ' + self.token
                setattr(new_req, '_sw360_retried', True)

                # Send new request and get new response
                if hasattr(r, "connection") and r.connection:
                    new_resp = r.connection.send(new_req, **kwargs)
                    new_resp.history.append(r)
                    new_resp.request = new_req
                    return new_resp

        return r
