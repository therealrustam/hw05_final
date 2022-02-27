"""
View-функции создания, редактирования
постов, комментариев, подписок и чтения сообществ.
"""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Group, Post, Follow


@cache_page(20, key_prefix='index_page')
def index(request):
    """
    Метод главной страницы, куда выводятся
    последние добавленные посты.
    """
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'index': True,
        'follow': False,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """
    Метод страницы сообщества, куда выводятся
    все посты сообщества.
    """
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, settings.PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """
    Метод страницы профиля автора, куда выводятся
    последние добавленные посты автора.
    """
    author = get_object_or_404(User, username=username)
    following = False
    if request.user.is_authenticated:
        follow_list = Follow.objects.filter(user=request.user, author=author)
        following = follow_list.exists()
    post_list = author.posts.all()
    post_sum = post_list.count()
    paginator = Paginator(post_list, settings.PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'author': author,
        'post_sum': post_sum,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """
    Метод страницы поста, куда выводятся
    все данные, связанные с данным постом.
    """
    post_one = get_object_or_404(Post, id=post_id)
    author_one = post_one.author
    post_list = author_one.posts.all()
    post_sum = post_list.count()
    preview = post_one.text[:30]
    form = CommentForm(request.POST or None)
    comments = post_one.comments.all()
    context = {
        'author_one': author_one,
        'preview': preview,
        'post_one': post_one,
        'post_sum': post_sum,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """
    Метод страницы создания поста, куда
    вводятся все данные.
    """
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            form_for_save = form.save(commit=False)
            form_for_save.author = request.user
            form_for_save.save()
            return redirect('posts:profile', form_for_save.author)
        return render(request, 'posts/create_post.html', {
            'form': form,
        })
    return render(request, 'posts/create_post.html', {
        'form': form,
    })


@login_required
def post_edit(request, post_id):
    """
    Метод страницы редактирования поста, где
    возможно отредактировать данные уже созданного поста.
    """
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    if author != request.user:
        return redirect('posts:post_detail', post_id)
    is_edit = True
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html', {
        'form': form,
        'is_edit': is_edit,
    })


@login_required
def add_comment(request, post_id):
    """
    Метод добавления комментария для
    авторизованного пользователя.
    """
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """
    Метод страницы постов авторов.
    """
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, settings.PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'index': False,
        'follow': True,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """
    Метод подписки на автора.
    """
    author = get_object_or_404(User, username=username)
    if request.user.id != author.id:
        Follow.objects.get_or_create(user=request.user, author=author)
    else:
        return redirect('posts:profile', username)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    """
    Метод отписки от автора.
    """
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user,
                          author=author).delete()
    return redirect('posts:follow_index')
