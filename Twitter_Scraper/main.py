from TwitterDatabaseInterface import TwitterDatabaseInterface
from TwitterBrowserInterface  import TwitterBrowserInterface
#from authentication           import tw_username, tw_password

if __name__ == "__main__":	
	database_path     = "../Twitter_Image.db"
	image_destination = "../Original_Image"

	database = TwitterDatabaseInterface(database_path)

	for username in username_list:
		database.add_user_by_name(username)

	browser = TwitterBrowserInterface()
	#browser.signin_to_twitter(tw_username, tw_password)
	#browser.sleep(10)

	MAX_SCROLL_TRIAL = 5
	RESET_TRIAL_BY_NEW_POST   = True
	RESET_TRIAL_BY_NEW_HEIGHT = True
	SCAN_NEW_POST             = False
	for username, user_id, resume_last_height  in database.get_all_user():
		resume_last_height = int(resume_last_height)
		last_height        = 0
		remaining_trial    = MAX_SCROLL_TRIAL

		if not SCAN_NEW_POST and resume_last_height == -1:
			continue

		browser.load_profile_page_by_username(username)
		while True:
			browser.sleep(3)	
			remaining_trial -= 1

			packages = browser.gather_post_and_photo_url(username)
			for post_url, image_set in packages:
				post_id = database.add_post_info(post_url, user_id, 1 if image_set else 0)
				if post_id != - 1: 
					if RESET_TRIAL_BY_NEW_POST:
						remaining_trial = MAX_SCROLL_TRIAL
					
					for image_url in image_set:
						database.add_image_info(image_url, post_id, user_id)

						image_url_short = image_url.split('/')[-1].split('?')[0]
						file_name = f'''{str(user_id).zfill(6)}_{post_url}_{image_url_short}.jpg'''
						TwitterBrowserInterface.download_image_by_url(image_url, file_name, image_destination)

			new_height = browser.page_scroll(last_height)

			if new_height > last_height:
				if resume_last_height != -1 and new_height > resume_last_height:
					database.set_user_max_height(username, resume_last_height = last_height)
				
				if RESET_TRIAL_BY_NEW_HEIGHT:
					remaining_trial = MAX_SCROLL_TRIAL

			if remaining_trial == 0:
				if resume_last_height != -1 and new_height == last_height:
					database.set_user_max_height(username, resume_last_height = -1)
				break

			last_height = new_height

	browser.sleep(1000)

