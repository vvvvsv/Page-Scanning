from matplotlib.pyplot import sca
import numpy as np
import cv2
from scipy.spatial import distance

import argparse

class Scanner():
    def __init__(self, visualize=False):
        """
        构造函数
        visualize: True or False, 是否显示文档四边形、扫描结果
        """
        self.visualize = visualize

    def resize(self, image, width=None, height=None):
        """
        图像放缩
        image:  原图像
        width:  新图像宽度
        height: 新图像高度
            若 width 和 height 都不为 None，则使用 width
        return: 新图像, scale
        """
        if width is None and height is None:
            raise ValueError('Scanner.resize: width is None and height is None!')
        size = None
        scale = None
        (h, w) = image.shape[:2]

        if width is None:
            scale = height / float(h)
            size = (int(w * scale), height)
        else:
            scale = width / float(w)
            size = (width, int(h * scale))
        return cv2.resize(image.copy(), size, interpolation=cv2.INTER_AREA), scale

    def __canny_edge(self, ori_img, channels=1, kernel_size=(5,5)):
        """
        使用简单的canny计算图片边缘
        ori_img:     原图片
        channels:    原图片通道数
        kernel_size: 高斯模糊和膨胀的核大小，长宽都为奇数
        return:      图片边缘
        """
        edge_sum = np.zeros(ori_img.shape[:2], dtype=np.uint16)
        for channel in range(channels):
            # 对各个通道计算canny并求和
            img = ori_img[:, :, channel]
            img = cv2.GaussianBlur(img, kernel_size, 0)
            edge = cv2.Canny(img, 30, 120)
            edge_sum += edge
        edge_sum = np.where(edge_sum>255, 255, edge_sum)
        # 膨胀计算
        edge_sum = cv2.dilate(edge_sum, np.ones(kernel_size), 1)
        return edge_sum.astype(np.uint8)

    def __enhence_edge(self, ori_edge):
        """
        使用hough算法加强图片边缘中的直线部分
        ori_edge: 原始图片边缘
        return:   加强后的图片边缘
        """
        edge = ori_edge.copy()
        # 找到原边缘中足够长的直线段
        lines = cv2.HoughLinesP(edge, 1, np.pi/360, 100, minLineLength=200, maxLineGap=5)
        # 将直线段加粗并绘制在边缘中以加强边缘
        if lines is None:
            lines = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(edge, (x1, y1), (x2, y2), (255, ), 2)
        return edge

    def __find_quad_from_edge(self, edge):
        """
        从图片边缘中寻找最大的四边形
        edge:   图片边缘
        return: 四边形顶点坐标, 面积
        """
        # 从图片边缘提取闭合轮廓
        contours, hierarchy = cv2.findContours(edge, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        # 按轮廓包含面积从大到小排序
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        for c in contours:
            # 计算周长
            length = cv2.arcLength(c, True)
            # 用多边形拟合
            quad = cv2.approxPolyDP(c, 0.01 * length, True)
            # 如果是四边形
            if quad.shape[0]==4:
                return quad, cv2.contourArea(c)
        return None, 0

    def __find_doc_quad(self, ori_img):
        """
        寻找文档四边形
        ori_img: 原始图片
        return:  四边形顶点坐标
        """
        # 缩小图片
        img, scale = self.resize(ori_img.copy(), height=500)
        # 尝试不同的膨胀和高斯模糊的核大小
        for length in [5, 7, 3, 9]:
            # 计算初始图片边缘
            edge = self.__canny_edge(img.copy(), channels=img.shape[2], kernel_size=(length, length))
            # 加强图片边缘直到能找到一个面积大于等于整张图1/3的四边形
            quad = None
            for _ in range(10):
                quad, area = self.__find_quad_from_edge(edge)
                if(area*3 > img.shape[0]*img.shape[1]):
                    # 找到符合要求的四边形
                    if(self.visualize):
                        draw_img = cv2.drawContours(img.copy(), [quad], -1, (0, 0, 255), 1)
                        cv2.imshow('Document quadrilateral', draw_img)
                        cv2.waitKey(0)
                    return (quad.reshape(4, 2) / scale).astype(np.float32)
                edge = self.__enhence_edge(edge)

        # Document quadrilateral not found
        height, width = ori_img.shape[:2]
        quad = np.array([[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]])
        quad = quad.reshape(4, 1, 2)
        if(self.visualize):
            draw_img = cv2.drawContours(img.copy(), [(quad * scale).astype(np.int32)], -1, (0, 0, 255), 1)
            cv2.imshow('Document quadrilateral', draw_img)
            cv2.waitKey(0)
        return quad.reshape(4, 2).astype(np.float32)

    def __order_points(self, quad):
        """
        重新排列四边形顶点，按左上、右上、左下、右下排好顺序
        quad:   四边形中以顺时针或逆时针排列的四个顶点坐标
        return: 重新排列后的顶点坐标
        """
        top_left = np.argmin(quad.sum(axis=1))
        top_right = None
        bottom_right = None
        bottom_left = None
        next_pt = (top_left+1)%4
        diff = quad[next_pt] - quad[top_left]
        if diff[0]>diff[1]:
            # next_pt 为右上角，顺时针
            top_right = next_pt
            bottom_right = (top_right+1)%4
            bottom_left = (bottom_right+1)%4
        else:
            # next_pt 为左下角，逆时针
            bottom_left = next_pt
            bottom_right = (bottom_left+1)%4
            top_right = (bottom_right+1)%4
        return quad[[top_left, top_right, bottom_left, bottom_right]]

    def quad_correction(self, img, quad):
        """
        四边形校正（透视变换）
        Zhang, Zhengyou and He, Li-wei, Whiteboard Scanning and Image Enhancement,
        Digital Signal Processing, 2007 April, 414-432
        假定拍摄环境为一个针孔相机模型，在透视投影下，一个矩形被拍摄成一个四边形。根据该
        四边形的形状，可以求解焦距，然后得到原矩形的纵横比。
        img:    原始图片
        quad:   四边形顶点坐标
        return: 四边形校正并裁剪后的图片, 四边形顶点坐标（按左上、右上、左下、右下排好顺序）
        """

        try:
            # 原始图片中的中心点
            rows, cols = img.shape[:2]
            u0 = (cols)/2.0
            v0 = (rows)/2.0

            # 四边形四个顶点坐标
            p = self.__order_points(quad)

            # 投影图像的宽度和高度
            w1 = distance.euclidean(p[0], p[1])
            w2 = distance.euclidean(p[2], p[3])

            h1 = distance.euclidean(p[0], p[2])
            h2 = distance.euclidean(p[1], p[3])

            w = max(w1, w2)
            h = max(h1, h2)

            # 投影图像的原始纵横比
            ar_vis = float(w)/float(h)

            # 取出顶点并在后面补上1（齐次坐标）
            m1,m2,m3,m4 = np.hstack((p,np.ones((4,1)))).astype(np.float32)

            # 计算焦距偏差
            k2 = np.dot(np.cross(m1, m4), m3) / np.dot(np.cross(m2, m4), m3)
            k3 = np.dot(np.cross(m1, m4), m2) / np.dot(np.cross(m3, m4), m2)

            n2 = k2 * m2 - m1
            n3 = k3 * m3 - m1

            n21 = n2[0]
            n22 = n2[1]
            n23 = n2[2]

            n31 = n3[0]
            n32 = n3[1]
            n33 = n3[2]

            f = np.sqrt(np.abs( (1.0/(n23*n33)) * ((n21*n31 - (n21*n33 + n23*n31)*u0 + n23*n33*u0*u0) + (n22*n32 - (n22*n33+n23*n32)*v0 + n23*n33*v0*v0))))

            A = np.array([[f, 0, u0], [0, f, v0], [0, 0, 1]]).astype(np.float32)

            At = np.transpose(A)
            Ati = np.linalg.inv(At)
            Ai = np.linalg.inv(A)

            # 计算实际纵横比
            ar_real = np.sqrt(np.dot(np.dot(np.dot(n2, Ati), Ai), n2) / np.dot(np.dot(np.dot(n3, Ati), Ai), n3))

            if ar_real < ar_vis:
                W = int(w)
                H = int(W / ar_real)
            else:
                H = int(h)
                W = int(ar_real * H)

            pts1 = p.astype(np.float32)
            pts2 = np.float32([[0, 0], [W-1, 0], [0, H-1], [W-1, H-1]])

            # 用实际纵横比重新投影图像
            M = cv2.getPerspectiveTransform(pts1, pts2)
            warped = cv2.warpPerspective(img.copy(), M, (W, H))
            return warped, p

        except Exception:
            # 若出现问题则用普通方法裁剪
            p = self.__order_points(quad)
            tl = p[0]
            tr = p[1]
            bl = p[2]
            br = p[3]

            w1 = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
            w2 = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
            W = max(int(w1), int(w2))
            h1 = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
            h2 = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
            H = max(int(h1), int(h2))

            pts1 = p.astype(np.float32)
            pts2 = np.float32([[0, 0], [W-1, 0], [0, H-1], [W-1, H-1]])

            M = cv2.getPerspectiveTransform(pts1, pts2)
            warped = cv2.warpPerspective(img.copy(), M, (W, H))
            return warped, p

    def scan(self, img):
        """
        扫描图片，寻找文档四边形，裁剪图片并返回
        img:    原始图片
        return: 四边形校正并裁剪后的图片, 四边形顶点坐标（按左上、右上、左下、右下排好顺序）
        """
        quad = self.__find_doc_quad(img.copy())

        corrected_img, points = self.quad_correction(img.copy(), quad)
        if(self.visualize):
            cv2.imshow('Scanned image', self.resize(corrected_img.copy(), height=1000)[0])
            cv2.waitKey(0)
        return corrected_img, points

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scan out a document page from a picture')
    parser.add_argument('--src', type=str, required=True, help='path of the source image')
    parser.add_argument('--dst', type=str, default='dst.jpg', help='path to storage scanned image')
    parser.add_argument('-v', '--visualize', action='store_true', help='display document quadrilateral and scanned image')
    args = parser.parse_args()

    scanner = None
    if args.visualize:
        scanner = Scanner(visualize=True)
    else:
        scanner = Scanner(visualize=False)
    src_img = cv2.imread(args.src)
    if src_img is None:
        raise ValueError('Failed to load image!')
    dst_img = scanner.scan(src_img)[0]
    cv2.imwrite(args.dst, dst_img)