import os
import cv2
import constants
import pytesseract
import numpy as np
from fuzzywuzzy import process, fuzz, utils

pytesseract.pytesseract.tesseract_cmd = constants.TESSERACT_BINARY

def crop_image(im):
    return im[125:650, 0:100].copy(), im[125:650, 1820:1920].copy()

def ocr(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY_INV, 25, -60)
    img = cv2.bitwise_not(binary)
    #cv2.imshow('img', img)
    #cv2.waitKey(0)
    return pytesseract.image_to_string(img)

def get_champs(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    results = []
    sift = cv2.SIFT_create(nfeatures=0, nOctaveLayers=3,
                           contrastThreshold=0.04, edgeThreshold=10000000,
                           sigma=0.8)
    index_params = dict(algorithm=5, trees=2)
    search_params = dict(checks=200)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    kp2, des2 = sift.detectAndCompute(image, None)
    good = []
    kps = {}
    for champ in os.listdir('../data/champions'):
        pic = os.path.join('../data/champions', champ)
        name = os.path.splitext(champ)[0]
        pic = cv2.imread(pic)
        pic = cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY)
        pic = cv2.GaussianBlur(pic, (3, 3), 0)
        kp1, des1 = sift.detectAndCompute(pic, None)
        matches = flann.knnMatch(des1, des2, k=2)
        kps[name] = kp1
        curr = []
        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                curr.append(m)
        good.append((curr, name))
    good.sort(key=lambda x: len(x[0]))
    for m, name in good[-5:]:
        src_pts = np.float32([ kps[name][n.queryIdx].pt for n in m ]).reshape(-1,1,2)
        dst_pts = np.float32([ kp2[n.trainIdx].pt for n in m ]).reshape(-1,1,2)
        M, mask = cv2.findHomography(src_pts, dst_pts, method=cv2.RANSAC)
        matchesMask = mask.ravel().tolist()
        h,w = pic.shape
        pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
        dst = cv2.perspectiveTransform(pts,M)
        yVal = dst[0][0][1]
        results.append((name, yVal))
    results.sort(key = lambda x: x[1])
    return [x[0] for x in results]

def get_names(image, team1, team2, league):
    names = []
    final_score = 0
    team1Name = team1
    team2Name = team2
    originalTeam1 = team1
    originalTeam2 = team2
    if any([x in team1Name for x in ['Team', 'The']]):
        team1Name = team1Name.split()[1]
    else:
        team1Name = team1Name.split()[0]
    if any([x in team2Name for x in ['Team', 'The']]):
        team2Name = team2Name.split()[1]
    else:
        team2Name = team2Name.split()[0]
    team1 = constants.rosters['Team'].apply(lambda x: x.lower()).str.split()
    mask = team1.apply(lambda x: team1Name.lower() in x)
    team1 = ','.join(constants.rosters[mask]['ID'].ravel().flatten()).split(',')
    team1Names = ','.join(constants.rosters[mask]['Name'].ravel().flatten()).split(',')
    team2 = constants.rosters['Team'].apply(lambda x: x.lower()).str.split()
    mask = team2.apply(lambda x: team2Name.lower() in x)
    team2 = ','.join(constants.rosters[mask]['ID'].ravel().flatten()).split(',')
    team2Names = ','.join(constants.rosters[mask]['Name'].ravel().flatten()).split(',')
    score = 0
    h = 21
    k = 104
    yVals = [i * k for i in range(5)]
    for y in yVals:
        candidates = []
        for j in range(8):
            y = y + j 
            name = ocr(image[y:y+h, 0:100])
            #print(name)
            if utils.full_process(name):
                #team1Res = process.extractOne(name, team1, scorer=fuzz.partial_ratio)
                #team2Res = process.extractOne(name, team2, scorer=fuzz.partial_ratio)
                team1Res = process.extractOne(name, team1, scorer=fuzz.ratio)
                team2Res = process.extractOne(name, team2, scorer=fuzz.ratio)
                #print(team1Res, team2Res)
                score = score - team1Res[1]
                score = score + team2Res[1]
                candidates.append(team1Res if team1Res[1] > team2Res[1] else team2Res)
                #if abs(team1Res[1] - team2Res[1]) > 90:
                if team1Res[1] > 60 or team2Res[1] > 60:
                    break
        names.append(max(candidates, key = lambda x: x[1])[0])
        final_score = final_score + max(candidates, key = lambda x: x[1])[1]
    assert(final_score > 260)
    if score < 0:
        return [process.extractOne(x, team1Names, scorer=fuzz.partial_ratio)[0] for x in names], originalTeam1
    else:
        return [process.extractOne(x, team2Names, scorer=fuzz.partial_ratio)[0] for x in names], originalTeam2

def mse(im1, im2):
    img1 = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
    img2 = cv2.cvtColor(im2, cv2.COLOR_BGR2GRAY)
    h, w = img1.shape
    diff = cv2.subtract(img1, img2)
    err = np.sum(diff**2)
    mse = err/(float(h*w))
    return mse

def banner_present(top_image, league):
    banner_name = os.path.join('../data/banners', league.string+'.png')
    template = cv2.imread(banner_name)
    res = cv2.matchTemplate(top_image, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    return max_val >= .5

