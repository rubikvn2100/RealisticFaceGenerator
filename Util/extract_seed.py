import os

if __name__ == "__main__":
	source = ""

	seed_list = [str(int(file_name[4:-4])) for file_name in os.listdir(source)]
	seed_list = ','.join(seed_list)
	print("Found seed:")
	print(seed_list)

	with open("seed_list.txt", 'w') as file_handler:
		file_handler.write(seed_list)
