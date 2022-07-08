#%%

import os
import cv2
import numpy as np
from urllib.request import urlopen


#%%

# y1, y2, x1, x2
start = [36, 52, 20, 36]

req = urlopen('http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/uber/uber20220621puz.png')
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
            w, h = template.shape[::-1]

            # Check if template matches letter image
            res = cv2.matchTemplate(cropped_img, template,cv2.TM_CCOEFF_NORMED)
            maxVal = cv2.minMaxLoc(res)[1]
            
            # Check against threshold value
            if maxVal > 0.95:
                letters[i][j] = filename[0]
                break

print(letters)


# %%
