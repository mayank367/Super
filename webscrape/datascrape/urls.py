from django.urls import path
from .views import search_view, download_excel

urlpatterns = [
    path('', search_view, name='search'),
    path('download/', download_excel, name='download_excel'),
]
