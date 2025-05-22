from html import escape
from unittest.mock import patch, MagicMock

# Assuming the helpers module is in src.asana.helpers
from src.asana.helpers import asana_comment_from_github_comment
from src.github.models import Comment as GithubComment # For type hinting if needed
from test.impl.mock_dynamodb_test_case import MockDynamoDbTestCase
from test.impl.builders import builder, build
from test.test_utils import magic_mock_with_return_type_value


@patch(
    "src.aws.s3_client.get_asana_domain_user_id_from_github_handle",
    magic_mock_with_return_type_value(
        {"github_test_user_login": "TEST_USER_ASANA_DOMAIN_USER_ID"}
    ),
)
class TestAsanaCommentFromGitHubComment(MockDynamoDbTestCase):
    @classmethod
    def setUpClass(cls):
        MockDynamoDbTestCase.setUpClass()

    def test_includes_comment_text(
        self,
    ):
        github_comment = build(
            builder.comment()
            .author(builder.user("github_unknown_user_login"))
            .body("GITHUB_COMMENT_TEXT")
        )
        asana_comment_html, _ = asana_comment_from_github_comment(github_comment)
        self.assertContainsStrings(asana_comment_html, ["GITHUB_COMMENT_TEXT"])

    def test_transforms_urls_from_comment_tect(
        self,
    ):
        url = "https://www.foo.bar/?a=1&b=2"
        github_comment = build(
            builder.comment()
            .author(builder.user("github_unknown_user_login"))
            .body("Can you refer to the documentation at {}".format(url))
        )
        asana_comment_html, _ = asana_comment_from_github_comment(github_comment)
        self.assertContainsStrings(
            asana_comment_html, ['<a href="{}">{}</a>'.format(escape(url), url)]
        )

    def test_includes_asana_comment_author(
        self,
    ):
        github_comment = build(
            builder.comment().author(builder.user("github_test_user_login"))
        )
        asana_comment_html, _ = asana_comment_from_github_comment(github_comment)
        self.assertContainsStrings(asana_comment_html, ["TEST_USER_ASANA_DOMAIN_USER_ID"])

    def test_handles_non_asana_comment_author_gracefully(
        self,
    ):
        github_comment = build(
            builder.comment().author(
                builder.user("github_unknown_user_login", "GITHUB_UNKNOWN_USER_NAME")
            )
        )
        asana_comment_html, _ = asana_comment_from_github_comment(github_comment)
        self.assertContainsStrings(
            asana_comment_html, ["github_unknown_user_login", "GITHUB_UNKNOWN_USER_NAME"]
        )

    def test_handles_non_asana_comment_author_that_has_no_name_gracefully(
        self,
    ):
        github_comment = build(
            builder.comment().author(builder.user("github_unknown_user_login"))
        )
        asana_comment_html, _ = asana_comment_from_github_comment(github_comment)
        self.assertContainsStrings(asana_comment_html, ["github_unknown_user_login"])

    def test_does_not_inject_unsafe_html(
        self,
    ):
        placeholder = "💣"
        github_placeholder_comment = build(
            builder.comment()
            .author(builder.user("github_unknown_user_login"))
            .body(placeholder)
        )
        asana_placeholder_comment_html, _ = asana_comment_from_github_comment(
            github_placeholder_comment
        )
        unsafe_characters = ["&", "<", ">"]
        for unsafe_character in unsafe_characters:
            github_comment_unsafe = build(
                builder.comment()
                .author(builder.user("github_unknown_user_login"))
                .body(unsafe_character)
            )
            asana_comment_unsafe_html, _ = asana_comment_from_github_comment(github_comment_unsafe)
            # Compare the HTML part only
            unexpected_html = asana_placeholder_comment_html.replace(
                placeholder, unsafe_character
            )
            self.assertNotEqual(
                asana_comment_unsafe_html,
                unexpected_html,
                f"Expected the {unsafe_character} character to be escaped",
            )

    def test_considers_double_quotes_safe_in_comment_text(
        self,
    ):
        github_author = builder.user("github_unknown_user_login")
        placeholder = "💣"
        github_placeholder_comment = build(
            builder.comment().body(placeholder).author(github_author)
        )
        asana_placeholder_comment_html, _ = asana_comment_from_github_comment(
            github_placeholder_comment
        )
        safe_characters = ['"', "'"]
        for safe_character in safe_characters:
            github_comment_safe = build(
                builder.comment().body(safe_character).author(github_author)
            )
            asana_comment_safe_html, _ = asana_comment_from_github_comment(github_comment_safe)
            expected_html = asana_placeholder_comment_html.replace(placeholder, safe_character)
            self.assertEqual(
                asana_comment_safe_html,
                expected_html,
                f"Did not expected the {safe_character} character to be escaped",
            )

    def test_transforms_github_at_mentions_to_asana_at_mentions(
        self,
    ):
        github_comment = build(
            builder.comment()
            .author(builder.user("github_unknown_user_login"))
            .body("@github_test_user_login")
        )
        asana_comment_html, _ = asana_comment_from_github_comment(github_comment)
        self.assertContainsStrings(asana_comment_html, ["TEST_USER_ASANA_DOMAIN_USER_ID"])

    def test_handles_non_asana_comment_at_mention_gracefully(
        self,
    ):
        github_comment = build(
            builder.comment()
            .author(builder.user("github_unknown_user_login"))
            .body("@github_unknown_user_login")
        )
        asana_comment_html, _ = asana_comment_from_github_comment(github_comment)
        self.assertContainsStrings(asana_comment_html, ["@github_unknown_user_login"])

    def test_handles_at_sign_in_comment_gracefully(
        self,
    ):
        github_comment = build(
            builder.comment()
            .author(builder.user("github_unknown_user_login"))
            .body("hello@world.asana.com")
        )
        asana_comment_html, _ = asana_comment_from_github_comment(github_comment)
        self.assertContainsStrings(asana_comment_html, ["hello@world.asana.com"])

    def test_includes_url_in_comment(
        self,
    ):
        url = "https://github.com/Asana/SGTM/pull/31#issuecomment-626850667"
        github_comment = build(builder.comment().url(url))
        asana_comment_html, _ = asana_comment_from_github_comment(github_comment)
        self.assertContainsStrings(asana_comment_html, [f'<A href="{url}">'])

    # New tests for image extraction
    @patch("src.asana.helpers._format_github_text_for_asana")
    def test_no_images_in_comment_body(self, mock_format_text, _): # Mock the s3 client from class decorator
        mock_comment = MagicMock(spec=GithubComment)
        mock_comment.author.return_value = build(builder.user("test_user"))
        mock_comment.url.return_value = "http://comment.url"
        mock_comment.body.return_value = "Comment body without images." # Original body

        # Configure _format_github_text_for_asana mock
        expected_html_from_format = "<p>Processed body without images</p>"
        expected_images_from_format = []
        mock_format_text.return_value = (expected_html_from_format, expected_images_from_format)

        html_body, images_to_attach = asana_comment_from_github_comment(mock_comment)

        self.assertIn(expected_html_from_format, html_body) # Check if the processed body is part of the final HTML
        self.assertEqual(images_to_attach, expected_images_from_format)
        mock_format_text.assert_called_once_with(mock_comment.body())

    @patch("src.asana.helpers._format_github_text_for_asana")
    def test_one_image_in_comment_body(self, mock_format_text, _):
        mock_comment = MagicMock(spec=GithubComment)
        mock_comment.author.return_value = build(builder.user("test_user"))
        mock_comment.url.return_value = "http://comment.url"
        mock_comment.body.return_value = 'Comment with <img src="test.png" alt="alt text">'

        expected_html_from_format = "<p>Processed body with image removed</p>"
        expected_images_from_format = [{"src": "test.png", "alt": "alt text"}]
        mock_format_text.return_value = (expected_html_from_format, expected_images_from_format)

        html_body, images_to_attach = asana_comment_from_github_comment(mock_comment)

        self.assertIn(expected_html_from_format, html_body)
        self.assertEqual(images_to_attach, expected_images_from_format)
        mock_format_text.assert_called_once_with(mock_comment.body())
        # Ensure the original <img> tag is not in the final HTML body
        self.assertNotIn("<img", html_body.lower())


    @patch("src.asana.helpers._format_github_text_for_asana")
    def test_multiple_images_in_comment_body(self, mock_format_text, _):
        mock_comment = MagicMock(spec=GithubComment)
        mock_comment.author.return_value = build(builder.user("test_user"))
        mock_comment.url.return_value = "http://comment.url"
        mock_comment.body.return_value = 'Body <img src="1.gif"> and <img src="2.jpg" alt="2nd">'

        expected_html_from_format = "<p>Processed body, images gone</p>"
        expected_images_from_format = [
            {"src": "1.gif", "alt": "image"}, # Assuming default alt if not provided by _format_github_text_for_asana mock directly
            {"src": "2.jpg", "alt": "2nd"},
        ]
        mock_format_text.return_value = (expected_html_from_format, expected_images_from_format)
        
        html_body, images_to_attach = asana_comment_from_github_comment(mock_comment)

        self.assertIn(expected_html_from_format, html_body)
        self.assertEqual(images_to_attach, expected_images_from_format)
        mock_format_text.assert_called_once_with(mock_comment.body())
        self.assertNotIn("<img", html_body.lower())

if __name__ == "__main__":
    from unittest import main as run_tests

    run_tests()
