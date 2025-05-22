import unittest
from unittest.mock import patch, MagicMock

from bs4 import BeautifulSoup

# Assuming the helpers module is in src.asana.helpers
from src.asana.helpers import _format_github_text_for_asana
# We also need to import the functions that _format_github_text_for_asana calls internally
# if we want to assert they were called, or if their behavior is part of the test.
from src.markdown_parser import convert_github_markdown_to_asana_xml
from src.asana.helpers import _transform_github_mentions_to_asana_mentions


class TestFormatGithubTextForAsana(unittest.TestCase):
    @patch("src.asana.helpers._transform_github_mentions_to_asana_mentions")
    @patch("src.asana.helpers.convert_github_markdown_to_asana_xml")
    def test_no_image_tags(
        self, mock_convert_markdown, mock_transform_mentions
    ):
        text = "<p>This is a test paragraph.</p>"
        # Mock the internal calls to return their input to isolate _format_github_text_for_asana's direct logic
        mock_convert_markdown.side_effect = lambda x: x
        mock_transform_mentions.side_effect = lambda x: x

        formatted_text, images = _format_github_text_for_asana(text)

        self.assertEqual(formatted_text, text)
        self.assertEqual(images, [])
        mock_convert_markdown.assert_called_once_with(text)
        mock_transform_mentions.assert_called_once_with(text)

    @patch("src.asana.helpers._transform_github_mentions_to_asana_mentions")
    @patch("src.asana.helpers.convert_github_markdown_to_asana_xml")
    def test_one_valid_image_tag(
        self, mock_convert_markdown, mock_transform_mentions
    ):
        text = '<p>Text with <img src="http://example.com/image.png" alt="Test Image"> an image.</p>'
        expected_text_after_img_removal = "<p>Text with  an image.</p>"
        expected_images = [{"src": "http://example.com/image.png", "alt": "Test Image"}]

        # Mock the internal calls
        mock_convert_markdown.side_effect = lambda x: x # Pass through
        mock_transform_mentions.side_effect = lambda x: x # Pass through

        formatted_text, images = _format_github_text_for_asana(text)

        self.assertEqual(formatted_text, expected_text_after_img_removal)
        self.assertEqual(images, expected_images)
        mock_convert_markdown.assert_called_once_with(expected_text_after_img_removal)
        mock_transform_mentions.assert_called_once_with(expected_text_after_img_removal)

    @patch("src.asana.helpers._transform_github_mentions_to_asana_mentions")
    @patch("src.asana.helpers.convert_github_markdown_to_asana_xml")
    def test_multiple_image_tags(
        self, mock_convert_markdown, mock_transform_mentions
    ):
        text = '<p><img src="img1.jpg" alt="Alt1"> some text <img src="http://domain.com/img2.gif" alt="Alt2"></p>'
        expected_text_after_img_removal = "<p> some text </p>"
        expected_images = [
            {"src": "img1.jpg", "alt": "Alt1"},
            {"src": "http://domain.com/img2.gif", "alt": "Alt2"},
        ]
        mock_convert_markdown.side_effect = lambda x: x
        mock_transform_mentions.side_effect = lambda x: x

        formatted_text, images = _format_github_text_for_asana(text)
        self.assertEqual(formatted_text, expected_text_after_img_removal)
        self.assertEqual(images, expected_images)

    @patch("src.asana.helpers._transform_github_mentions_to_asana_mentions")
    @patch("src.asana.helpers.convert_github_markdown_to_asana_xml")
    def test_image_tag_empty_alt(
        self, mock_convert_markdown, mock_transform_mentions
    ):
        text = '<img src="empty_alt.png" alt="">'
        expected_text_after_img_removal = ""
        expected_images = [{"src": "empty_alt.png", "alt": ""}]
        mock_convert_markdown.side_effect = lambda x: x
        mock_transform_mentions.side_effect = lambda x: x

        formatted_text, images = _format_github_text_for_asana(text)
        self.assertEqual(formatted_text, expected_text_after_img_removal)
        self.assertEqual(images, expected_images)

    @patch("src.asana.helpers._transform_github_mentions_to_asana_mentions")
    @patch("src.asana.helpers.convert_github_markdown_to_asana_xml")
    def test_image_tag_no_alt_attribute(
        self, mock_convert_markdown, mock_transform_mentions
    ):
        text = '<img src="no_alt.jpeg">'
        expected_text_after_img_removal = ""
        # The implementation defaults to "image" if alt is None
        expected_images = [{"src": "no_alt.jpeg", "alt": "image"}]
        mock_convert_markdown.side_effect = lambda x: x
        mock_transform_mentions.side_effect = lambda x: x

        formatted_text, images = _format_github_text_for_asana(text)
        self.assertEqual(formatted_text, expected_text_after_img_removal)
        self.assertEqual(images, expected_images)
        
    @patch("src.asana.helpers._transform_github_mentions_to_asana_mentions")
    @patch("src.asana.helpers.convert_github_markdown_to_asana_xml")
    def test_image_tag_with_query_params_in_src(
        self, mock_convert_markdown, mock_transform_mentions
    ):
        text = '<img src="image.png?param=value&another=true" alt="Image with params">'
        expected_text_after_img_removal = ""
        expected_images = [{"src": "image.png?param=value&another=true", "alt": "Image with params"}]
        mock_convert_markdown.side_effect = lambda x: x
        mock_transform_mentions.side_effect = lambda x: x

        formatted_text, images = _format_github_text_for_asana(text)
        self.assertEqual(formatted_text, expected_text_after_img_removal)
        self.assertEqual(images, expected_images)

    @patch("src.asana.helpers.s3_client") # Mock s3_client for mention transformation
    def test_mixed_html_markdown_and_mentions(self, mock_s3_client):
        # This test is more of an integration test for _format_github_text_for_asana
        # It checks that the img tag removal happens before markdown and mention processing.

        # Mock the s3_client call within _transform_github_mentions_to_asana_mentions
        mock_s3_client.get_asana_domain_user_id_from_github_handle.return_value = "asana_user_gid_for_testuser"
        
        text = """### Title
Hello @testuser!
This is a *markdown* text.
<img src="test.gif" alt="A GIF">
Another paragraph with `code`.
And a final image: <img src="final.png" alt="">"""

        # Expected state after image removal (input to markdown and mention processing)
        text_after_img_removal = """### Title
Hello @testuser!
This is a *markdown* text.

Another paragraph with `code`.
And a final image: """

        # Expected final HTML structure (simplified, actual might vary based on markdown parser)
        # The key is that mentions are processed and markdown is converted.
        # BeautifulSoup by default adds <html><body> tags when parsing a fragment.
        # The actual output of convert_github_markdown_to_asana_xml and _transform_github_mentions_to_asana_mentions
        # will determine the exact expected_formatted_text.
        # For this test, let's assume convert_github_markdown_to_asana_xml does its job
        # and _transform_github_mentions_to_asana_mentions correctly converts @testuser.

        # Let's get the actual output of the internal functions for a more robust check
        # 1. After image removal, text becomes `text_after_img_removal`
        # 2. Then `convert_github_markdown_to_asana_xml` is called
        # 3. Then `_transform_github_mentions_to_asana_mentions` is called

        # We need to ensure BeautifulSoup doesn't add <html><body> tags if the original text didn't imply a full document.
        # The current _format_github_text_for_asana does `str(soup)`, which for fragments might not include <html><body>.
        # Let's assume convert_github_markdown_to_asana_xml and _transform_github_mentions_to_asana_mentions
        # are tested elsewhere and work correctly.

        # Simplified expectation:
        # - Markdown like ### and * is converted to Asana XML (e.g., <strong> for bold)
        # - Mentions like @testuser are converted to Asana user links
        # - Images are gone from the text and present in the list
        
        # To make this test more focused on _format_github_text_for_asana's orchestration:
        # Patch the sub-functions and check they are called with the image-stripped text.
        
        with patch("src.asana.helpers.convert_github_markdown_to_asana_xml") as mock_convert, \
             patch("src.asana.helpers._transform_github_mentions_to_asana_mentions") as mock_transform:
            
            mock_convert.return_value = "markdown_converted_text" # Dummy return
            mock_transform.return_value = "final_transformed_text" # Dummy return

            formatted_text, images = _format_github_text_for_asana(text)

            expected_images = [
                {"src": "test.gif", "alt": "A GIF"},
                {"src": "final.png", "alt": ""},
            ]

            self.assertEqual(images, expected_images)
            self.assertEqual(formatted_text, "final_transformed_text")
            
            # Verify that the functions were called with the text *after* images were removed.
            # The `str(soup)` operation might produce slightly different whitespace/formatting
            # than manually typing `text_after_img_removal`.
            # We can parse `text_after_img_removal` with BeautifulSoup as well for a more robust comparison.
            
            # What BeautifulSoup will output after parsing text and removing images:
            # (Note: BeautifulSoup might add <html><body> tags if not handled carefully, 
            # but current _format_github_text_for_asana does str(soup) on a fragment)
            # Let's simulate the soup to string conversion carefully for the assertion.
            soup = BeautifulSoup(text, "html.parser")
            for img_tag in soup.find_all("img"):
                img_tag.decompose()
            processed_text_for_assertion = str(soup)

            mock_convert.assert_called_once_with(processed_text_for_assertion)
            mock_transform.assert_called_once_with("markdown_converted_text")


if __name__ == "__main__":
    unittest.main()
