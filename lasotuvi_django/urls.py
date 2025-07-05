from django.conf.urls import url

from lasotuvi_django.views import api, lasotuvi_django_index, xuat_text_laso

urlpatterns = [
    url(r'^api', api),
    url(r'^$', lasotuvi_django_index),
    url(r'^xuat-text-laso/$', xuat_text_laso, name='xuat_text_laso'),
]
