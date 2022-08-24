from flask import Flask, request, render_template, make_response
from PIL import Image
import numpy as np
import cv2
import os
from random import randint

from scan import Scanner
import cam_filter
from baiduocr import OCR

app=Flask(__name__)
app.config['UPLOADED_PATH'] = os.getcwd() + '/static/img/upload/'

scanner = Scanner(visualize=False)
ocr = OCR()

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    """
    上传界面，且上传的文件也回来这里处理，保存在后端
    """
    if request.method == 'POST':
        for f in request.files.getlist('file'):
            imgpath = os.path.join(app.config['UPLOADED_PATH'], f.filename)
            f.save(imgpath)

            # 以默认的 Scanner.scan 处理图片并保存
            src_path = f'./static/img/upload/{f.filename}'
            dst_path = f'./static/img/corrected/{f.filename}'

            src_img = cv2.imread(src_path)
            if src_img is None:
                raise ValueError(f'Failed to load image {src_path}!')
            dst_img = scanner.scan(src_img)[0]
            dst_img = cam_filter.recommend_bandw(dst_img)
            cv2.imwrite(dst_path, dst_img)
        return ''

    return render_template('index.html')

@app.route('/show', methods=('get', 'post'))
def show():
    """
    展示界面，根据从前端传来的文件名字找到图片，将这些图片返回去前端
    """
    ori_nameList = request.form['picName'] #获得文件对象
    ori_nameList = ori_nameList.strip(' ')
    nameList = str(ori_nameList).split(' ')

    links = ''
    len_nameList = len(nameList)
    for i, name in enumerate(nameList):
        #每五张图片一行，加上<tr>，并在每一行图片上面都加上标号
        if (i%4) == 0:
            links += '<tr>'
            for j in range(4):
                if i+j+1 > len_nameList:
                    break
                links += "<td style='font-size:22px' class='index'>{:0>2d}</td>".format(i+j+1)

            links += '</tr><tr>'
        #把原图和处理好的图都传去前端，不过原图会隐藏起来(class='hide')
        links += f"""
                <td class='image index'>
                    <img src='/static/img/corrected/{name}?t={randint(0,1024)}'  name={name} class='show'>
                    <img src='/static/img/upload/{name}'  name={name} class='hide'>
                </td>"""
        #加上</tr>
        if (i%4)==3: links += '</tr>'

    return render_template('show.html', links=links, ori_nameList=ori_nameList)

@app.route('/submit', methods=['post', ])
def submit():
    """
    用户重新选取原图范围时，按下确认，返回一个字符串
    字符串中包括：文件名，四个点的坐标（顺时针），滤镜名，锐度
    所有内容由空格间隔，因此用split处理一下即可
    """
    res = request.form['res']
    res = res.strip().split(' ')
    filename = res[0]
    quad = np.array([int(i) for i in res[1:9]]).reshape(4, 2).astype(np.float32)
    flitername = res[-2]
    shapen_amount = int(res[-1])


    # 重新处理
    src_path = f'./static/img/upload/{filename}'
    dst_path = f'./static/img/corrected/{filename}'

    src_img = cv2.imread(src_path)
    if src_img is None:
        raise ValueError(f'Failed to load image {src_path}!')

    # 裁剪
    dst_img = None
    if (quad==0).all():
        # 没选，默认原图
        dst_img = src_img.copy()
    else:
        height = src_img.shape[0]
        quad *= (height / 600.0)

        dst_img = scanner.quad_correction(src_img, quad)[0]

    # 锐化
    dst_img = cam_filter.sharpen(dst_img, shapen_amount)
    # 加滤镜
    if flitername=='原图':
        dst_img = cam_filter.original(dst_img)
    elif flitername=='灰度':
        dst_img = cam_filter.grayscale(dst_img)
    elif flitername=='黑白':
        dst_img = cam_filter.black_and_white(dst_img)
    elif flitername=='增亮':
        dst_img = cam_filter.lighten(dst_img)
    elif flitername=='推荐滤镜（黑白）':
        dst_img = cam_filter.recommend_bandw(dst_img)
    elif flitername=='推荐滤镜（彩色）':
        dst_img = cam_filter.recommend_color(dst_img)
    else:
        raise ValueError(f'Flitername {flitername} not found.')
    cv2.imwrite(dst_path, dst_img)

    return ''

@app.route('/pdf', methods=['post', 'get'])
def pdf():
    """
    从前端获取全部图片的名字，然后处理这些图片成pdf
    """
    res=request.args['res'] #空格隔开的所有（图片）文件的名字
    ls=res.split(' ') #将其转换成列表

    img_ls = []
    img1 = Image.open(os.path.join('./static/img/corrected/', ls[0]))
    width1 = img1.size[0]
    for filename in ls[1:]:
        img = Image.open(os.path.join('./static/img/corrected/', filename))
        # 缩放至与第一张图片宽度相同
        oriwidth = img.size[0]
        oriheight = img.size[1]
        width = width1
        height = int(oriheight * (width / oriwidth))
        img = img.resize((width, height))

        if img.mode == 'RGBA':
            img = img.convert('RGB')
            img_ls.append(img)
        else:
            img_ls.append(img)
    img1.save('./static/cache/document.pdf', 'PDF', resolution=100.0, save_all=True, append_images=img_ls)

    download = make_response(app.send_static_file('cache/document.pdf'))
    download.headers["Content-Disposition"] = "attachment; filename=document.pdf;"
    return download

@app.route('/recognition', methods=['post', 'get'])
def recognition():
    """
    从前端获取全部图片的名字，然后对它们文字识别，处理成txt返回回去
    """
    res = request.args['res'] #空格隔开的所有（图片）文件的名字
    ls = res.split(' ') #将其转换成列表

    content = ''
    for page, filename in enumerate(ls):
        content += '第{:0>2d}页：\n'.format(page+1)
        content += ocr.recognize_img(f'./static/img/corrected/{filename}')
        content += '\n\n'
    with open('./static/cache/document.txt', 'w') as f:
        f.write(content)

    download = make_response(app.send_static_file('cache/document.txt'))
    download.headers["Content-Disposition"] = "attachment; filename=document.txt;"
    return download

@app.route('/recognition_one', methods=['post', 'get'])
def recognition_one():
    """
    从前端获取某张图片的名字，然后对其文字识别，处理成txt返回回去
    """
    res = request.args['res'] #图片的名字

    content = ocr.recognize_img(f'./static/img/corrected/{res}')
    with open(f'./static/cache/{res}.txt', 'w') as f:
        f.write(content)
    download = make_response(app.send_static_file(f'cache/{res}.txt'))
    download.headers["Content-Disposition"] = f"attachment; filename={res}.txt;"
    return download

@app.route('/download_img', methods=['post', 'get'])
def download_img():
    """
    从前端获取某张图片的名字，然后返回处理后的该图片
    """
    res = request.args['res'] #图片的名字

    download = make_response(app.send_static_file(f'img/corrected/{res}'))
    download.headers["Content-Disposition"] = f"attachment; filename=corrected_{res};"
    return download

@app.route('/rotate_img', methods=['post', 'get'])
def rotate_img():
    """
    从前端获取某张图片的名字，将处理后的该图片逆时针旋转90度
    """
    res = request.args['res'] #图片的名字

    imgpath = f"./static/img/corrected/{res}"
    img = cv2.imread(imgpath)
    img = np.rot90(img)
    cv2.imwrite(imgpath, img)

    return ''


if __name__=="__main__":
    app.run(port=80, debug=True)