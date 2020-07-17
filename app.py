import os
import boto3
from chalice import Chalice, Response
from chalicelib import db


app = Chalice(app_name='chalice-workshop')
app.debug = True
_DB = None

# Change this to use any desired aws profile
# boto3.setup_default_session(profile_name="andres")


def get_app_db():
    global _DB
    if _DB is None:
        _DB = db.DynamoDBTodo(
            boto3.resource('dynamodb').Table(
                os.environ['APP_TABLE_NAME'])
        )
    return _DB


@app.route('/todos', methods=['GET'])
def get_todos():
    return Response(body={'todos': get_app_db().list_items()},
                    status_code=200,
                    headers={'Content-Type': 'application/json'})


@app.route('/todos', methods=['POST'])
def add_new_todo():
    body = app.current_request.json_body
    todo_id = get_app_db().add_item(
        description=body.get('description'),
        metadata=body.get('metadata'),
    )
    return Response(body={'item_id': todo_id},
                    status_code=200,
                    headers={'Content-Type': 'application/json'})


@app.route('/todos/{uid}', methods=['GET'])
def get_todo(uid):
    try:
        return Response(body={'todo': get_app_db().get_item(uid)},
                        status_code=200,
                        headers={'Content-Type': 'application/json'})
    except Exception as ex:
        return Response(body={'message': f"Item [{uid}] does not exist"},
                        status_code=400,
                        headers={'Content-Type': 'application/json'})


@app.route('/todos/{uid}', methods=['DELETE'])
def delete_todo(uid):
    get_app_db().delete_item(uid)
    return Response(body={'message': "Successfully deleted item"},
                    status_code=200,
                    headers={'Content-Type': 'application/json'})


@app.route('/todos/{uid}', methods=['PUT'])
def update_todo(uid):
    body = app.current_request.json_body
    try:
        get_app_db().update_item(
            uid,
            description=body.get('description'),
            state=body.get('state'),
            metadata=body.get('metadata'))
        return Response(body={'message': "Successfully updated item"},
                        status_code=200,
                        headers={'Content-Type': 'application/json'})
    except Exception as ex:
        return Response(body={'message': f"Item [{uid}] does not exist"},
                        status_code=400,
                        headers={'Content-Type': 'application/json'})
