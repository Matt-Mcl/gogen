#%%

import os
import cv2
import numpy as np
from urllib.request import urlopen


# %%

# y1, y2, x1, x2
start = [35, 44, 180, 236]

req = urlopen('http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/uber/uber20220621puz.png')
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
        cropped_img = img_gray[start[0] + j * 14:start[1] + j * 14, start[2] + i * 56:start[3] + i * 56]
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
                w, h = template.shape[::-1]

                # Check if template matches letter image
                res = cv2.matchTemplate(letter_img, template,cv2.TM_CCOEFF_NORMED)
                maxVal = cv2.minMaxLoc(res)[1]

                # Check against threshold value
                if maxVal > 0.95:
                    letters.append(filename[0])
                    break

        words.append(letters)

# Combine letters into list of words
words = [''.join(w) for w in words if len(w) > 1]

print(words)

# %%
