import json
import os
import pytest
from unittest.mock import patch, MagicMock
from create_user.app import lambda_handler, generate_temporary_password, insert_db
from botocore.exceptions import ClientError

@patch.dict(os.environ, {
    "REGION_NAME": "us-west-2",
    "USER_POOL_ID": "us-west-2_example",
    "RDS_ENDPOINT": "example.rds.amazonaws.com",
    "RDS_USERNAME": "admin",
    "RDS_PASSWORD": "password",
    "RDS_DB_NAME": "example_db"
})
@patch('create_user.app.boto3.client')
@patch('create_user.app.insert_db')
def test_lambda_handler_success(mock_insert_db, mock_boto_client):
    mock_client = MagicMock()
    mock_boto_client.return_value = mock_client

    # Mock de la respuesta de admin_create_user
    mock_client.admin_create_user.return_value = {
        'User': {
            'Username': 'mock_cognito_username'
        }
    }

    # Mock de la respuesta de admin_get_user para el caso en el que el usuario no existe
    mock_client.admin_get_user.side_effect = mock_client.exceptions.UserNotFoundException({}, "admin_get_user")

    event = {
        "body": json.dumps({
            "email": "testuser@example.com"
        })
    }

    response = lambda_handler(event, {})

    assert response['statusCode'] == 200
    assert "User created successfully" in response['body']
    mock_insert_db.assert_called_once_with('mock_cognito_username', 'testuser@example.com', mock.ANY, 'usuario')

@patch.dict(os.environ, {
    "REGION_NAME": "us-west-2",
    "USER_POOL_ID": "us-west-2_example",
    "RDS_ENDPOINT": "example.rds.amazonaws.com",
    "RDS_USERNAME": "admin",
    "RDS_PASSWORD": "password",
    "RDS_DB_NAME": "example_db"
})
@patch('create_user.app.boto3.client')
def test_lambda_handler_user_already_exists(mock_boto_client):
    mock_client = MagicMock()
    mock_boto_client.return_value = mock_client

    # Mock de la respuesta de admin_get_user para el caso en el que el usuario ya existe
    mock_client.admin_get_user.return_value = {
        'Username': 'testuser@example.com'
    }

    event = {
        "body": json.dumps({
            "email": "testuser@example.com"
        })
    }

    response = lambda_handler(event, {})

    assert response['statusCode'] == 400
    assert "User account already exists" in response['body']

@patch.dict(os.environ, {
    "REGION_NAME": "us-west-2",
    "USER_POOL_ID": "us-west-2_example",
    "RDS_ENDPOINT": "example.rds.amazonaws.com",
    "RDS_USERNAME": "admin",
    "RDS_PASSWORD": "password",
    "RDS_DB_NAME": "example_db"
})
@patch('create_user.app.boto3.client')
def test_lambda_handler_missing_email(mock_boto_client):
    event = {
        "body": json.dumps({})
    }

    response = lambda_handler(event, {})

    assert response['statusCode'] == 400
    assert "Missing input parameters" in response['body']

@patch.dict(os.environ, {
    "REGION_NAME": "us-west-2",
    "USER_POOL_ID": "us-west-2_example",
    "RDS_ENDPOINT": "example.rds.amazonaws.com",
    "RDS_USERNAME": "admin",
    "RDS_PASSWORD": "password",
    "RDS_DB_NAME": "example_db"
})
@patch('create_user.app.boto3.client')
def test_lambda_handler_cognito_exception(mock_boto_client):
    mock_client = MagicMock()
    mock_boto_client.return_value = mock_client

    # Mock de una excepción de Cognito
    mock_client.admin_create_user.side_effect = ClientError(
        {"Error": {"Message": "Something went wrong"}},
        "admin_create_user"
    )

    event = {
        "body": json.dumps({
            "email": "testuser@example.com"
        })
    }

    response = lambda_handler(event, {})

    assert response['statusCode'] == 400
    assert "Something went wrong" in response['body']

@patch.dict(os.environ, {
    "REGION_NAME": "us-west-2",
    "USER_POOL_ID": "us-west-2_example",
    "RDS_ENDPOINT": "example.rds.amazonaws.com",
    "RDS_USERNAME": "admin",
    "RDS_PASSWORD": "password",
    "RDS_DB_NAME": "example_db"
})
@patch('create_user.app.boto3.client')
def test_lambda_handler_unexpected_exception(mock_boto_client):
    mock_client = MagicMock()
    mock_boto_client.return_value = mock_client

    # Mock de una excepción inesperada
    mock_client.admin_create_user.side_effect = Exception("Unexpected error")

    event = {
        "body": json.dumps({
            "email": "testuser@example.com"
        })
    }

    response = lambda_handler(event, {})

    assert response['statusCode'] == 500
    assert "Unexpected error" in response['body']

def test_generate_temporary_password():
    password = generate_temporary_password()

    assert len(password) >= 8
    assert any(char.isdigit() for char in password)
    assert any(char.isupper() for char in password)
    assert any(char.islower() for char in password)
    assert any(char in '^$*.[]{}()?-"!@#%&/\\,><\':;|_~+= ' for char in password)
