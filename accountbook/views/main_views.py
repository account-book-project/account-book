# accountbook/views/main_views.py

from django.views.generic import TemplateView


class MainPageView(TemplateView):
    template_name = 'main.html'
