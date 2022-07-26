# Realistic Face Generator
A StyleGAN variant that generates cosplayer faces

![](https://raw.githubusercontent.com/rubikvn2100/RealisticFaceGenerator/main/sample/Realistic%20Face%20Generator%20Thumbnail.png)

StyleGAN is a famous generative machine learning model found by researchers at NVIDIA. It is capable of creating realistic faces. I would like to fine-tune the model to create cosplayer faces. In other to achieve the goal, a dataset of cosplayer faces is needed. Such dataset can be created in three steps.

- Gather Images from social media.
- Detect and crop out the faces.
- Filter out faces.

## Gather Images
One of the places where we can gather images is Twitter. At the time of writing, tweets can be accessed without a login credential. So, I build a [Twitter Scraper](https://github.com/rubikvn2100/RealisticFaceGenerator/tree/main/Twitter_Scraper) using [Selenium](https://www.selenium.dev/), and the data gathered will be stored in a [sqlite3](https://docs.python.org/3/library/sqlite3.html) relational database. In other to keep the code clean and easy to read, I create interfaces for [browser](https://github.com/rubikvn2100/RealisticFaceGenerator/blob/main/Twitter_Scraper/TwitterBrowserInterface.py) and [database](https://github.com/rubikvn2100/RealisticFaceGenerator/blob/main/Twitter_Scraper/TwitterDatabaseInterface.py). A [main program](https://github.com/rubikvn2100/RealisticFaceGenerator/blob/main/Twitter_Scraper/main.py) is put on top to control them. You will need to download the latest [Chorme Driver](https://chromedriver.chromium.org/downloads) and put it in the same directory as the main program.

Note 1: at the time of writing, the database path and image destination are hard-coded into the program. 

Note 2: at the time of writing, you will need to add some Twitter usernames into the database manually by adding elements into username_list or using [DB Browser](https://sqlitebrowser.org/). It is recommended to use the first method.

While the program running, it will open each user profile page, scroll down, extract image links in new posts, and store the result in the database.

# Detect and crop out the faces 
A dataset for StyleGAN consists of square image of faces. In other to detect faces from the raw images that we collect above, I use [Haar Cascades](https://medium.com/analytics-vidhya/haar-cascades-explained-38210e57970d) from [Open CV](https://opencv.org/). But, Haar's faces detector is not perfect. I need to also use Haar's eyes detector by using a simple condition that only choose faces that contain eyes. It incrersese's the detection rate significantly. 

Open CV is also a rich libary of image manipulation. So, it is helpful to use the read, crop, and write functions to help crop out the faces.

# Filter out faces.
(await to be written)

# Training using Colab GPU
(await to be written)

Run the follow command to use NVIDIA_stylegan2_ada_dataset_tool.py

python NVDIA_stylegan2_ada_dataset_tool.py --source Classified_Image\Asian_face_dataset_limit_256 --dest Classified_Image\dataset_256 --width 256 --height 256

# Results
(await to be written)