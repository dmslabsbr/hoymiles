import re
import requests
import pytest

from hoymiles.cloud_api import CloudApi


class TestCloudApi:
    cloud_api: CloudApi

    def setup_class(self):
        self.cloud_api = CloudApi(config={})

    def test_send_post_request(self, mocker):
        expected_retv = {"status": "ok"}
        mocker_snd_request = mocker.patch(
            "hoymiles.cloud_api.CloudApi._send_request", return_value=expected_retv
        )
        url = "https://test.com"
        header = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 1234567890",
        }
        payload = {
            "username": "test",
            "password": "test",
        }
        response = self.cloud_api.send_post_request(url, header, payload)
        mocker_snd_request.called_once_with(url, header, payload, "POST")
        assert response == expected_retv, "Response is not as expected"

    def test_send_options_request(self, mocker):
        expected_retv = {"status": "ok"}
        mocker_snd_request = mocker.patch(
            "hoymiles.cloud_api.CloudApi._send_request", return_value=expected_retv
        )
        url = "https://test.com"
        header = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 1234567890",
        }
        payload = {
            "username": "test",
            "password": "test",
        }
        response = self.cloud_api.send_options_request(url, header, payload)
        mocker_snd_request.called_once_with(url, header, payload, "OPTIONS")
        assert response == expected_retv, "Response is not as expected"

    def test_send_request(self, mocker):
        expected_retv = requests.Response()
        url = "https://test.com"
        header = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 1234567890",
        }
        mocker_req = mocker.patch("requests.Request")
        mocker_send = mocker.patch("requests.Session.send", return_value=expected_retv)

        response = self.cloud_api._send_request(url, header, {}, "POST")
        mocker_req.prepare.called_once()
        mocker_req.prepare.return_value = "prepared"
        mocker_send.send.called_once_with("prepared")
        assert response == expected_retv, "Response is not as expected"

    def test_send_request_exception(self, mocker):
        expected_retv = requests.Response()
        url = "https://test.com"
        header = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 1234567890",
        }
        mocker_req = mocker.patch("requests.Request")
        mocker_send = mocker.patch("requests.Session.send", side_effect=Exception())

        response = self.cloud_api._send_request(url, header, {}, "POST")
        mocker_req.prepare.called_once()
        mocker_req.prepare.return_value = "prepared"
        mocker_send.send.called_once_with("prepared")

        assert response == None, "Response is not as expected"

    def test_get_token(self, mocker):
        expected_retv = requests.Response()
        expected_retv.status_code = 200
        expected_retv._content = (
            b'{ "status" : "0",  "data": { "token": "1234567890" } }'
        )
        mocker_snd_request = mocker.patch(
            "hoymiles.cloud_api.CloudApi.send_post_request", return_value=expected_retv
        )

        mocker.patch(
            "hoymiles.cloud_api.CloudApi.get_credentials",
            return_value=("user", "pass_hex"),
        )
        assert self.cloud_api.get_token()
        mocker_snd_request.called_once()

    def test_get_token_missing_token(self, mocker):
        expected_retv = requests.Response()
        expected_retv.status_code = 200
        expected_retv._content = b'{ "status" : "0",  "data": { } }'
        mocker_snd_request = mocker.patch(
            "hoymiles.cloud_api.CloudApi.send_post_request", return_value=expected_retv
        )

        mocker.patch(
            "hoymiles.cloud_api.CloudApi.get_credentials",
            return_value=("user", "pass_hex"),
        )
        assert not self.cloud_api.get_token()
        mocker_snd_request.called_once()

    def test_get_token_error_form_cloud(self, mocker):
        """Request status code is 200 but status in response is not 0"""
        expected_retv = requests.Response()
        expected_retv.status_code = 200
        expected_retv._content = b'{ "status" : "1",  "data": { } }'
        mocker_snd_request = mocker.patch(
            "hoymiles.cloud_api.CloudApi.send_post_request", return_value=expected_retv
        )

        mocker.patch(
            "hoymiles.cloud_api.CloudApi.get_credentials",
            return_value=("user", "pass_hex"),
        )
        assert not self.cloud_api.get_token()
        mocker_snd_request.called_once()
