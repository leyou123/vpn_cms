from django.urls import path
from apps.report.views import PingUpdate, ConnectUpdate, ConnectView, PingFeedbackView, Countryrate, Noderate, Userrate
from apps.report.views import NodeHead, CheckAllNode, TestResultView, NodeBlackView, DelRepoet

urlpatterns = [
    path('connect', ConnectView.as_view(), name="connect"),
    path('ping', PingFeedbackView.as_view(), name="ping"),
    path('ping_update', PingUpdate.as_view(), name="ping_update"),
    path('connect_update', ConnectUpdate.as_view(), name="connect_update"),

    path('country_rate', Countryrate.as_view(), name="country_rate"),
    path('node_rate', Noderate.as_view(), name="node_rate"),
    path('user_rate', Userrate.as_view(), name="user_rate"),
    path('node_head', NodeHead.as_view(), name="node_head"),
    # path('node_black', NodeBlackView.as_view(), name="node_black"),


    path('check_all_node', CheckAllNode.as_view(), name="check_all_node"),
    path('test_result', TestResultView.as_view(), name="test_result"),
    path('del_report', DelRepoet.as_view(), name="del_report"),

]
