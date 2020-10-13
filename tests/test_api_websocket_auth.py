'''
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

'''
from builtins import str

import pytest
from faraday.server.api.modules.websocket_auth import decode_agent_websocket_token


class TestWebsocketAuthEndpoint:

    def test_not_logged_in_request_fail(self, test_client, workspace):
        res = test_client.post('/v2/ws/{}/websocket_token/'.format(
            workspace.name))
        assert res.status_code == 401

    @pytest.mark.usefixtures('logged_user')
    def test_get_method_not_allowed(self, test_client, workspace):
        res = test_client.get('/v2/ws/{}/websocket_token/'.format(
            workspace.name))
        assert res.status_code == 405

    @pytest.mark.usefixtures('logged_user')
    def test_succeeds(self, test_client, workspace):
        res = test_client.post('/v2/ws/{}/websocket_token/'.format(
            workspace.name))
        assert res.status_code == 200

        # A token for that workspace should be generated,
        # This will break if we change the token generation
        # mechanism.
        assert res.json['token'].startswith(str(workspace.id))


class TestAgentWebsocketToken:
    @pytest.mark.usefixtures('session')  # I don't know why this is required
    def test_fails_without_authorization_header(self, test_client):
        res = test_client.post(
            '/v2/agent_websocket_token/',
        )
        assert res.status_code == 401

    @pytest.mark.usefixtures('logged_user')
    def test_fails_with_logged_user(self, test_client):
        res = test_client.post(
            '/v2/agent_websocket_token/',
        )
        assert res.status_code == 401

    @pytest.mark.usefixtures('logged_user')
    def test_fails_with_user_token(self, test_client, session):
        res = test_client.get('/v2/token/')

        assert res.status_code == 200

        headers = [('Authorization', 'Token ' + res.json)]

        # clean cookies make sure test_client has no session
        test_client.cookie_jar.clear()
        res = test_client.post(
            '/v2/agent_websocket_token/',
            headers=headers,
        )
        assert res.status_code == 401

    @pytest.mark.usefixtures('session')
    def test_fails_with_invalid_agent_token(self, test_client):
        headers = [('Authorization', 'Agent 13123')]
        res = test_client.post(
            '/v2/agent_websocket_token/',
            headers=headers,
        )
        assert res.status_code == 403

    @pytest.mark.usefixtures('session')
    def test_succeeds_with_agent_token(self, test_client, agent, session):
        session.add(agent)
        session.commit()
        assert agent.token
        headers = [('Authorization', 'Agent ' + agent.token)]
        res = test_client.post(
            '/v2/agent_websocket_token/',
            headers=headers,
        )
        assert res.status_code == 200
        decoded_agent = decode_agent_websocket_token(res.json['token'])
        assert decoded_agent == agent


# I'm Py3
