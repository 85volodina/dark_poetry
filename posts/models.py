from django.contrib.auth.models import User
from django.db import models


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    title = models.CharField(max_length=200 ,
        blank=True,
        null=True,)
    text = models.TextField()
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="author_posts"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="group_posts",
        blank=True,
        null=True,
    )
    image = models.ImageField(upload_to="posts/", blank=True, null=True)

    class Meta:
        ordering = ["-pub_date"]

    def __str__(self):
        return self.text


class Comment(models.Model):

    text = models.TextField()
    created = models.DateTimeField("date published", auto_now_add=True)
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments"
    )

    class Meta:
        ordering = ["-created"]


def __str__(self):
    return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="follower"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following"
    )

    class Meta:
        unique_together = ("user", "author")
