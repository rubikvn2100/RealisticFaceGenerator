import os, sys
import cv2, pickle
import random
import numpy as np
from tensorflow import keras

if __name__ == "__main__":
	INPUT_IMAGE_SIZE = 128
	# source       = "../Crop_Image/high_resolution"
	# destination  = "../Classified_Image"
	source       = "../Classified_Image/manual please"
	destination  = "../Classified_Image/manual result"
	model_source = "./CNN_beauty_face_detection_model"

	def create_image_data_generator():
		for image_name in os.listdir(source):
			input_file_path = f"{source}/{image_name}"
			original_image  = cv2.imread(input_file_path)
			resized_image   = cv2.resize(original_image, (INPUT_IMAGE_SIZE, INPUT_IMAGE_SIZE), interpolation = cv2.INTER_AREA)
			
			yield (original_image, resized_image, image_name)

	image_data_generator = create_image_data_generator()

	CNN_beauty_face_detection_model = keras.models.load_model(model_source)
	batch_size = 1024

	while True:
		images_data = []
		for i in range(batch_size):
			try:
				image_data = next(image_data_generator)
			except StopIteration:
				break
			images_data.append(image_data)

		final_batch_size = len(images_data)
		if final_batch_size == 0:
			break 

		batch = [resized_image * (1. / 255) for _, resized_image, _ in images_data]
		batch = np.array(batch)

		predictions = CNN_beauty_face_detection_model.predict(batch)
		predictions = [1 if prediction > 0.5 else 0 for prediction in predictions]

		for i in range(len(predictions)):
			output_file_path = f"{destination}/{predictions[i]}_by_computer/{images_data[i][2]}"
			cv2.imwrite(output_file_path, images_data[i][0])