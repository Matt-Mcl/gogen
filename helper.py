from gazpacho import get, Soup
import os
import cv2
import numpy as np
from urllib.request import urlopen


def get_tables():
    url = "http://www.puzzles.grosse.is-a-geek.com/uberarchive.html"
    html = get(url)

    soup = Soup(html)

    tables = soup.find('center')[2]

    with open ('tables.html', 'w') as f:
        f.write(str(tables))
        f.close()


def read_tables(puzzle_type):
    with open ('tables.html', 'r') as f:
        html = f.read()
        f.close()

    soup = Soup(html)

    index = 0

    if puzzle_type == "ultra":
        index = 1
    elif puzzle_type == "hyper":
        index = 2
    elif puzzle_type != "uber":
        raise Exception(f"Invalid puzzle type: Choose uber, ultra or hyper. \"{puzzle_type}\" provided.")

    puzzles = soup.find('table')[index].find('tr')[2:]

    urls = []
    url_prefix = "http://www.puzzles.grosse.is-a-geek.com/"

    for u in puzzles:
        links = u.find('a')
        puzzle_link = links[0].attrs.get('href')
        solution_link = links[1].attrs.get('href')

        urls.append((f"{url_prefix}{puzzle_link}", f"{url_prefix}{solution_link}"))

    return urls




def get_board(image_url):
    # y1, y2, x1, x2
    start = [36, 52, 20, 36]

    req = urlopen(image_url)
    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
    img_rgb = cv2.imdecode(arr, -1)
    trans_mask = img_rgb[:,:,3] == 0
    img_rgb[trans_mask] = [255, 255, 255, 255]
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

    # Initialise emtpy 5x5 array
    letters = [['']*5 for _ in range(5)]

    # Loop through 5x5 board
    for i in range(0, 5):
        for j in range(0, 5):

            # Crop image to each letter
            cropped_img = img_gray[start[0] + i * 32:start[1] + i * 32, start[2] + j * 32:start[3] + j * 32]

            # Loop through each template letter
            for filename in os.listdir("letters/board"):
                # Load letter template, remove transparent background and make grey
                template = cv2.imread(f"letters/board/{filename}", cv2.IMREAD_UNCHANGED)
                trans_mask = template[:,:,3] == 0
                template[trans_mask] = [255, 255, 255, 255]
                template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

                # Check if template matches letter image
                res = cv2.matchTemplate(cropped_img, template,cv2.TM_CCOEFF_NORMED)
                maxVal = cv2.minMaxLoc(res)[1]
                
                # Check against threshold value
                if maxVal > 0.95:
                    letters[i][j] = filename[0]
                    break

    return letters


def get_words(image_url):
    # y1, y2, x1, x2
    start = [35, 44, 180, 236]

    req = urlopen(image_url)
    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
    img_rgb = cv2.imdecode(arr, -1)
    trans_mask = img_rgb[:,:,3] == 0
    img_rgb[trans_mask] = [255, 255, 255, 255]
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

    words = []
    columns = 2

    # Means there is only 1 column of words
    if img_gray.shape[1] < 290:
        columns = 1

    # Loop through each column of words
    for i in range(0, columns):
        # Loop through each row for each word
        for j in range(0, 11):
            # Crop image to just word
            cropped_img = img_gray[start[0] + j * 14:start[1] + j * 14, start[2] + i * 49:start[3] + i * 49]
            letters = []

            # Loop through each letter in word
            for k in range(0, 8):
                # Crop word to letter
                letter_img = cropped_img[0:9, 0 + k * 7:6 + k * 7]

                # Loop through each template letter
                for filename in os.listdir("letters/words"):
                    # Load letter template, remove transparent background and make grey
                    template = cv2.imread(f"letters/words/{filename}", cv2.IMREAD_UNCHANGED)
                    trans_mask = template[:,:,3] == 0
                    template[trans_mask] = [255, 255, 255, 255]
                    template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

                    # Check if template matches letter image
                    res = cv2.matchTemplate(letter_img, template,cv2.TM_CCOEFF_NORMED)
                    maxVal = cv2.minMaxLoc(res)[1]

                    # Check against threshold value
                    if maxVal > 0.95:
                        letters.append(filename[0])
                        break
                
                else:
                    if len(letters) > 0:
                        break

            words.append(letters)

    # Combine letters into list of words
    words = [''.join(w) for w in words if len(w) > 1]

    return words

