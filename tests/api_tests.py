import unittest
import os
import json
try: from urllib.parse import urlparse
except ImportError: from urlparse import urlparse # Python 2 compatibility

# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "posts.config.TestingConfig"

from posts import app
from posts import models
from posts.database import Base, engine, session

class TestAPI(unittest.TestCase):
	""" Tests for the posts API """

	def setUp(self):
		""" Test setup """
		self.client = app.test_client()
		
		# Set up the tables in the database
		Base.metadata.create_all(engine)
	
	def tearDown(self):
		""" Test teardown """
		session.close()
		# Remove the tables and their data from the database
		Base.metadata.drop_all(engine)
		
	def test_get_empty_posts(self):
		""" Getting posts from an empty database """
		response = self.client.get("/api/posts",
					headers=[("Accept", "application/json")]
		)
		
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.mimetype, "application/json")
		
		data = json.loads(response.data.decode("ascii"))
		self.assertEqual(data, [])

	def test_get_posts(self):
		""" getting a single post from a populated database """
		postA = models.Post(title="test Post A", body="testing a")
		postB = models.Post(title="test Post B", body="testing b")
		
		session.add_all([postA, postB])
		session.commit()
		
		response = self.client.get("/api/posts/{}".format(postB.id),
					headers=[("Accept", "application/json")]
		)
		print("postB id")
		print(postB.id)
		print("end postB id")
		print(postA.id)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.mimetype, "application/json")
		
		post = json.loads(response.data.decode("ascii"))
		self.assertEqual(post["title"], "test Post B")
		self.assertEqual(post["body"], "testing b")
		
	def test_get_non_existent_post(self):
		""" Getting a single post which doesn't exist """
		response = self.client.get("/api/posts/1",
					headers=[("Accept", "application/json")]
		)
		
		self.assertEqual(response.status_code, 404)
		self.assertEqual(response.mimetype, "application/json")
		
		data = json.loads(response.data.decode("ascii"))
		self.assertEqual(data["message"], "Could not find post with id 1")
	
	def test_unsupported_accept_header(self):
		response = self.client.get("/api/posts",
					headers=[("Accept", "application/xml")]
		)
		
		self.assertEqual(response.status_code, 406)
		self.assertEqual(response.mimetype, "application/json")
		
		data = json.loads(response.data.decode("ascii"))
		self.assertEqual(data["message"],
						"Request must accept application/json data")

	def test_delete_single_post(self):
		""" deleting a post from a populated database """
		postA = models.Post(title="test Post A", body="testing a")
		
		session.add_all([postA])
		session.commit()
		
		
		response = self.client.post("/api/posts/{}/delete".format(postA.id),
					headers=[("Accept", "application/json")]
		)
		self.assertEqual(response.status_code,200)
		self.assertEqual(response.mimetype, "application/json")
		
		entries = session.query(models.Post).all()
		data = json.loads(response.data.decode("ascii"))
		self.assertEqual(data["message"], "Post has been deleted!")
		self.assertEqual(len(data), 1)

	def test_get_posts_with_title(self):
		""" Filtering posts by title """
		postA = models.Post(title="Post with bells", body="test1")
		postB = models.Post(title="Post with whistles", body="test2")
		postC = models.Post(title="Post with bells and whistles",
							body="test3")
		
		session.add_all([postA, postB, postC])
		session.commit()
		
		response = self.client.get("/api/posts?title_like=whistles",
						headers=[("Accept", "application/json")]
		)
		
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.mimetype, "application/json")
		
		posts = json.loads(response.data.decode("ascii"))
		self.assertEqual(len(posts), 2)
		
		post = posts[0]
		self.assertEqual(post["title"], "Post with whistles")
		self.assertEqual(post["body"], "test2")
		
		post = posts[1]
		self.assertEqual(post["title"], "Post with bells and whistles")
		self.assertEqual(post["body"], "test3")

	def test_get_posts_with_body(self):
		""" Filtering posts by body """
		postA = models.Post(title="Post with bells", body="test1")
		postB = models.Post(title="Post with whistles", body="test2")
		postC = models.Post(title="Post with bells and whistles",
							body="test32")
		
		session.add_all([postA, postB, postC])
		session.commit()
		
		response = self.client.get("/api/posts?body_like=2",
					headers=[("Accept", "application/json")]
		)
		
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.mimetype, "application/json")
		
		posts = json.loads(response.data.decode("ascii"))
		self.assertEqual(len(posts), 2)
		
		post = posts[0]
		self.assertEqual(post["title"], "Post with whistles")
		self.assertEqual(post["body"], "test2")
		
		post = posts[1]
		self.assertEqual(post["title"], "Post with bells and whistles")
		self.assertEqual(post["body"], "test32")
	
	def test_get_posts_with_title_and_body(self):
		""" Filtering posts by title and body"""
		postA = models.Post(title="Post with bells", body="test1")
		postB = models.Post(title="Post with whistles", body="test2")
		postC = models.Post(title="Post with bells and whistles",
							body="test3")
		
		session.add_all([postA, postB, postC])
		session.commit()
		
		response = self.client.get("/api/posts?title_like=bells&body_like=test1",
					headers=[("Accept", "application/json")]
		)
		
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.mimetype, "application/json")
		
		posts = json.loads(response.data.decode("ascii"))
		self.assertEqual(len(posts), 1)
		
		post = posts[0]
		self.assertEqual(post["title"], "Post with bells")
		self.assertEqual(post["body"], "test1")

	def test_post_post(self):
		""" Posting a new post """
		data = {
			"title": "Example Post",
			"body": "test post body"
		}
		
		response = self.client.post("/api/posts",
				data=json.dumps(data),
				content_type="application/json",
				headers=[("Accept", "application/json")]
		)
		
		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.mimetype, "application/json")
		self.assertEqual(urlparse(response.headers.get("Location")).path,
						"/api/posts/1")
						
		data = json.loads(response.data.decode("ascii"))
		self.assertEqual(data["id"], 1)
		self.assertEqual(data["title"], "Example Post")
		self.assertEqual(data["body"], "test post body")
		
		posts = session.query(models.Post).all()
		self.assertEqual(len(posts), 1)
		
		post = posts[0]
		self.assertEqual(post.title, "Example Post")
		self.assertEqual(post.body, "test post body")
	
	def test_unsupported_mimetype(self):
		data = "<xml></xml>"
		response = self.client.post("/api/posts",
				data = json.dumps(data),
				content_type = "application/xml",
				headers = [("Accept", "application/json")]
		)
		
		self.assertEqual(response.status_code, 415)
		self.assertEqual(response.mimetype, "application/json")
		
		data = json.loads(response.data.decode("ascii"))
		self.assertEqual(data["message"],
						"Request must contain application/json data")
	
	def test_invalid_data(self):
		""" Posting a post with an invalid body """
		data = {
			"title": "Example Post",
			"body": 32
		}
		
		response = self.client.post("/api/posts",
				data = json.dumps(data),
				content_type = "application/json",
				headers = [("Accept", "application/json")]
		)
		
		self.assertEqual(response.status_code, 422)
		
		data = json.loads(response.data.decode("ascii"))
		self.assertEqual(data["message"], "32 is not of type 'string'")
		
	def test_missing_data(self):
		""" Posting a post with a missing body """
		data = {
			"title": "Example Post",
		}
		
		response = self.client.post("/api/posts",
				data = json.dumps(data),
				content_type = "application/json",
				headers = [("Accept", "application/json")]
		)
		
		self.assertEqual(response.status_code, 422)
		
		data = json.loads(response.data.decode("ascii"))
		self.assertEqual(data["message"], "'body' is a required property")
	
	def test_editing_post(self):
		""" Editing a post """
		
		# data = {
		# 	"title": "Example Post",
		# 	"body": "test post body"
		# }
		
		# response = self.client.post("/api/posts",
		# 		data=json.dumps(data),
		# 		content_type="application/json",
		# 		headers=[("Accept", "application/json")]
		# )
		
		# self.assertEqual(response.status_code, 201)
		# self.assertEqual(response.mimetype, "application/json")
		# self.assertEqual(urlparse(response.headers.get("Location")).path,
		# 				"/api/posts/1")
						
		# data = json.loads(response.data.decode("ascii"))
		
		# self.assertEqual(data["id"], 1)
		# self.assertEqual(data["title"], "Example Post")
		# self.assertEqual(data["body"], "test post body")
		
		# posts = session.query(models.Post).all()
		# self.assertEqual(len(posts), 1)
		
		# post = posts[0]
		# self.assertEqual(post.title, "Example Post")
		# self.assertEqual(post.body, "test post body")
		
		self.test_post_post()
		
		data = {
			"title": "edited post title!",
			"body": "edited post body!"
		}
		
		response = self.client.put("/api/posts/1",
				data=json.dumps(data),
				content_type="application/json",
				headers=[("Accept", "application/json")]
		)
		
		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.mimetype, "application/json")
		self.assertEqual(urlparse(response.headers.get("Location")).path,
						"/api/posts/1")
		
		data = json.loads(response.data.decode("ascii"))
		
		self.assertEqual(data["id"], 1)
		self.assertEqual(data["title"], "edited post title!")
		self.assertEqual(data["body"], "edited post body!")
		
		posts = session.query(models.Post).all()
		self.assertEqual(len(posts), 1)
		
		post = posts[0]
		self.assertEqual(post.title, "edited post title!")
		self.assertEqual(post.body, "edited post body!")

if __name__ == "__main__":
    unittest.main()