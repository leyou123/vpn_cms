from django.urls import path,re_path
from apps.orders.views import QueryOrder, GoogleSubscriptions, GoogleNotification
from apps.orders.views import IosSubscriptions, IosOrderNotifications, IosRecoverOrder, OrderCallbackNotifications,SyncSingleOrder,PaypalProducts,ProductsPlan,RadarCallbackNotifications
from apps.orders.views import PalpalProductsPlan,PaypalSubscriptions,PaypalNotification,IosNotifications

urlpatterns = [
    path('query', QueryOrder.as_view(), name="query"),
    path('google_subscriptions', GoogleSubscriptions.as_view(), name="google_subscriptions"),
    path('google_notification', GoogleNotification.as_view(), name="google_notification"),
    path('ios_subscriptions', IosSubscriptions.as_view(), name="ios_subscriptions"),
    path('ios_recover_orders', IosRecoverOrder.as_view(), name="ios_recover_orders"),

    # path('ios_order_notifications', IosOrderNotifications.as_view(), name="ios_order_notifications"),
    # path('orders_callback_notifications', OrderCallbackNotifications.as_view(), name="orders_callback_notifications"),
    # path('radar_callback_notifications', RadarCallbackNotifications.as_view(), name="radar_callback_notifications"),

    # path('iosNotifications', IosNotifications.as_view(), name="sync_single_order"),

    # paypal 支付
    path('paypal_products', PaypalProducts.as_view(), name="paypal_products"),
    path('products_plan', ProductsPlan.as_view(), name="products_plan"),
    path('create_products_plan', PalpalProductsPlan.as_view(), name="create_products_plan"),
    path('paypal_subscriptions', PaypalSubscriptions.as_view(), name="paypal_subscriptions"),
    path('paypal_notifications', PaypalNotification.as_view(), name="paypal_notifications"),

    re_path(r'^.*$', IosNotifications.as_view(), name="radar_callback_notifications"),

]
