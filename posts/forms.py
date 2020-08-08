from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ["group", "title", "text", "image"]
        labels = {"text": "Текст", "title": "Заголовок", "group": "Группа", "image": "Изображение"}
        help_texts = {
            "group": ("Выберете группу для добавления записи"),
            "title": ("Введите заголовок"),
            "text": ("Введите текст записи"),
            "image": ("Добавьте изображение"),
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        labels = {"text": "Текст"}
        help_texts = {"text": ("Введите текст комментария")}
