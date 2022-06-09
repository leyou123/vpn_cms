# -*- coding=utf-8 -*-
import time, os


class Template(object):
    """html报告"""
    HTML_TMPL = r"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>日志信息</title>
           <style type="text/css" media="screen">
                    #main {
                        position: absolute;
                        width:370px;
                        height:370px;
                        %(style)s
                        margin-left:-200px;
                        margin-top:-100px;
                    }
            </style>
        </head>
        <body style="background-color: black">
        
            <div id="main" style="background-color: white">
                <img src="%(url)s" alt="">
                <p %(p_style)s>Scan the QR code, please</p>
            </div>
        </body>
        </html>"""


def create(url, name):
    """
    生成静态html
    :param url:
    :param name:
    :return:
    """
    try:
        html = Template()
        style = 'left:50%;top:50%;'
        p_style = 'style="color: white;margin-left: 25%"'
        output = html.HTML_TMPL % dict(url=url, style=style, p_style=p_style)
        filename = f'{name}.html'

        root_path = "/root/vpn_cms/media/html"
        file_path = os.path.join(f"{root_path}/", filename)
        with open(file_path, 'wb') as f:
            f.write(output.encode('utf8'))
        return filename
    except Exception as e:
        return False


if __name__ == '__main__':
    # create_html()
    pass

