from selenium                       import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by   import By
from selenium.webdriver.support.ui  import WebDriverWait
from selenium.webdriver.support     import expected_conditions as EC
from selenium.common.exceptions     import NoSuchElementException as NSEE
from selenium.common.exceptions     import TimeoutException as TE

import requests
import time
import os

class TwitterBrowserInterface:
	"""
	A wrapper that interact with the Twitter browser via selenium.

	Attributes
		driver:
			A selenium handler that run a chrome browser 

		wait:

		is_signed_in: bool 
			True if the drive have login successfully to an account

		sleep_time: int
			The amount of time before the next click to prevent Twitter block.

		wait_time: int
			The amount of wait time while finding an element.
	"""
	def __init__(self, PATH = "chromedriver.exe"):
		"""
		Set up a driver

		Parameter:
			PATH: str
				Name or path to the chorme driver
				Note: Chrome Driver and Chrome Browser need to be the same version.
		"""
		self.driver       = webdriver.Chrome(PATH)
		self.is_signed_in = False
		self.sleep_time   = 3
		self.wait_time    = 30

		# Setup wait for later
		self.wait = WebDriverWait(self.driver, self.wait_time)

		print("Successfully setup Chrome driver")

	def __del__(self):
		"""
		Close the browser
		"""
		self.driver.quit()
		print("Quit Chrome driver")

	def sleep(self, sleep_time = None):
		"""
		Sleep for an amount of second indicate by the attribute sleep_time
		"""
		if sleep_time is None:
			sleep_time = self.sleep_time

		print(f"Chrome driver is sleeping for {sleep_time} second(s)")
		time.sleep(sleep_time)	

	def page_scroll(self, last_height = None, scoll_to_height = None):
		"""
		Scroll a page and return new scroll height.
		Return -1 if the height is not change.
		"""	
		if scoll_to_height != None:
			self.driver.execute_script(f'''window.scrollTo(0, {new_height});''')
				
			document_body_scrollHeight = self.driver.execute_script("return document.body.scrollHeight")

			# This condition help return the correct height if we could not reach the specificate height
			if document_body_scrollHeight <= scoll_to_height:
				return document_body_scrollHeight

			return scoll_to_height
	
		if last_height is None:
			last_height = 0

		new_height = last_height + 1500
		self.driver.execute_script(f'''window.scrollTo(0, {new_height});''')

		document_body_scrollHeight = self.driver.execute_script("return document.body.scrollHeight")

		# This condition help return the correct height if we could not reach the height specify by new_height.
		if document_body_scrollHeight < new_height:
			new_height = document_body_scrollHeight

		return new_height

	# Dev Note: Should implement a exception 
	def signin_to_twitter(self, tw_username, tw_password):
		"""
		Login and close the popup window. 
		Return True if success and update self.is_signed_in, otherwise return False.

		Parameter:
			tw_username: str
			
			tw_password: str
		"""

		try:
			# Get to the Twitter page and click the button to go to FB login page
			self.driver.get("https://twitter.com/i/flow/login")
			
			self.sleep() 			
			self.driver.find_element(By.NAME, "text").send_keys(tw_username)
			self.wait.until(EC.presence_of_element_located(
				(By.XPATH, '''//span[contains(text(), "Next")]''')
			)).click()	

			self.sleep() 			
			self.driver.find_element(By.NAME, "password").send_keys(tw_password)
			self.wait.until(EC.presence_of_element_located(
				(By.XPATH, '''//span[contains(text(), "Log in")]''')
			)).click()

			print("Successfully login to Twitter")
			self.is_signed_in = True
		except:
			print("Warning: could not login to Twitter")
		
		return self.is_signed_in

	def load_profile_page_by_username(self, username, extenstion_path = "/with_replies"):
		"""
		Load a profile page by username.

		Parameter:
			username: str
			extension_path: str
		"""
		self.driver.get(f"https://twitter.com/{username}{extenstion_path}")
		print(f'''Successfully load "{username}" profile''')

	def load_a_post_by_url(self, post_url):
		"""
		Load a post by a post url

		Parameter:
			post_url: str
				A sequence of number represent the post.
				Note: post_url is timestamp + other stuff
		"""
		self.driver.get(f"https://twitter.com/i/web/status/{post_url}/")
		print(f'''Successfully load "{post_url}" post''')

	def gather_post_and_photo_url(self, username):
		"""
		Gather all post and photo url of a user.
		Return a list of post data contain post_url and set of image_url
		Assumption:
			The profile page is already loaded
			The page is fully load

		Parameter:
			username: str
		"""
		packages = []

		primary_column = self.wait.until(EC.presence_of_element_located((By.XPATH, '''//div[@data-testid="primaryColumn"]''')))
		cell_elements  = primary_column.find_elements(By.XPATH, '''//div[@data-testid="cellInnerDiv"]''')
		for i, cell in enumerate(cell_elements):
			page_height = cell.get_attribute("style").replace(')', '(').split('(')[1]
			print("Current page height", page_height)

			# Note: a post will have at least a link either to the post itself or the images.
			#       So, we only need to set post_url once.
			post_url  = None
			image_set = set()
			for a_element in cell.find_elements(By.TAG_NAME, "a"):
				href = a_element.get_attribute("href").split('/')
				if len(href) > 4 and href[3] == username and href[4] == "status":
					if len(href) > 6 and href[6] == "photo":
						# Note: for some reason, the program detect a non exist post.
						# Previous debug shows:
						#
						# Current page height 105189px
						# Debug state: 1283563469053112320 - ['https:', '', 'twitter.com', 'xiaoyukikowo', 'status', '1283563469053112320', 'photo', '1']
						# Debug state: 1283563469053112320 - ['https:', '', 'twitter.com', 'xiaoyukikowo', 'status', '1283563469053112320', 'photo', '2']
						# Current page height 105606px
						# Debug state: 1281502587796115462 - ['https:', '', 'twitter.com', 'xiaoyukikowo', 'status', '1281502587796115462', 'photo', '1']
						# Debug state: 1281502587796115462 - ['https:', '', 'twitter.com', 'xiaoyukikowo', 'status', '1281502587796115462', 'photo', '2']
						# Current page height 106002px
						# Debug state: 1280429117075156992 - ['https:', '', 'twitter.com', 'xiaoyukikowo', 'status', '1280428748295163905', 'photo', '1']
						# 
						# Where 1280428748295163905 is non exist
						try:
							image_url = a_element.find_element(By.TAG_NAME, "img").get_attribute("src").split('&')
						except:
							continue

						image_set.add(image_url[0]) 
					else:
						post_url = href[5]

			if post_url:
				package = (post_url, image_set)
				packages.append(package)

		return packages

	def download_image_by_url(image_url, file_name, destination = '.'):
		"""
		Download image from an url and store locally.

		Parameter:
			image_url: str
				The full url to the image

			file_name: str
				Name of the file that we want to store.

			destination: str
				Path to the storage directory.
		"""
		response = requests.get(image_url)
		with open(os.path.join(destination, file_name), "wb") as file:
			file.write(response.content)