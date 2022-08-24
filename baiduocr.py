from aip import AipOcr
import argparse

class OCR():
    def __init__(self, APP_ID='26308104',
                       API_KEY='8i4NskB4txQUDOoGnnnS5y5F',
                       SECRET_KEY='S2zF6EiENBofLDu1qVeo0siDRhPFTvyG'):
        """
        构造函数，建立与百度服务器的连接
        """
        self.__client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

    def recognize_img(self, img_path):
        """
        OCR识别图片
        img_path: 待识别图像存储路径
        return:   识别结果
        """
        img = None
        with open(img_path, 'rb') as fp:
            img = fp.read()
        options = dict()
        options['language_type'] = 'CHN_ENG'
        options['detect_direction'] = 'true'
        options['detect_language'] = 'true'
        res = self.__client.basicAccurate(img, options)
        ret = []
        for result in res['words_result']:
            ret.append(result['words'])
        return '\n'.join(ret)

    def recognize_pdf(self, pdf_path):
        """
        OCR识别pdf
        pdf_path: 待识别图像存储路径
        return:   识别结果
        """
        pdf = None
        with open(pdf_path, 'rb') as fp:
            pdf = fp.read()
        options = dict()
        options['language_type'] = 'CHN_ENG'
        options['detect_direction'] = 'true'
        options['detect_language'] = 'true'
        res = self.__client.basicAccuratePdf(pdf, options)
        ret = []
        for result in res['words_result']:
            ret.append(result['words'])
        return '\n'.join(ret)

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='OCR')
    parser.add_argument('--src', type=str, required=True, help='path of the source image')
    args = parser.parse_args()
    ocr = OCR()
    res = ocr.recognize(args.src)
    print(res)