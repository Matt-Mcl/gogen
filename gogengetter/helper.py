from gazpacho import get, Soup
import os
import cv2
import numpy as np
import warnings
from urllib.request import urlopen

np.seterr(all="ignore")

def get_tables():
    # Get table urls
    # Try multiple times as a dropped connection can cause this to fail
    for _ in range(0, 3):
        try:
            url = "http://www.puzzles.grosse.is-a-geek.com/uberarchive.html"
            html = get(url)

            soup = Soup(html)

            tables = soup.find('center')[2]

            with open ('tables.html', 'w') as f:
                f.write(str(tables))
                f.close()
        except TypeError:
            continue
        break
    else:
        raise Exception("Could not get tables")


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

        if links is not None:
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
    start = [35, 44, 180, 242]

    req = urlopen(image_url)
    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
    img_rgb = cv2.imdecode(arr, -1)
    trans_mask = img_rgb[:,:,3] == 0
    img_rgb[trans_mask] = [255, 255, 255, 255]
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

    words = []

    # Loop through each column of words
    for i in range(0, 2):
        # Loop through each row for each word
        for j in range(0, 11):
            # Crop image to just word
            cropped_img = img_gray[start[0] + j * 14:start[1] + j * 14, start[2] + i * 42:start[3] + i * 42]
            letters = []

            # Debug
            # cv2.imwrite(f"temp/{i}{j}.png", cropped_img)

            # Loop through each letter in word
            for k in range(0, 9):
                # Crop word to letter
                letter_img = cropped_img[0:9, 0 + k * 7:6 + k * 7]

                # Check if letter is blank
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                    if np.mean(letter_img) == 255:
                        if len(letters) > 1:
                            # Check that word isn't the end of another word
                            if len(list(filter(lambda x: ''.join(letters) in x, words))) == 0:
                                break
                            else:
                                letters = []
                        elif len(letters) > 0:
                            letters = []

                # Loop through each template letter
                for filename in os.listdir("letters/words"):
                    # Load letter template, remove transparent background and make grey
                    template = cv2.imread(f"letters/words/{filename}", cv2.IMREAD_UNCHANGED)
                    trans_mask = template[:,:,3] == 0
                    template[trans_mask] = [255, 255, 255, 255]
                    template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

                    # Check if template matches letter image
                    try:
                        res = cv2.matchTemplate(letter_img, template,cv2.TM_CCOEFF_NORMED)
                    except:
                        pass
                    maxVal = cv2.minMaxLoc(res)[1]

                    # Check against threshold value
                    if maxVal > 0.95:
                        letters.append(filename[0])
                        break

            # Checks parts of words aren't being repeated
            if len(list(filter(lambda x: ''.join(letters) in x, words))) == 0:
                words.append(''.join(letters))

    return words

