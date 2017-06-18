from bson.objectid import ObjectId
from flask_pymongo import PyMongo


builtin_list = list


mongo = PyMongo()


def _id(id):
    if not isinstance(id, ObjectId):
        return ObjectId(id)
    return id


def from_mongo(data):
    """
    Translates the MongoDB dictionary format into the format that's expected
    by the application.
    """
    if not data:
        return None

    data['id'] = str(data['_id'])
    return data


def init_app(app):
    mongo.init_app(app)


def list(limit=10, cursor=None):
    cursor = int(cursor) if cursor else 0

    results = mongo.db.posts.find(skip=cursor, limit=10).sort('modifiedDate')
    posts = builtin_list(map(from_mongo, results))

    next_page = cursor + limit if len(posts) == limit else None
    return (posts, next_page)


def list_by_user(user_id, limit=10, cursor=None):
    cursor = int(cursor) if cursor else 0

    results = mongo.db.posts\
        .find({'createdById': user_id}, skip=cursor, limit=10).sort('modifiedDate')
    posts = builtin_list(map(from_mongo, results))

    next_page = cursor + limit if len(posts) == limit else None
    return (posts, next_page)


def read(id):
    result = mongo.db.posts.find_one(_id(id))
    return from_mongo(result)


def create(data):
    new_id = mongo.db.posts.insert(data)
    return read(new_id)


def update(data, id):
    mongo.db.posts.update({'_id': _id(id)}, data)
    return read(id)


def delete(id):
    mongo.db.posts.remove(_id(id))
