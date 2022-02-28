"""
View-класс для регистрациии пользователя.
"""
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm


class SignUp(CreateView):
    """
    View-класс для регистрациии
    нового пользователя.
    """
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'
