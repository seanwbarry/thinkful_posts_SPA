import json

from flask import request, Response, url_for
from jsonschema import validate, ValidationError

from . import models
from . import decorators
from posts import app
from .database import session

#JSON Schema describing the structure of a post
post_schema = {
    "properties": {
        "title": {"type": "string"},
        "body": {"type": "string"}
    },
    "required": ["title", "body"]
}

@app.route("/api/posts", methods=["GET"])
@decorators.accept("application/json")
def posts_get():
    """ Get a list of posts """
    #get the querystring arguments
    title_like = request.args.get("title_like")
    
    body_like = request.args.get("body_like")
    
    #get and filter the posts from the database
    #the vars don't execute here (they are just set)
    #here we are suffixing subsequent methods that are attached to objects down the tree
    #eg. ob1 methods . methods attached to ob1 methods . methods attached to methods of ob1 methods . etc
    posts = session.query(models.Post)
    if title_like:
        posts = posts.filter(models.Post.title.contains(title_like))
    if body_like:
        posts = posts.filter(models.Post.body.contains(body_like))
    
    posts = posts.order_by(models.Post.id)
    
    print(posts)
    
    #convert the posts to JSON and return a reponse
    #the vars are executed here (only here is the database 'hit')
    data = json.dumps([post.as_dictionary() for post in posts])
    return Response(data, 200, mimetype="application/json")
    

@app.route("/api/posts/<int:id>", methods=["GET"])
@decorators.accept("application/json")
def post_get(id):
    """ Single post endpoint """
    #get the post from the database
    post = session.query(models.Post).get(id)
    
    #check whether post exists
    #if not return a 404 with a helpful message
    if not post:
        message = "Could not find post with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")
        
    #return the post as JSON
    data = json.dumps(post.as_dictionary())
    return Response(data, 200, mimetype="application/json")

@app.route("/api/posts/<int:id>/delete", methods=["POST"])
@decorators.accept("application/json")
def delete_post(id):
    """delete single post endpoint"""
    #get the post from the db
    returned_post = session.query(models.Post).get(id)
    
    #check whether it exists
    #if not return 404 with helpful message
    if not returned_post:
        message = "Could not find post with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")
    
    #delete post
    #return successful deletion message
    session.delete(returned_post)
    session.commit()
    message = "Post has been deleted!"
    data = json.dumps({"message": message})
    return Response(data, 200, mimetype="application/json")
    
@app.route("/api/posts", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def posts_post():
    """ Add a new post """
    data = request.json
    
    #Check that the supplied JSON is valid and then if it 
    #isn't valid return a 422 Unprocessable Entity error
    try:
        validate(data, post_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")
    
    #Add the post to the database
    post = models.Post(title=data["title"], body=data["body"])
    session.add(post)
    session.commit()
    
    #return a 201 Created, containing the post as JSON and with
    #the Location header set to the location of the post
    data = json.dumps(post.as_dictionary())
    headers = {"Location": url_for("post_get", id=post.id)}
    return Response(data, 201, headers=headers,
                    mimetype="application/json")
    
@app.route("/api/posts/<int:id>", methods=["PUT"])
@decorators.accept("application/json")
@decorators.require("application/json")
def posts_put(id):
    """ Edit a post """
    data = request.json
    
    #check that the supplied JSON is valid and then if it
    #isn't return a 422 Unprocessable Entity error
    try:
        validate(data, post_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")
    
    #commit the edited post to the database
    title = data["title"]
    body = data["body"]
    post = session.query(models.Post).get(id)
    
    post.title = title
    post.body = body
    session.commit()
    
    data = json.dumps(post.as_dictionary())
    headers = {"Location": url_for("post_get", id=post.id)}
    return Response(data, 201, headers=headers,
                    mimetype="application/json")