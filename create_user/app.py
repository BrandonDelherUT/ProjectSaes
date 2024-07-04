import json
import os
import random
import string
import boto3
from botocore.exceptions import ClientError
from connection_bd import connect_to_db, execute_query, close_connection
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def lambda_handler(event, context):
    body_parameters = json.loads(event["body"])
    email = body_parameters.get('email')
    username = email  # Usar el correo electrónico como nombre de usuario
    password = generate_temporary_password()
    role = "usuario"

    if email is None:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Missing input parameters"})
        }

    try:
        # Configura el cliente de Cognito
        client = boto3.client('cognito-idp', region_name=os.environ['REGION_NAME'])
        user_pool_id = os.environ['USER_POOL_ID']

        # Verifica si el usuario ya existe
        try:
            client.admin_get_user(
                UserPoolId=user_pool_id,
                Username=username
            )
            return {
                'statusCode': 400,
                'body': json.dumps({"error_message": "User account already exists"})
            }
        except client.exceptions.UserNotFoundException:
            pass  # El usuario no existe, podemos continuar con la creación

        # Crea el usuario con correo no verificado y contraseña temporal que se envia automáticamente a su correo
        client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'false'},
            ],
            TemporaryPassword=password
        )

        # Verifica si el grupo 'usuario' existe
        try:
            client.get_group(
                GroupName=role,
                UserPoolId=user_pool_id
            )
        except client.exceptions.ResourceNotFoundException:
            # Si el grupo no existe, créalo
            client.create_group(
                GroupName=role,
                UserPoolId=user_pool_id
            )

        client.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=username,
            GroupName=role
        )

        # Inserta el usuario en la base de datos
        insert_db(username, password, email, role)

        return {
            'statusCode': 200,
            'body': json.dumps({"message": "User created successfully, verification email sent."})
        }

    except ClientError as e:
        logging.error(f"ClientError: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({"error_message": e.response['Error']['Message']})
        }
    except Exception as e:
        logging.error(f"Exception: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({"error_message": str(e)})
        }

def insert_db(username, password, email, role):
    query = f"INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)"
    connection = connect_to_db(
        host=os.environ['RDS_ENDPOINT'],
        user=os.environ['RDS_USERNAME'],
        password=os.environ['RDS_PASSWORD'],
        database=os.environ['RDS_DB_NAME']
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (username, password, email, role))
            connection.commit()
    finally:
        close_connection(connection)

def generate_temporary_password(length=12):
    """Genera una contraseña temporal segura"""
    special_characters = '^$*.[]{}()?-"!@#%&/\\,><\':;|_~`+= '
    characters = string.ascii_letters + string.digits + special_characters

    while True:
        # Genera una contraseña aleatoria
        password = ''.join(random.choice(characters) for _ in range(length))

        # Verifica los criterios
        has_digit = any(char.isdigit() for char in password)
        has_upper = any(char.isupper() for char in password)
        has_lower = any(char.islower() for char in password)
        has_special = any(char in special_characters for char in password)

        if has_digit and has_upper and has_lower and has_special and len(password) >= 8:
            return password
