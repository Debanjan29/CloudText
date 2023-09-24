from django.urls import path
from ct import views

urlpatterns = [
    path("",views.save,name="save"),
    path("save/",views.save,name="save"),
    path("get/",views.get,name="get"),
    path("result/",views.get,name="result"),
    path("About/",views.about,name="about"),
]
