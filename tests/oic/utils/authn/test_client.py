# pylint: disable=missing-docstring,no-self-use

import base64

import pytest

from oic.oauth2 import Client
from oic.oauth2.grant import Grant
from oic.oauth2.message import AccessTokenRequest, ResourceRequest, \
    AuthorizationResponse, AccessTokenResponse
from oic.utils.authn.client import ClientSecretBasic, BearerHeader, BearerBody, \
    ClientSecretPost
from utils_for_tests import _eq  # pylint: disable=import-error


@pytest.fixture
def client():
    cli = Client("A")
    cli.client_secret = "boarding pass"
    return cli


class TestClientSecretBasic(object):
    def test_construct(self, client):
        cis = AccessTokenRequest(code="foo", redirect_uri="http://example.com")

        csb = ClientSecretBasic(client)
        http_args = csb.construct(cis)

        assert http_args == {"headers": {'Authorization': 'Basic {}'.format(
            base64.b64encode('A:boarding pass'))}}


class TestBearerHeader(object):
    def test_construct(self, client):
        request_args = {"access_token": "Sesame"}
        bh = BearerHeader(client)
        http_args = bh.construct(request_args=request_args)

        assert http_args == {"headers": {"Authorization": "Bearer Sesame"}}

    def test_construct_with_http_args(self, client):
        request_args = {"access_token": "Sesame"}
        bh = BearerHeader(client)
        http_args = bh.construct(request_args=request_args,
                                 http_args={"foo": "bar"})

        assert _eq(http_args.keys(), ["foo", "headers"])
        assert http_args["headers"] == {"Authorization": "Bearer Sesame"}

    def test_construct_with_headers(self, client):
        request_args = {"access_token": "Sesame"}

        bh = BearerHeader(client)
        http_args = bh.construct(request_args=request_args,
                                 http_args={"headers": {"x-foo": "bar"}})

        assert _eq(http_args.keys(), ["headers"])
        assert _eq(http_args["headers"].keys(), ["Authorization", "x-foo"])
        assert http_args["headers"]["Authorization"] == "Bearer Sesame"

    def test_construct_with_resource_request(self, client):
        bh = BearerHeader(client)
        cis = ResourceRequest(access_token="Sesame")

        http_args = bh.construct(cis)

        assert "access_token" not in cis
        assert http_args == {"headers": {"Authorization": "Bearer Sesame"}}

    def test_construct_with_token(self, client):
        resp1 = AuthorizationResponse(code="auth_grant", state="state")
        client.parse_response(AuthorizationResponse, resp1.to_urlencoded(),
                              "urlencoded")
        resp2 = AccessTokenResponse(access_token="token1",
                                    token_type="Bearer", expires_in=0,
                                    state="state")
        client.parse_response(AccessTokenResponse, resp2.to_urlencoded(),
                              "urlencoded")

        http_args = BearerHeader(client).construct(ResourceRequest(),
                                                   state="state")
        assert http_args == {"headers": {"Authorization": "Bearer token1"}}


class TestBearerBody(object):
    def test_construct_with_request_args(self, client):
        request_args = {"access_token": "Sesame"}
        cis = ResourceRequest()
        http_args = BearerBody(client).construct(cis, request_args)

        assert cis["access_token"] == "Sesame"
        assert http_args is None

    def test_construct_with_state(self, client):
        resp = AuthorizationResponse(code="code", state="state")
        grant = Grant()
        grant.add_code(resp)
        atr = AccessTokenResponse(access_token="2YotnFZFEjr1zCsicMWpAA",
                                  token_type="example",
                                  refresh_token="tGzv3JOkF0XG5Qx2TlKWIA",
                                  example_parameter="example_value",
                                  scope=["inner", "outer"])
        grant.add_token(atr)
        client.grant["state"] = grant

        cis = ResourceRequest()
        http_args = BearerBody(client).construct(cis, {}, state="state",
                                                 scope="inner")
        assert cis["access_token"] == "2YotnFZFEjr1zCsicMWpAA"
        assert http_args is None

    def test_construct_with_request(self, client):
        resp1 = AuthorizationResponse(code="auth_grant", state="state")
        client.parse_response(AuthorizationResponse, resp1.to_urlencoded(),
                              "urlencoded")
        resp2 = AccessTokenResponse(access_token="token1",
                                    token_type="Bearer", expires_in=0,
                                    state="state")
        client.parse_response(AccessTokenResponse, resp2.to_urlencoded(),
                              "urlencoded")

        cis = ResourceRequest()
        BearerBody(client).construct(cis, state="state")

        assert "access_token" in cis
        assert cis["access_token"] == "token1"


class TestClientSecretPost(object):
    def test_construct(self, client):
        cis = AccessTokenRequest(code="foo", redirect_uri="http://example.com")
        csp = ClientSecretPost(client)
        http_args = csp.construct(cis)

        assert cis["client_id"] == "A"
        assert cis["client_secret"] == "boarding pass"
        assert http_args is None

        cis = AccessTokenRequest(code="foo", redirect_uri="http://example.com")
        http_args = csp.construct(cis, {},
                                  http_args={"client_secret": "another"})
        assert cis["client_id"] == "A"
        assert cis["client_secret"] == "another"
        assert http_args == {}
