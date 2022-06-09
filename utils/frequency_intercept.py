import time
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
MAX_REQUEST_PER_SECOND = 5  # 每秒访问次数


class RequestBlockingMiddleware(MiddlewareMixin):
    def process_request(self, request):

        now = time.time()
        request_queue = request.session.get('request_queue', [])
        if len(request_queue) < MAX_REQUEST_PER_SECOND:
            request_queue.append(now)
            request.session['request_queue'] = request_queue
        else:
            time0 = request_queue[0]
            if (now - time0) < 1:
                time.sleep(5)
            request_queue.append(time.time())
            request.session['request_queue'] = request_queue[1:]


# class OauthProcessMiddleware(MiddlewareMixin):
#     def process_response(self, request, response):
#         """
#         """
#         # 调试模式下,当出现404或500,跳转到指定页面
#         if response.status_code == 404 or response.status_code == 500:
#             return redirect('https://www.9527.click')
