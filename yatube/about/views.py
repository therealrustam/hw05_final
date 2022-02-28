"""
View-классы страниц об авторе и технологии.
"""
from django.views.generic import TemplateView


class AboutAuthorView (TemplateView):
    """
    Класс view страницы об авторе.
    """
    template_name = 'about/author.html'


class AboutTechView (TemplateView):
    """
    Класс view страницы о применяемых технологиях.
    """
    template_name = 'about/tech.html'
