from unittest.mock import MagicMock, patch

from requests.models import PreparedRequest, Response

from capycli.common.keycloak_auth import KeycloakAuth


class TestKeycloakAuth:
    def test_refresh_token(self) -> None:
        with patch('capycli.common.keycloak_auth.SW360Keycloak') as mock_kc:
            instance = mock_kc.return_value
            instance.get_keycloak_token.return_value = "new_token"

            auth = KeycloakAuth("http://localhost", "client", "secret", False, "old_token")
            assert auth._refresh_token() is True
            assert auth.token == "new_token"

    def test_call_adds_header(self) -> None:
        with patch('capycli.common.keycloak_auth.SW360Keycloak') as _:
            auth = KeycloakAuth("http://localhost", "client", "secret", False, "old_token")
            # Instead of assigning to a method, patch it:
            with patch.object(auth, 'is_token_expiring_soon', return_value=False):
                req = PreparedRequest()
                setattr(req, 'headers', {})
                setattr(req, 'register_hook', MagicMock())

                req2 = auth(req)
                assert getattr(req2, 'headers')['Authorization'] == 'Bearer old_token'

    def test_handle_401_get(self) -> None:
        with patch('capycli.common.keycloak_auth.SW360Keycloak') as mock_kc:
            instance = mock_kc.return_value
            instance.get_keycloak_token.return_value = "new_token"

            auth = KeycloakAuth("http://localhost", "client", "secret", False, "old_token")

            r = Response()
            r.status_code = 401
            r.request = PreparedRequest()
            r.request.method = "GET"
            r.request.url = "http://localhost"
            setattr(r.request, 'headers', {})
            setattr(r, 'connection', MagicMock())

            mock_new_resp = Response()
            mock_new_resp.status_code = 200
            getattr(r, 'connection').send.return_value = mock_new_resp

            new_r = auth.handle_401(r)

            assert getattr(r, 'connection').send.called
            assert new_r == mock_new_resp

    def test_handle_401_no_retry_for_post(self) -> None:
        with patch('capycli.common.keycloak_auth.SW360Keycloak') as mock_kc:
            instance = mock_kc.return_value
            instance.get_keycloak_token.return_value = "new_token"

            auth = KeycloakAuth("http://localhost", "client", "secret", False, "old_token")

            r = Response()
            r.status_code = 401
            r.request = PreparedRequest()
            r.request.method = "POST"
            r.request.url = "http://localhost"
            setattr(r.request, 'headers', {})
            setattr(r, 'connection', MagicMock())

            new_r = auth.handle_401(r)

            assert not getattr(r, 'connection').send.called
            assert new_r == r

    def test_handle_401_no_second_retry(self) -> None:
        with patch('capycli.common.keycloak_auth.SW360Keycloak') as mock_kc:
            instance = mock_kc.return_value
            instance.get_keycloak_token.return_value = "new_token"

            auth = KeycloakAuth("http://localhost", "client", "secret", False, "old_token")

            r = Response()
            r.status_code = 401
            r.request = PreparedRequest()
            r.request.method = "GET"
            r.request.url = "http://localhost"
            setattr(r.request, 'headers', {})
            # This simulates a request that was already retried
            setattr(r.request, '_sw360_retried', True)
            setattr(r, 'connection', MagicMock())

            new_r = auth.handle_401(r)

            assert not getattr(r, 'connection').send.called
            assert new_r == r
