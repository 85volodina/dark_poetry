from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post


def index(request):
    num_posts = 9
    post_list = Post.objects.select_related("author", "group").all()
    paginator = Paginator(post_list, num_posts)
    groups = Group.objects.all()
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(
        request,
        "index.html",
        {"page": page, "paginator": paginator, "page_number": page_number, "num_posts":num_posts, "groups": groups},
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.select_related("author").all()
    groups = Group.objects.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(
        request,
        "group.html",
        {"page": page, "paginator": paginator, "group": group, "groups": groups},
    )


@login_required
def new_post(request):
    edit = False
    form = PostForm(request.POST or None, files=request.FILES or None)

    if not form.is_valid():
        return render(request, "new.html", {"form": form, "edit": edit})

    post = form.save(commit=False)
    post.author = request.user
    post.save()

    return redirect("index")


def profile(request, username):
    author = get_object_or_404(User, username=username)

    author_posts = author.author_posts.select_related("group").all()
    paginator = Paginator(author_posts, 10)

    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    posts_count = author_posts.count()
    following = False

    if request.user.is_authenticated:
        authors_following = Follow.objects.filter(user=request.user)
        for person in authors_following:
            if person.author == author:
                following = True
    following_count, followers_count= follow_count(username)

    return render(
        request,
        "profile.html",
        {
            "page": page,
            "paginator": paginator,
            "author": author,
            "posts_count": posts_count,
            "following": following,
            "following_count": following_count,
            "followers_count": followers_count,
        },
    )


def post_view(request, username, post_id):

    post = get_object_or_404(Post, pk=post_id)
    posts_count = post.author.author_posts.select_related("group").count()
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    following_count, followers_count= follow_count(username)
    comments_count = str(post.comments.count())


    return render(
        request,
        "post.html",
        {
            "post": post,
            "author": post.author,
            "posts_count": posts_count,
            "form": form,
            "comments": comments,
            "following_count": following_count,
            "followers_count": followers_count,
    
        },
    )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    edit = True

    if post.author != request.user:
        return redirect("post", username=username, post_id=post_id)

    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )

    if not form.is_valid():
        return render(
            request, "new.html", {"form": form, "edit": edit, "post": post}
        )

    post = form.save(commit=False)
    post.author = request.user
    post.save()

    return redirect("post", username=username, post_id=post_id)


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)

    if not form.is_valid():
        return render(
            request, "includes/comments.html", {"form": form, "post": post}
        )

    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    comment.save()

    return redirect("post", username=username, post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    groups = Group.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request, "follow.html", {"page": page, "paginator": paginator, "groups": groups}
    )


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    if not (
        Follow.objects.filter(user=request.user, author=author).exists()
    ) and not (author == request.user):
        follow = Follow.objects.create(user=request.user, author=author)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    follow = get_object_or_404(
        Follow, user=request.user, author=User.objects.get(username=username)
    )
    follow.delete()
    return redirect("profile", username=username)


def follow_count(username):
    following_count = Follow.objects.filter(
        user=User.objects.get(username=username)
    ).count()
    followers_count = Follow.objects.filter(
        author=User.objects.get(username=username)
    ).count()
    return following_count, followers_count

