import os
import cv2

class FaceIsolatorInterface:
	"""
	A wrapper that use open cv2 to isolate face

	Attributes
		face_detector:

		eye_detector:

		output_config: List of tuple of (size, path)
			Configuration for output directory where:
				int size input coresponse with "below_{size}"
			There is at least a high resolution config
			Size is None if show_box is True

		image_generator:
			A generator that return image and gray version.

		show_box:
			If we want to display box
		
		verbose:
			True if we want to display log message
	"""
	def __init__(self, source = "./data", destination = "./result", 
		output_config = [], show_box = False, verbose = False):
		"""
		Initiate the detectors. 
		Create the source and destination directory if needed.

		Parameter:
			source: str
				Path to directory that store the input.

			destination: str
				Path to directory that we will put the output to.

			output_config: tuple 
				Configuration for output directory.

			show_box: bool

			verbose: bool
		"""
		self.face_detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
		self.eye_detector  = cv2.CascadeClassifier("haarcascade_eye.xml")
		self.show_box = show_box
		self.verbose  = verbose

		if not os.path.exists(source):
			os.makedirs(source)

		if not os.path.exists(destination):
			os.makedirs(destination)

		self.output_config = [(10**6, f"{destination}/high_resolution")]
		for size in output_config:
			path = f"{destination}/below_{size}"
			self.output_config.append((size, path))
		
		for size, path in self.output_config:
			if not os.path.exists(path):
				os.makedirs(path)

		def create_image_generator(source):
			"""
			Return name, color image and gray version from source input.

			Parameter:
				source: str
					The path to the directory that store images.
			"""
			for i, image_name in enumerate(os.listdir(source)):
				if self.verbose and i % 250 == 0:
					print(f"load {i} images")

				file_path = f'''{source}/{image_name}'''
				try:
					image = cv2.imread(file_path)
					gray  = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
				except:
					print(f'''Warning: could not open {file_path}''')
					continue

				yield((image_name, image, gray))

		self.image_generator = create_image_generator(source)

	def detect_face(self, image = None, gray_image = None):
		"""
		Detect face and return a list of faces.
		Each face has format (x, y, w, h)

		Parameter:
			image: numpy array
				Color version of the image.

			gray_image: numpy array
				Grayscale version of the image.
		"""
		if gray_image is None:
			if image is None:
				return -1
			else:
				try: 
					gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
				except:
					return -1

		faces = self.face_detector.detectMultiScale(gray_image, 1.1, 4)
		faces = list(faces)
		faces.sort(key = lambda face: face[0] * 10000 + face[1]) 
		return faces

	def detect_eye(self, image = None, gray_image = None):
		"""
		Detect eye and return a list of eyes.
		Each eye has format (x, y, w, h)

		Parameter:
			image: numpy array
				Color version of the image.

			gray_image: numpy array
				Grayscale version of the image.
		"""
		if gray_image is None:
			if image is None:
				return -1
			else:
				try: 
					gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
				except:
					return -1

		eyes = self.eye_detector.detectMultiScale(gray_image, 1.1, 4)
		eyes = list(eyes)
		eyes.sort(key = lambda eye: eye[0] * 10000 + eye[1])
		return eyes

	def detect_face_with_eye(self, image, gray_image = None):
		"""
		Detect face that has eye and return a list of tuple where each tuple is
			(face, list of eye)
			Note: list of eye will be empty if show_box is False
		Each face and eye has format (x, y, w, h)

		Parameter:
			image: numpy array
				Color version of the image.

			gray_image: numpy array
				Grayscale version of the image.
		"""
		if gray_image is None:
			try: 
				gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
			except:
				return -1

		faces = self.detect_face(gray_image = gray_image)
		if len(faces) == 0:
			return []

		eyes = self.detect_eye(gray_image = gray_image)
		if len(eyes) == 0:
			return []

		result = []
		# print(f"Found {len(faces)} faces and {len(eyes)} eyes")
		for face in faces:
			face_x1, face_y1, face_w, face_h = face
			face_x2 = face_x1 + face_w
			face_y2 = face_y1 + face_h
			# print("face x1, y1, x2, y2", face_x1, face_y1, face_x2, face_y2)

			eye_list = []
			for eye in eyes:
				eye_x1, eye_y1, eye_w, eye_h = eye
				eye_x2 = eye_x1 + eye_w
				eye_y2 = eye_y1 + eye_h
				eye_cx = eye_x1 + eye_w / 2
				eye_cy = eye_y1 + eye_h / 2
				# print("eye cx cy", eye_cx, eye_cy)

				if face_x1 <= eye_cx and eye_cx <= face_x2 and face_y1 <= eye_cy and eye_cy <= face_y2:
					eye_list.append(eye)
					if not self.show_box:
						break

			if len(eye_list) != 0:
				result.append((face, eye_list))

		return result
			
	def export_results(self, original_image_name, image, faces_and_eyes_info, face_ratio = 1.6):
		"""
		Export image to the coresponding directory setup in output_config

		Parameter:
			original_image_name: str
				
			image: numpy array
				The original image

			faces_and_eyes_info: list of tuple where each tuple contain 
				(face, list of eye)
				Where face and eye has the form (x, y, w, h)

			face_ratio: float
				The minimum ratio of face and image
		"""
		if len(faces_and_eyes_info) == 0:
			return

		image_w = image.shape[1]
		image_h = image.shape[0]

		for i, (face, eyes) in enumerate(faces_and_eyes_info):
			face_x, face_y, face_w, face_h = face
			face_cx = int(face_x + face_w / 2)
			face_cy = int(face_y + face_h / 2)

			output_size = min(image_w, image_h, int(face_w * face_ratio))

			output_x = int(face_cx - output_size / 2)
			if output_x < 0:
				output_x = 0
			elif output_x + output_size > image_w:
				output_x = image_w - output_size		# <-- Oh My God, I have a bug here (which I fixed)
														#     It was output_y instead of output_x
			output_y = int(face_cy - output_size / 2)
			if output_y < 0:
				output_y = 0
			elif output_y + output_size > image_h:
				output_y = image_h - output_size

			output_file_name = f"{original_image_name[:-4]}_face_{i}_size_{output_size}.jpg"
			
			min_size         = 10**9
			destination_path = ""
			for config_size, config_path in self.output_config:
				if output_size < config_size and min_size > config_size:
					min_size         = config_size
					destination_path = config_path

			output_path  = f"{destination_path}/{output_file_name}"
			if self.show_box:
				cv2.rectangle(image, (face_x, face_y), (face_x + face_w, face_y + face_h), (0, 255, 0), 2)
				for eye_x, eye_y, eye_w, eye_h  in eyes:
					cv2.rectangle(image, (eye_x, eye_y), (eye_x + eye_w, eye_y + eye_h), (0, 0, 255), 2)

			try:
				cv2.imwrite(output_path, image[output_y:output_y + output_size:, output_x:output_x + output_size:, ::])
			except:
				print(f'''Warning: fail to write "{output_path}"''')