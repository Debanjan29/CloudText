from django.urls import path
from ct import views

urlpatterns = [
    path("",views.save,name="save"),
    path("save/",views.save,name="save"),
    path("get/",views.get,name="get"),
    path("result/",views.get,name="result"),
    path("about/",views.about,name="about"),
    # === 2026 update! ===
    path("download/<str:id>/", views.download_file, name="download_file"),
    # === 2026 update! ===
]
