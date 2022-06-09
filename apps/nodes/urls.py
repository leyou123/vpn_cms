from django.urls import path
from apps.nodes.views import Node, Register, CountryNode

urlpatterns = [
    path('all', Node.as_view(), name="nodes"),
    path('register', Register.as_view(), name="register"),
    path('country', CountryNode.as_view(), name="country_node"),

]
