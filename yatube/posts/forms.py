"""
Формы создания постов и комментариев.
"""

from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    """
    Форма создания постов.
    """
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': ('Текст поста'),
            'group': ('Группа'),
            'image': ('Изображение'),
        }
        help_texts = {
            'text': ('Текст нового поста'),
            'group': ('Группа, к которой будет относиться пост'),
            'image': ('Изображение к данному посту'),
        }


class CommentForm(forms.ModelForm):
    """
    Форма комментариев.
    """
    class Meta:
        model = Comment
        fields = ('text',)
