from FaceIsolatorInterface import FaceIsolatorInterface

if __name__ == "__main__":
	# try:
	# 	os.remove("./result") # Just for testing
	# except:
	# 	pass
	
	face_isolator = FaceIsolatorInterface("../Original_Image", "../Crop_Image", output_config = [128, 256], show_box = False, verbose = True)

	while True:
		try:
			name, image, gray = next(face_isolator.image_generator)
			faces_info = face_isolator.detect_face_with_eye(image, gray)
			face_isolator.export_results(name, image, faces_info)
		except StopIteration:
			break