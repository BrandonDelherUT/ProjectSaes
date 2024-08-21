import json
import os
import random
import string
import uuid
import boto3
from botocore.exceptions import ClientError
from connection_bd import connect_to_db, execute_query, close_connection
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',  # Permite todas las fuentes
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'OPTIONS,POST',  # Métodos permitidos
    }

    body_parameters = json.loads(event["body"])
    email = body_parameters.get('email')
    password = generate_temporary_password()
    role = "usuario"

    if email is None:
        return {
            "statusCode": 400,
            "headers": headers,
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
                Username=email
            )
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({"error_message": "User account already exists"})
            }
        except client.exceptions.UserNotFoundException:
            pass  # El usuario no existe, podemos continuar con la creación

        # Crea el usuario con el atributo custom:role y el email como Username
        response = client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'false'},
                {'Name': 'custom:role', 'Value': role}  # Añade el rol como atributo personalizado
            ],
            TemporaryPassword=password
        )

        # Recupera el cognito:username generado por Cognito (user_id en la base de datos)
        cognito_username = response['User']['Username']

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
            Username=email,
            GroupName=role
        )

        # Inserta el usuario en la base de datos y registra el perfil
        insert_db(cognito_username, email, password, role)

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({"message": "User created successfully, verification email sent."})
        }

    except ClientError as e:
        logging.error(f"ClientError: {e}")
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({"error_message": e.response['Error']['Message']})
        }
    except Exception as e:
        logging.error(f"Exception: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({"error_message": str(e)})
        }

def insert_db(user_id, email, password, role):
    connection = connect_to_db(
        host=os.environ['RDS_ENDPOINT'],
        user=os.environ['RDS_USERNAME'],
        password=os.environ['RDS_PASSWORD'],
        database=os.environ['RDS_DB_NAME']
    )
    try:
        with connection.cursor() as cursor:
            # Inserta el usuario en la tabla de usuarios con cognito_username como user_id
            user_insert_query = """
                INSERT INTO users (user_id, username, password, email, role) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(user_insert_query, (user_id, email, password, email, role))
            connection.commit()

            # Inserta un registro en la tabla profile con el user_id
            profile_insert_query = """
                INSERT INTO user_profiles (user_id) 
                VALUES (%s)
            """
            cursor.execute(profile_insert_query, (user_id,))
            connection.commit()

    finally:
        close_connection(connection)

def generate_temporary_password(length=12):
    """Genera una contraseña temporal segura"""
    special_characters = '^$*.[]{}()?-"!@#%&/\\,><\':;|_~+= '
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
