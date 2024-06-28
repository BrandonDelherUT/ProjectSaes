import json
import os
import boto3
import pymysql

def get_db_credentials():
    client = boto3.client('secretsmanager')
    secret_name = os.environ['RDS_SECRET_NAME']
    secret_value = client.get_secret_value(SecretId=secret_name)
    return json.loads(secret_value['SecretString'])

def lambda_handler(event, context):
    db_credentials = get_db_credentials()
    connection = pymysql.connect(
        host=os.environ['RDS_ENDPOINT'],
        user=db_credentials['username'],
        password=db_credentials['password'],
        db=os.environ['RDS_DB_NAME']
    )
    try:
        user_id = event['pathParameters']['id']
        body = json.loads(event['body'])
        username = body.get('username')
        email = body.get('email')

        with connection.cursor() as cursor:
            sql = "UPDATE users SET username = %s, email = %s WHERE user_id = %s"
            cursor.execute(sql, (username, email, user_id))
            connection.commit()

        return {
            'statusCode': 200,
            'body': json.dumps('User updated successfully')
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Internal server error')
        }
    finally:
        connection.close()
