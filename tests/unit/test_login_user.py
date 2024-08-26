import json
import os
import pytest
from unittest.mock import patch, MagicMock
from login_user.app import lambda_handler
from botocore.exceptions import ClientError

# Mocks de boto3 y configuración de variables de entorno
@patch.dict(os.environ, {"REGION_NAME": "us-west-2", "CLIENT_ID": "your_client_id", "USER_POOL_ID": "your_user_pool_id"})
@patch('boto3.client')
def test_lambda_handler_successful_login(mock_boto_client):
    mock_client = MagicMock()
    mock_boto_client.return_value = mock_client

    # Mock de la respuesta de initiate_auth
    mock_client.initiate_auth.return_value = {
        'AuthenticationResult': {
            'IdToken': 'mock_id_token',
            'AccessToken': 'mock_access_token',
            'RefreshToken': 'mock_refresh_token'
        }
    }

    # Mock de la respuesta de admin_get_user
    mock_client.admin_get_user.return_value = {
        'UserAttributes': [
            {'Name': 'custom:role', 'Value': 'user'},
            {'Name': 'sub', 'Value': 'mock_cognito_user_id'}
        ]
    }

    event = {
        "body": json.dumps({
            "username": "testuser",
            "password": "testpassword"
        })
    }

    response = lambda_handler(event, {})

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['id_token'] == 'mock_id_token'
    assert body['access_token'] == 'mock_access_token'
    assert body['refresh_token'] == 'mock_refresh_token'
    assert body['role'] == 'user'
    assert body['user_id'] == 'mock_cognito_user_id'

@patch.dict(os.environ, {"REGION_NAME": "us-west-2", "CLIENT_ID": "your_client_id", "USER_POOL_ID": "your_user_pool_id"})
@patch('boto3.client')
def test_lambda_handler_new_password_required(mock_boto_client):
    mock_client = MagicMock()
    mock_boto_client.return_value = mock_client

    # Mock de la respuesta de initiate_auth con NEW_PASSWORD_REQUIRED
    mock_client.initiate_auth.return_value = {
        'ChallengeName': 'NEW_PASSWORD_REQUIRED',
        'Session': 'mock_session'
    }

    # Mock de la respuesta de respond_to_auth_challenge
    mock_client.respond_to_auth_challenge.return_value = {
        'AuthenticationResult': {
            'IdToken': 'mock_id_token',
            'AccessToken': 'mock_access_token',
            'RefreshToken': 'mock_refresh_token'
        }
    }

    # Mock de la respuesta de admin_get_user
    mock_client.admin_get_user.return_value = {
        'UserAttributes': [
            {'Name': 'custom:role', 'Value': 'user'},
            {'Name': 'sub', 'Value': 'mock_cognito_user_id'}
        ]
    }

    event = {
        "body": json.dumps({
            "username": "testuser",
            "password": "testpassword",
            "newPassword": "newpassword"
        })
    }

    response = lambda_handler(event, {})

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['id_token'] == 'mock_id_token'
    assert body['access_token'] == 'mock_access_token'
    assert body['refresh_token'] == 'mock_refresh_token'
    assert body['role'] == 'user'
    assert body['user_id'] == 'mock_cognito_user_id'

@patch.dict(os.environ, {"REGION_NAME": "us-west-2", "CLIENT_ID": "your_client_id", "USER_POOL_ID": "your_user_pool_id"})
@patch('boto3.client')
def test_lambda_handler_missing_username_or_password(mock_boto_client):
    event = {
        "body": json.dumps({
            "password": "testpassword"
        })
    }

    response = lambda_handler(event, {})

    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert "Username and password are required" in body['error_message']

@patch.dict(os.environ, {"REGION_NAME": "us-west-2", "CLIENT_ID": "your_client_id", "USER_POOL_ID": "your_user_pool_id"})
@patch('boto3.client')
def test_lambda_handler_missing_new_password(mock_boto_client):
    mock_client = MagicMock()
    mock_boto_client.return_value = mock_client

    # Mock de la respuesta de initiate_auth con NEW_PASSWORD_REQUIRED
    mock_client.initiate_auth.return_value = {
        'ChallengeName': 'NEW_PASSWORD_REQUIRED',
        'Session': 'mock_session'
    }

    event = {
        "body": json.dumps({
            "username": "testuser",
            "password": "testpassword"
        })
    }

    response = lambda_handler(event, {})

    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert "New password is required to complete the challenge" in body['error_message']

@patch.dict(os.environ, {"REGION_NAME": "us-west-2", "CLIENT_ID": "your_client_id", "USER_POOL_ID": "your_user_pool_id"})
@patch('boto3.client')
def test_lambda_handler_cognito_exception(mock_boto_client):
    mock_client = MagicMock()
    mock_boto_client.return_value = mock_client

    # Mock de una excepción de Cognito
    mock_client.initiate_auth.side_effect = ClientError(
        {"Error": {"Message": "User does not exist"}},
        "InitiateAuth"
    )

    event = {
        "body": json.dumps({
            "username": "testuser",
            "password": "testpassword"
        })
    }

    response = lambda_handler(event, {})

    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert "User does not exist" in body['error_message']

@patch.dict(os.environ, {"REGION_NAME": "us-west-2", "CLIENT_ID": "your_client_id", "USER_POOL_ID": "your_user_pool_id"})
@patch('boto3.client')
def test_lambda_handler_unexpected_exception(mock_boto_client):
    mock_client = MagicMock()
    mock_boto_client.return_value = mock_client

    # Mock de una excepción inesperada
    mock_client.initiate_auth.side_effect = Exception("Unexpected error")

    event = {
        "body": json.dumps({
            "username": "testuser",
            "password": "testpassword"
        })
    }

    response = lambda_handler(event, {})

    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert "Unexpected error" in body['error_message']
