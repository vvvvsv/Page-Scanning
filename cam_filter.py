import numpy as np
import cv2
from scipy import signal

def sharpen(img, amount=5.0):
    """
    锐化滤镜
    img:    原始图片
    amount: 锐化程度
    return: 锐化滤镜处理后的图片
    """
    # 使用反锐化遮罩进行锐化处理
    blur_img = cv2.GaussianBlur(img.copy(), (5, 5), 0.0)
    sharp_img = float(amount + 1) * img - float(amount) * blur_img
    sharp_img = np.maximum(sharp_img, np.zeros(sharp_img.shape))
    sharp_img = np.minimum(sharp_img, 255 * np.ones(sharp_img.shape))
    sharp_img = sharp_img.round().astype(np.uint8)

    # 最后做一次高斯模糊，去除毛刺
    sharp_img = cv2.GaussianBlur(sharp_img, (5,5), 0.0)
    return sharp_img

def original(img):
    """
    原图滤镜
    img:    原始图片
    return: 原图滤镜处理后的图片
    """
    return img.copy()

def grayscale(img):
    """
    灰度滤镜
    img:    原始图片
    return: 灰度滤镜处理后的图片
    """
    return cv2.cvtColor(img.copy(), cv2.COLOR_BGR2GRAY)

def black_and_white(img):
    """
    黑白滤镜
    将原图用自适应阈值二值化
    img:    原始图片
    return: 黑白滤镜处理后的图片
    """
    gray_img = cv2.cvtColor(img.copy(), cv2.COLOR_BGR2GRAY)
    binary_img = cv2.adaptiveThreshold(gray_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 10)
    return binary_img

def lighten(img, value=50):
    """
    增亮滤镜
    img:    原始图片
    value:  增亮程度
    return: 增亮滤镜处理后的图片
    """
    # 转化为hsv，增强v即可
    hsv = cv2.cvtColor(img.copy(), cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    lim = 255 - value
    v[v > lim] = 255
    v[v <= lim] += value

    hsv = cv2.merge((h, s, v))
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

def recommend_bandw(img):
    """
    推荐滤镜（黑白）
    直接使用 cv2.adaptiveThreshold 无法使得背景全为白色、文字全为黑色。
    因为背景是渐变的，若直接使用均值当作阈值，总有一些背景像素在阈值之下。
    所以需要将阈值乘以一个系数，比如 0.9，以过滤掉所有背景。
    img:    原始图片
    return: 滤镜处理后的图片
    """
    gray_img = cv2.cvtColor(img.copy(), cv2.COLOR_BGR2GRAY)

    kernel = np.ones((9, 9))
    sums = signal.correlate2d(gray_img, kernel, 'same')
    cnts = signal.correlate2d(np.ones_like(gray_img), kernel, 'same')
    means = sums / cnts

    binary_img = np.where(gray_img < means * 0.9, 0, 255).astype(np.uint8)
    return binary_img

def recommend_color(img):
    """
    推荐滤镜（彩色）
    去除阴影，可以保留文字颜色
    img:    原始图片
    return: 滤镜处理后的图片
    """
    bgr_planes = cv2.split(img.copy())
    result_planes = []

    for plane in bgr_planes:
        dilated_img = cv2.dilate(plane, np.ones((7,7), np.uint8))
        bg_img = cv2.medianBlur(dilated_img, 21)
        diff_img = 255 - cv2.absdiff(plane, bg_img)
        norm_img = cv2.normalize(diff_img,None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        result_planes.append(norm_img)

    return cv2.merge(result_planes)

def morphology_open(img):
    """
    开运算滤镜
    做开运算，先腐蚀后膨胀，消除污染乱点
    img:    原始图片
    return: 开运算处理后的图片
    """
    eroded_img = cv2.erode(img.copy(), np.ones((3, 3)), 1)
    dilated_img = cv2.dilate(eroded_img, np.ones((3, 3)), 1)
    return dilated_img

def morphology_close(img):
    """
    闭运算滤镜
    做闭运算，先膨胀后腐蚀，填充空洞断裂
    img:    原始图片
    return: 闭运算处理后的图片
    """
    dilated_img = cv2.dilate(img.copy(), np.ones((3, 3)), 1)
    eroded_img = cv2.erode(dilated_img, np.ones((3, 3)), 1)
    return eroded_img

if __name__=='__main__':
    img = cv2.imread('img.jpg')
    img = recommend_color(img)
    cv2.imwrite('img1.jpg', img)

