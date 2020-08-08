from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Follow, Group, Post, User

DUMMY_CACHE = {
    "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
}


class PostAppTest(TestCase):
    def setUp(self):
        self.client_auth = Client()
        self.client_not_auth = Client()
        self.group = Group.objects.create(
            title="cat", slug="cat", description="test with group"
        )
        self.group_new = Group.objects.create(
            title="kitten", slug="kitten", description="group change"
        )
        self.user = User.objects.create_user(
            username="kotik", email="mrrr@gmail.com", password="12345"
        )
        self.user_to_follow = User.objects.create_user(
            username="pesik", email="gav@gmail.com", password="12345"
        )
        self.user_not_to_follow = User.objects.create_user(
            username="zlo", email="zlo@gmail.com", password="12345"
        )
        self.post_invisible = Post.objects.create(
            text="This shouldn't appear",
            author=self.user_not_to_follow,
            group=self.group,
        )
        self.post_visible = Post.objects.create(
            text="This should appear!",
            author=self.user_to_follow,
            group=self.group,
        )

        self.client_auth.force_login(self.user)
        self.post_text = "Mrrrrrrrr"
        self.post_text_new = "Mew"
        self.post = Post.objects.create(
            text=self.post_text, author=self.user, group=self.group
        )
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04"
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )
        self.wrong_img = SimpleUploadedFile("omg.txt", b"something")
        self.img = SimpleUploadedFile(
            "small.gif", small_gif, content_type="image/gif"
        )
        self.img_new = SimpleUploadedFile(
            "new.gif", small_gif, content_type="image/gif"
        )
        self.login = reverse("login")
        self.new = reverse("new_post")

    @override_settings(CACHES=DUMMY_CACHE)
    def _check_contains(self, text_check, group_slug, post_id):
        for url in [
            "/",
            f"/{self.user.username}/",
            f"/{self.user.username}/{post_id}/",
            f"/group/{group_slug}/",
        ]:
            response = self.client_not_auth.get(url)
            self.assertContains(response, text_check, status_code=200)

    def _check_context(self, fields, values):
        check_list = list(zip(fields, values))
        for item in check_list:
            self.assertEqual(item[0], item[1])

    def test_pub_deny(self):
        response = self.client_not_auth.get(reverse("new_post"), follow=True)
        self.assertRedirects(
            response,
            f"{self.login}?next={self.new}",
            status_code=302,
            target_status_code=200,
        )

    def test_new_post(self):
        response = self.client_auth.post(
            reverse("new_post"),
            {"group": self.group.id, "text": self.post_text, "edit": False},
            follow=True,
        )
        post_id = Post.objects.latest("pk").pk
        self._check_contains(self.post_text, self.group.slug, post_id)
        self.assertEqual(Post.objects.get(pk=post_id).text, self.post_text)

    @override_settings(CACHES=DUMMY_CACHE)
    def test_image(self):
        response = self.client_auth.post(
            reverse("new_post"),
            {
                "group": self.group.id,
                "text": "Новый пост с картинкой",
                "image": self.img,
                "edit": False,
            },
            follow=True,
        )
        post_id = Post.objects.latest("pk").pk
        posted_image = response.context["paginator"].object_list[0].image

        for url in [
            "/",
            f"/{self.user.username}/",
            f"/group/{self.group.slug}/",
        ]:
            response = self.client_not_auth.get(url)
            returned_image = response.context["paginator"].object_list[0].image
            self.assertEqual(posted_image, returned_image)

        response = self.client_not_auth.get(
            f"/{self.user.username}/{post_id}/"
        )
        returned_image = response.context["post"].image
        self.assertEqual(posted_image, returned_image)
        self._check_contains("<img", self.group.slug, post_id)
        self.assertIsNotNone(Post.objects.latest("pk").image)

    def test_wrong_image(self):
        response = self.client_auth.post(
            reverse("new_post"),
            {
                "group": self.group.id,
                "text": "Попытка загрузить неподдерживаемый формат",
                "image": self.wrong_img,
                "edit": False,
            },
            follow=True,
        )
        self.assertFormError(
            response,
            "form",
            "image",
            "Загрузите правильное изображение. "
            "Файл, который вы загрузили, поврежден"
            " или не является изображением.",
        )

    def test_edit_post(self):
        response = self.client_auth.post(
            reverse("new_post"),
            {
                "group": self.group.id,
                "text": self.post_text,
                "image": self.img,
                "edit": False,
            },
            follow=True,
        )
        post_id = Post.objects.latest("pk").pk
        response = self.client_auth.get(
            reverse("post_edit", args=[self.user.username, post_id])
        )

        self.assertEqual(response.status_code, 200)
        response = self.client_auth.post(
            reverse("post_edit", args=[self.user.username, post_id]),
            {
                "group": self.group_new.id,
                "text": self.post_text_new,
                "image": self.img_new,
                "edit": True,
            },
            follow=True,
        )
        posted_image = response.context["post"].image
        post = Post.objects.get(pk=post_id)
        self._check_contains(self.post_text_new, self.group_new.slug, post_id)
        self._check_context(
            [post.text, post.group, post.image],
            [self.post_text_new, self.group_new, posted_image],
        )

    def test_pub_allow(self):
        response = self.client_auth.get(reverse("new_post"), follow=True)
        self.assertEqual(response.status_code, 200)

    def page_not_found_test(self):
        response = self.client_not_auth.get("/unexistedpage/")
        self.assertEqual(response.status_code, 404)

    def test_cache(self):
        response = self.client_not_auth.get(reverse("index"))
        new_post = Post.objects.create(
            text="Something new", author=self.user, group=self.group
        )
        response = self.client_not_auth.get(reverse("index"))
        self.assertNotIn(new_post.text, response.content.decode())

    def test_follow(self):
        response = self.client_auth.post(
            reverse("profile_follow", args=[self.user_to_follow]),
            {},
            follow=True,
        )
        response = self.client_auth.get(
            reverse("profile", args=[self.user_to_follow])
        )
        self.assertEqual(response.context["following"], True)
        self.assertNotEqual(response.context["followers_count"], 0)
        response = self.client_auth.get(reverse("profile", args=[self.user]))
        self.assertNotEqual(response.context["following_count"], 0)
        self.assertEqual(
            Follow.objects.get(user=self.user).author, self.user_to_follow
        )

    def test_following(self):
        response = self.client_auth.post(
            reverse("profile_follow", args=[self.user_to_follow]),
            {},
            follow=True,
        )

        response = self.client_auth.get(reverse("follow_index"))
        post_text = response.context["paginator"].object_list[0].text
        self.assertEqual(post_text, self.post_visible.text)
        self.assertNotEqual(post_text, self.post_invisible.text)

    def test_comment_auth(self):
        response = self.client_auth.post(
            reverse(
                "add_comment", args=[self.user_to_follow, self.post_visible.pk]
            ),
            {"text": "New comment"},
            follow=True,
        )
        response = self.client_auth.get(
            reverse("post", args=[self.user_to_follow, self.post_visible.pk])
        )
        self.assertEqual(response.context["comments"][0].text, "New comment")
        response = self.client_not_auth.post(
            reverse(
                "add_comment", args=[self.user_to_follow, self.post_visible.pk]
            ),
            {"text": "Invisible comment"},
            follow=True,
        )

        redirect_comment = reverse(
            "add_comment", args=[self.user_to_follow, self.post_visible.pk]
        )
        self.assertRedirects(
            response,
            f"{self.login}?next={redirect_comment}",
            status_code=302,
            target_status_code=200,
        )
        response = self.client_not_auth.get(
            reverse("post", args=[self.user_to_follow, self.post_visible.pk])
        )
        self.assertNotEqual(
            response.context["comments"][0].text, "Invisible comment"
        )
