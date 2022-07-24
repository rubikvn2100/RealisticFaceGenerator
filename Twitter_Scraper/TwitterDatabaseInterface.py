import sqlite3

class TwitterDatabaseInterface:
	"""
	A wrapper that interact with the Twitter database via sqlite3.

	Attributes
		connection:
			An sqlite3 handler to connect with an sql database
		
		cursor:
			An sqlite3 cursor
	"""
	def __init__(self, database_name = "database.db"):
		"""
		Connect to the Twitter Database.
		Create the neccessary tables if the database does not exist.

		Parameter:
			database_name: str
				Name or path to the database.
		"""
		self.connection = sqlite3.connect(database_name)
		self.cursor     = self.connection.cursor()
		print(f'''Connect to "{database_name}" and create cursor''')

		# Create the neccessary table for database 
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS Twitter_user(
				username			NOT NULL,
				user_id 			NOT NULL,
				resume_last_height	NOT NULL
			)
		''')

		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS Twitter_post(
				post_url	NOT NULL,
				post_id		NOT NULL,
				user_id		NOT NULL,
				post_type	NOT NULL
			)
		''')

		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS Twitter_image(
				image_url		NOT NULL,
				image_id		NOT NULL,
				post_id			NOT NULL, 
				user_id			NOT NULL
			)
		''')

		self.connection.commit()

	def __del__(self):
		"""
		Disconnect from the database.
		"""
		self.connection.close()
		print("Close connection to database")

	def add_user_by_name(self, username):
		"""
		Add an username to the database, and assign a user index.
		Return user_id if successfully add the user, -1 otherwise.
		Give a warning if the username is already in the database.

		Parameter:
			username: str
		"""  
		self.cursor.execute(f'''
			SELECT EXISTS (
				SELECT	* 
				FROM	Twitter_user
				where	username = "{username}"
			)
		''')
		if self.cursor.fetchone()[0] == 1:
			print(f'''Warning: username "{username}" is already in the record''')
			return -1

		self.cursor.execute('''SELECT MAX(user_id) FROM Twitter_user''')
		max_user_id = self.cursor.fetchone()[0]
		max_user_id = max_user_id if max_user_id else 0
		new_user_id = max_user_id + 1

		self.cursor.execute(f'''
			INSERT 
			INTO Twitter_user (
				username, 
				user_id,
				resume_last_height
			)
			VALUES (
				"{username}", 
				{new_user_id},
				0
			)
		''')

		self.connection.commit()
		print(f'''Insert user "{username}" into database''')
		return new_user_id

	def add_post_info(self, post_url, user_id, post_type = 0):
		"""
		Add a post URL and the auther ID into the database, and assign a post index.
		Return post_id if successfully add the post, -1 otherwise.
		Give a warning if the post URL is already in the database.

		Parameter:
			post_url: str
				11 characters represent a post in Twitter.
				The entire URL can be retrieved.
					"https://twitter.com/i/web/status/{post_url}"

			user_id: int

			post_type: int
				0: Not known yet
				1: Image post
				2: Video post
		"""  
		self.cursor.execute(f'''
			SELECT EXISTS (
				SELECT	* 
				FROM	Twitter_post
				WHERE	post_url = "{post_url}"
			)
		''')
		if self.cursor.fetchone()[0] == 1:
			print(f'''Warning: post URL "{post_url}" is already in the record''')
			return -1

		self.cursor.execute('''SELECT MAX(post_id) FROM Twitter_post''')
		max_post_id = self.cursor.fetchone()[0]
		max_post_id = max_post_id if max_post_id else 0
		new_post_id = max_post_id + 1

		self.cursor.execute(f'''
			INSERT 
			INTO Twitter_post (
				post_url, 
				post_id, 
				user_id, 
				post_type
			)
			VALUES (
				"{post_url}", 
				{new_post_id},
				{user_id},
				{post_type}
			)
		''')

		self.connection.commit()
		print(f'''Insert post URL "{post_url}" of user {user_id} into database''')
		return new_post_id

	def add_image_info(self, image_url, post_id, user_id):
		"""
		Add a image URL, post ID, and user ID into the database. Then assign a post index.
		Return image_id if successfully add the image, -1 otherwise.
		Give a warning if the image URL is already in the database.

		Parameter:
			image_url: str
				The full path to the image

			post_id: int
			user_id: int
		"""
		self.cursor.execute(f'''
			SELECT EXISTS (
				SELECT * 
				FROM	Twitter_image
				WHERE	image_url = "{image_url}"
			)
		''')
		if self.cursor.fetchone()[0] == 1:
			print(f'''Warning: image URL is already in the record''')
			return -1

		self.cursor.execute('''SELECT MAX(image_id) FROM Twitter_image''')
		max_image_id = self.cursor.fetchone()[0]
		max_image_id = max_image_id if max_image_id else 0
		new_image_id = max_image_id + 1

		self.cursor.execute(f'''
			INSERT 
			INTO Twitter_image (
				image_url,
				image_id,
				post_id,
				user_id
			)
			VALUES 	(
				"{image_url}",
				{new_image_id},
				{post_id},
				{user_id}
			)
		''')

		self.connection.commit()
		print(f'''Insert Image URL "{image_url}" into database''')
		return new_image_id

	def get_all_user(self):
		"""
		Retrieve all username and user ID from the database
		"""
		self.cursor.execute(f'''SELECT * FROM Twitter_user''')
		return self.cursor.fetchall()

	def set_user_max_height(self, username, resume_last_height):
		self.cursor.execute(f'''
			SELECT	* 
			FROM	Twitter_user
			WHERE	username = "{username}"
		''')
		user = self.cursor.fetchone()
		if user is None:
			print(f'''Warning: username "{username}" is not in the record''')
			return -1

		current_last_height = int(user[2])
		if resume_last_height != -1 and current_last_height > resume_last_height:
			print(f'''Warning: current last height in the databse is higher''')
			return -1

		self.cursor.execute(f'''
			UPDATE	Twitter_user
			SET		resume_last_height = {resume_last_height}
			WHERE	username = "{username}"
		''')
		self.connection.commit()

	def get_unanalyzed_post_URL(self, number_of_post_url = 1):
		"""
		Retrieve an amount of unanalyzed post URL from database, with the corresponding data.

		Parameter:
			number_of_post_url: int
				The maximum amount of post we want to retrieve
		"""
		self.cursor.execute(f'''
			SELECT
				post_url, 
				post_id, 
				user_id
			FROM 	Twitter_post 
			WHERE 	post_type = 0
			LIMIT	{number_of_post_url}
		''')
		return self.cursor.fetchall()

	def set_post_type(self, post_id, post_type):
		self.cursor.execute(f'''
			UPDATE	Twitter_post
			SET		post_type = {post_type}
			WHERE	post_id = {post_id}
		''')
		self.connection.commit()