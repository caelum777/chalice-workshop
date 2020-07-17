import os
import boto3
from chalice import Chalice, AuthResponse, Response
from chalicelib import auth, db


app = Chalice(app_name='chalice-workshop')
app.debug = True
_DB = None
_USER_DB = None

# Change this to use any desired aws profile
# boto3.setup_default_session(profile_name="andres")


@app.route('/login', methods=['POST'])
def login():
    body = app.current_request.json_body
    record = get_users_db().get_item(
        Key={'username': body['username']})['Item']
    jwt_token = auth.get_jwt_token(
        body['username'], body['password'], record)
    return {'token': jwt_token}


@app.authorizer()
def jwt_auth(auth_request):
    token = auth_request.token
    decoded = auth.decode_jwt_token(token)
    return AuthResponse(routes=['*'], principal_id=decoded['sub'])


def get_users_db():
    global _USER_DB
    if _USER_DB is None:
        _USER_DB = boto3.resource('dynamodb').Table(
            os.environ['USERS_TABLE_NAME'])
    return _USER_DB


# Rest API code


def get_app_db():
    global _DB
    if _DB is None:
        _DB = db.DynamoDBTodo(
            boto3.resource('dynamodb').Table(
                os.environ['APP_TABLE_NAME'])
        )
    return _DB


def get_authorized_username(current_request):
    return current_request.context['authorizer']['principalId']


@app.route('/todos', methods=['GET'], authorizer=jwt_auth)
def get_todos():
    username = get_authorized_username(app.current_request)
    todos = get_app_db().list_items(username=username)
    return Response(body={'todos': todos},
                    status_code=200,
                    headers={'Content-Type': 'application/json'})


@app.route('/todos', methods=['POST'], authorizer=jwt_auth)
def add_new_todo():
    body = app.current_request.json_body
    username = get_authorized_username(app.current_request)
    todo_id = get_app_db().add_item(
        username=username,
        description=body.get('description'),
        metadata=body.get('metadata'),
    )
    return Response(body={'item_id': todo_id},
                    status_code=200,
                    headers={'Content-Type': 'application/json'})


@app.route('/todos/{uid}', methods=['GET'], authorizer=jwt_auth)
def get_todo(uid):
    try:
        username = get_authorized_username(app.current_request)
        return Response(body={'todo': get_app_db().get_item(uid, username=username)},
                        status_code=200,
                        headers={'Content-Type': 'application/json'})
    except Exception as ex:
        return Response(body={'message': f"Item [{uid}] does not exist"},
                        status_code=400,
                        headers={'Content-Type': 'application/json'})


@app.route('/todos/{uid}', methods=['DELETE'], authorizer=jwt_auth)
def delete_todo(uid):
    username = get_authorized_username(app.current_request)
    get_app_db().delete_item(uid, username=username)
    Response(body={'message': "Successfully deleted item"},
             status_code=200,
             headers={'Content-Type': 'application/json'})


@app.route('/todos/{uid}', methods=['PUT'], authorizer=jwt_auth)
def update_todo(uid):
    try:
        body = app.current_request.json_body
        username = get_authorized_username(app.current_request)
        get_app_db().update_item(
            uid,
            description=body.get('description'),
            state=body.get('state'),
            metadata=body.get('metadata'),
            username=username)
        return Response(body={'message': "Successfully updated item"},
                        status_code=200,
                        headers={'Content-Type': 'application/json'})
    except Exception as ex:
        return Response(body={'message': f"Item [{uid}] does not exist"},
                        status_code=400,
                        headers={'Content-Type': 'application/json'})
