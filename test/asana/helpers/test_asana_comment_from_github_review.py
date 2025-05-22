from unittest.mock import patch, MagicMock

import src.asana.helpers as asana_helpers
from src.github.models import ReviewState, Review as GithubReview, Comment as GithubComment
from test.impl.builders import builder, build
from test.impl.mock_dynamodb_test_case import MockDynamoDbTestCase
from test.test_utils import magic_mock_with_return_type_value

"""
    Extracts the GitHub author and comments from a GitHub Review, and transforms them into
    a suitable html comment string for Asana. This will involve looking up the GitHub author in
    DynamoDb to determine the Asana domain user id of the review author and any @mentioned GitHub
    users.
"""


@patch(
    "src.aws.s3_client.get_asana_domain_user_id_from_github_handle",
    magic_mock_with_return_type_value(
        {"github_test_user_login": "TEST_USER_ASANA_DOMAIN_USER_ID"}
    ),
)
class TestAsanaCommentFromGitHubReview(MockDynamoDbTestCase):
    @classmethod
    def setUpClass(cls):
        MockDynamoDbTestCase.setUpClass()

    def test_includes_review_text(self):
        github_review = build(
            builder.review()
            .author(builder.user("github_unknown_user_login"))
            .state(ReviewState.DEFAULT)
            .body("GITHUB_REVIEW_TEXT")
            .comment(builder.comment().body("GITHUB_REVIEW_COMMENT_TEXT"))
        )
        asana_review_comment_html, _ = asana_helpers.asana_comment_from_github_review(
            github_review
        )
        self.assertContainsStrings(
            asana_review_comment_html, ["GITHUB_REVIEW_TEXT", "GITHUB_REVIEW_COMMENT_TEXT"]
        )

    def test_converts_urls_to_links(self):
        github_review = build(
            builder.review()
            .author(builder.user("github_unknown_user_login"))
            .state(ReviewState.DEFAULT)
            .body("https://www.asana.com")
            .comment(builder.comment().body("http://www.foo.com"))
        )
        asana_review_comment_html, _ = asana_helpers.asana_comment_from_github_review(
            github_review
        )
        self.assertContainsStrings(
            asana_review_comment_html,
            [
                '<a href="{}">{}</a>'.format(url, url)
                for url in ["https://www.asana.com", "http://www.foo.com"]
            ],
        )

    def test_handles_no_review_text(self):
        github_review = build(
            builder.review()
            .author(builder.user("github_unknown_user_login"))
            .state(ReviewState.APPROVED)
            .body("")
            .comment(builder.comment().body("GITHUB_REVIEW_COMMENT_TEXT"))
        )
        asana_review_comment_html, _ = asana_helpers.asana_comment_from_github_review(
            github_review
        )
        self.assertContainsStrings(
            asana_review_comment_html,
            [
                "GitHub user 'github_unknown_user_login'",
                "approved",
                "and left inline comments:",
                "GITHUB_REVIEW_COMMENT_TEXT",
            ],
        )

    def test_includes_asana_review_comment_author(self):
        github_review = build(
            builder.review()
            .author(builder.user("github_test_user_login"))
            .state(ReviewState.DEFAULT)
        )
        asana_review_comment_html, _ = asana_helpers.asana_comment_from_github_review(
            github_review
        )
        self.assertContainsStrings(
            asana_review_comment_html, ["TEST_USER_ASANA_DOMAIN_USER_ID"]
        )

    def test_handles_non_asana_review_comment_author_gracefully(self):
        github_review = build(
            builder.review()
            .author(
                builder.user("github_unknown_user_login", "GITHUB_UNKNOWN_USER_NAME")
            )
            .state(ReviewState.DEFAULT)
        )
        asana_review_comment_html, _ = asana_helpers.asana_comment_from_github_review(
            github_review
        )
        self.assertContainsStrings(
            asana_review_comment_html,
            ["github_unknown_user_login", "GITHUB_UNKNOWN_USER_NAME"],
        )

    def test_handles_non_asana_review_comment_author_that_has_no_name_gracefully(self):
        github_review = build(
            builder.review()
            .author(builder.user("github_unknown_user_login"))
            .state(ReviewState.DEFAULT)
        )
        asana_review_comment_html, _ = asana_helpers.asana_comment_from_github_review(
            github_review
        )
        self.assertContainsStrings(
            asana_review_comment_html, ["github_unknown_user_login"]
        )

    def test_does_not_inject_unsafe_html(self):
        placeholder = "💣"
        github_placeholder_review = build(
            builder.review()
            .author(builder.user("github_unknown_user_login"))
            .state(ReviewState.DEFAULT)
            .body(placeholder)
            .comment(builder.comment().body(placeholder))
        )
        asana_placeholder_review_html, _ = asana_helpers.asana_comment_from_github_review(
            github_placeholder_review
        )
        unsafe_characters = ["&", "<", ">"]
        for unsafe_character in unsafe_characters:
            github_review_unsafe = build(
                builder.review()
                .author(builder.user("github_unknown_user_login"))
                .state(ReviewState.DEFAULT)
                .body(unsafe_character)
                .comment(builder.comment().body(unsafe_character))
            )
            asana_review_comment_unsafe_html, _ = (
                asana_helpers.asana_comment_from_github_review(github_review_unsafe)
            )
            unexpected_html = asana_placeholder_review_html.replace(placeholder, unsafe_character)
            self.assertNotEqual(
                asana_review_comment_unsafe_html,
                unexpected_html,
                f"Expected the {unsafe_character} character to be escaped",
            )

    def test_considers_double_quotes_safe_in_review_text(self):
        placeholder = "💣"
        github_placeholder_review = build(
            builder.review()
            .author(builder.user("github_unknown_user_login"))
            .state(ReviewState.DEFAULT)
            .body(placeholder)
            .comment(builder.comment().body(placeholder))
        )
        asana_placeholder_review_html, _ = asana_helpers.asana_comment_from_github_review(
            github_placeholder_review
        )
        safe_characters = ['"', "'"]
        for safe_character in safe_characters:
            github_review_safe = build(
                builder.review()
                .author(builder.user("github_unknown_user_login"))
                .state(ReviewState.DEFAULT)
                .body(safe_character)
                .comment(builder.comment().body(safe_character))
            )
            asana_review_comment_safe_html, _ = asana_helpers.asana_comment_from_github_review(
                github_review_safe
            )
            expected_html = asana_placeholder_review_html.replace(placeholder, safe_character)
            self.assertEqual(
                asana_review_comment_safe_html,
                expected_html,
                f"Did not expected the {safe_character} character to be escaped",
            )

    def test_transforms_github_at_mentions_to_asana_at_mentions(self):
        github_review = build(
            builder.review()
            .author(builder.user("github_unknown_user_login"))
            .state(ReviewState.DEFAULT)
            .body("@github_test_user_login")
        )
        asana_review_comment_html, _ = asana_helpers.asana_comment_from_github_review(
            github_review
        )
        self.assertContainsStrings(
            asana_review_comment_html, ["TEST_USER_ASANA_DOMAIN_USER_ID"]
        )

    def test_handles_non_asana_comment_at_mention_gracefully(self):
        github_review = build(
            builder.review()
            .author(builder.user("github_unknown_user_login"))
            .state(ReviewState.DEFAULT)
            .body("@github_unknown_user_login")
        )
        asana_review_comment_html, _ = asana_helpers.asana_comment_from_github_review(
            github_review
        )
        self.assertContainsStrings(asana_review_comment_html, ["@github_unknown_user_login"])

    def test_handles_at_sign_in_review_gracefully(self):
        github_review = build(
            builder.review()
            .author(builder.user("github_unknown_user_login"))
            .state(ReviewState.DEFAULT)
            .body("hello@world.asana.com")
        )
        asana_review_comment_html, _ = asana_helpers.asana_comment_from_github_review(
            github_review
        )
        self.assertContainsStrings(asana_review_comment_html, ["hello@world.asana.com"])

    def test_includes_link_to_comment(self):
        url = "https://github.com/Asana/SGTM/pull/31#issuecomment-626850667"
        github_review = build(
            builder.review()
            .state(ReviewState.DEFAULT)
            .comment(builder.comment().url(url))
        )
        asana_review_comment_html, _ = asana_helpers.asana_comment_from_github_review(
            github_review
        )
        self.assertContainsStrings(asana_review_comment_html, [f'<A href="{url}">'])

    def test_includes_link_to_review(self):
        url = "https://github.com/Asana/SGTM/pull/31#issuecomment-626850667"
        github_review = build(builder.review().state(ReviewState.DEFAULT).url(url))
        asana_review_comment_html, _ = asana_helpers.asana_comment_from_github_review(
            github_review
        )
        self.assertContainsStrings(asana_review_comment_html, [f'<A href="{url}">'])

    # New tests for image extraction in reviews
    @patch("src.asana.helpers._format_github_text_for_asana")
    def test_review_no_images(self, mock_format_text, _): # Mock s3_client from class decorator
        mock_review = MagicMock(spec=GithubReview)
        mock_review.author.return_value = build(builder.user("review_user"))
        mock_review.url.return_value = "http://review.url"
        mock_review.body.return_value = "Review body text."
        mock_review.comments.return_value = [] # No inline comments
        mock_review.is_just_comments.return_value = False


        # Mock _format_github_text_for_asana for the main body
        mock_format_text.return_value = ("<p>Processed review body</p>", [])

        html_body, images_to_attach = asana_helpers.asana_comment_from_github_review(mock_review)

        self.assertIn("<p>Processed review body</p>", html_body)
        self.assertEqual(images_to_attach, [])
        mock_format_text.assert_called_once_with("Review body text.")
        self.assertNotIn("<img", html_body.lower())


    @patch("src.asana.helpers._format_github_text_for_asana")
    def test_review_images_in_main_body_only(self, mock_format_text, _):
        mock_review = MagicMock(spec=GithubReview)
        mock_review.author.return_value = build(builder.user("review_user"))
        mock_review.url.return_value = "http://review.url"
        mock_review.body.return_value = 'Review body with <img src="body_img.png" alt="Body Img">'
        mock_review.comments.return_value = []
        mock_review.is_just_comments.return_value = False

        expected_body_html = "<p>Processed body</p>"
        expected_body_images = [{"src": "body_img.png", "alt": "Body Img"}]
        mock_format_text.return_value = (expected_body_html, expected_body_images)

        html_body, images_to_attach = asana_helpers.asana_comment_from_github_review(mock_review)

        self.assertIn(expected_body_html, html_body)
        self.assertEqual(images_to_attach, expected_body_images)
        mock_format_text.assert_called_once_with(mock_review.body())
        self.assertNotIn("<img", html_body.lower())

    @patch("src.asana.helpers._format_github_text_for_asana")
    def test_review_images_in_inline_comments_only(self, mock_format_text, _):
        mock_review = MagicMock(spec=GithubReview)
        mock_review.author.return_value = build(builder.user("review_user"))
        mock_review.url.return_value = "http://review.url"
        mock_review.body.return_value = "Review body text, no images here." # Main body
        mock_review.is_just_comments.return_value = False

        # Inline comments
        mock_comment1 = MagicMock(spec=GithubComment)
        mock_comment1.body.return_value = 'Inline comment 1 <img src="inline1.jpg" alt="Inline 1">'
        mock_comment1.url.return_value = "http://comment1.url"
        
        mock_comment2 = MagicMock(spec=GithubComment)
        mock_comment2.body.return_value = 'Inline comment 2 <img src="inline2.gif" alt="Inline 2">'
        mock_comment2.url.return_value = "http://comment2.url"
        mock_review.comments.return_value = [mock_comment1, mock_comment2]

        # Define behavior of _format_github_text_for_asana for each call
        # Call 1 (main body)
        main_body_processed_html = "<p>Processed main body</p>"
        # Call 2 (inline comment 1)
        inline_comment1_processed_html = "Processed inline 1"
        inline_comment1_images = [{"src": "inline1.jpg", "alt": "Inline 1"}]
        # Call 3 (inline comment 2)
        inline_comment2_processed_html = "Processed inline 2"
        inline_comment2_images = [{"src": "inline2.gif", "alt": "Inline 2"}]

        mock_format_text.side_effect = [
            (main_body_processed_html, []), # For main review body
            (inline_comment1_processed_html, inline_comment1_images), # For mock_comment1
            (inline_comment2_processed_html, inline_comment2_images), # For mock_comment2
        ]

        html_body, images_to_attach = asana_helpers.asana_comment_from_github_review(mock_review)

        self.assertIn(main_body_processed_html, html_body)
        self.assertIn(inline_comment1_processed_html, html_body)
        self.assertIn(inline_comment2_processed_html, html_body)
        self.assertEqual(images_to_attach, inline_comment1_images + inline_comment2_images)
        
        self.assertEqual(mock_format_text.call_count, 3)
        mock_format_text.assert_any_call(mock_review.body())
        mock_format_text.assert_any_call(mock_comment1.body())
        mock_format_text.assert_any_call(mock_comment2.body())
        self.assertNotIn("<img", html_body.lower())

    @patch("src.asana.helpers._format_github_text_for_asana")
    def test_review_images_in_both_main_and_inline(self, mock_format_text, _):
        mock_review = MagicMock(spec=GithubReview)
        mock_review.author.return_value = build(builder.user("review_user"))
        mock_review.url.return_value = "http://review.url"
        mock_review.body.return_value = 'Main body <img src="main.png" alt="Main">'
        mock_review.is_just_comments.return_value = False

        mock_comment = MagicMock(spec=GithubComment)
        mock_comment.body.return_value = 'Inline <img src="inline.jpg" alt="Inline">'
        mock_comment.url.return_value = "http://comment.url"
        mock_review.comments.return_value = [mock_comment]

        main_body_html = "<p>Processed main</p>"
        main_body_images = [{"src": "main.png", "alt": "Main"}]
        inline_html = "Processed inline"
        inline_images = [{"src": "inline.jpg", "alt": "Inline"}]

        mock_format_text.side_effect = [
            (main_body_html, main_body_images),
            (inline_html, inline_images),
        ]

        html_body, images_to_attach = asana_helpers.asana_comment_from_github_review(mock_review)

        self.assertIn(main_body_html, html_body)
        self.assertIn(inline_html, html_body)
        self.assertEqual(images_to_attach, main_body_images + inline_images)
        self.assertEqual(mock_format_text.call_count, 2)
        self.assertNotIn("<img", html_body.lower())

if __name__ == "__main__":
    from unittest import main as run_tests

    run_tests()
