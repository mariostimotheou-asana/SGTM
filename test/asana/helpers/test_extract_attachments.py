import unittest
from unittest.mock import patch, MagicMock, mock_open # Add MagicMock, mock_open
import urllib.request # Import for mocking urlopen errors

from src.asana import helpers as asana_helpers
from test.impl.base_test_case_class import BaseClass
# from test.impl.builders import builder, build # Not used in the new tests for create_attachments

# Keep existing tests for _extract_attachments, perhaps rename class for clarity
class TestAttachmentFunctions(BaseClass): # Renamed class
    def test_extract_no_attachments(self):
        github_comment = "No urls here!! ![but some weird formatting] (oops)"
        attachments = asana_helpers._extract_attachments(github_comment)
        self.assertEqual(len(attachments), 0)

    def test_extract_attachment_with_unknown_extension(self):
        github_comment = (
            "Ok here it is ![photoo ooo](www.photopng.com/this.fakeg) and there it was"
        )
        attachments = asana_helpers._extract_attachments(github_comment)
        self.assertEqual(len(attachments), 0)

    # Existing tests for _extract_attachments continue here...
    def test_extract_attachments_with_extensions(self):
        github_comment = (
            "Ok here's the first: ![photo.png](www.photopng.com/this.png) and the"
            " second!! ![giferino.gif](giphy.com/example.gif)"
        )
        attachments = asana_helpers._extract_attachments(github_comment)
        self.assertListEqual(
            attachments,
            [
                asana_helpers.AttachmentData(
                    file_name="photo.png",
                    file_url="www.photopng.com/this.png",
                    image_type="image/png",
                ),
                asana_helpers.AttachmentData(
                    file_name="giferino.gif",
                    file_url="giphy.com/example.gif",
                    image_type="image/gif",
                ),
            ],
        )

    def test_extract_attachment_without_extension(self):
        github_comment = (
            "Ok here's the first: ![photo](www.photopng.com/this.png) and that's it!"
        )
        attachments = asana_helpers._extract_attachments(github_comment)
        self.assertListEqual(
            attachments,
            [
                asana_helpers.AttachmentData(
                    file_name="photo.png",
                    file_url="www.photopng.com/this.png",
                    image_type="image/png",
                ),
            ],
        )

    def test_extract_attachment_no_file_name_given(self):
        github_comment = (
            "Ok here's the first: ![](www.photopng.com/this.png) and that's it!"
        )
        attachments = asana_helpers._extract_attachments(github_comment)
        self.assertListEqual(
            attachments,
            [
                asana_helpers.AttachmentData(
                    file_name="github_attachment.png",
                    file_url="www.photopng.com/this.png",
                    image_type="image/png",
                ),
            ],
        )


if __name__ == "__main__":
    from unittest import main as run_tests

    run_tests()

    # New tests for create_attachments (from previous attempt, ensure these are correctly placed)
    @patch("src.asana.helpers.asana_client.create_attachment_on_task")
    @patch("urllib.request.urlopen")
    @patch("src.asana.helpers._extract_attachments") # To verify it's NOT called
    def test_create_attachments_with_parsed_images_success(
        self, mock_extract_attachments, mock_urlopen, mock_create_asana_attachment
    ):
        task_id = "test_task_123"
        parsed_images = [
            {"src": "http://example.com/image.png", "alt": "Nice PNG"},
            {"src": "https://another.domain/pic.jpg?query=param", "alt": "Cool JPEG"},
            {"src": "http://images.com/no_alt.gif", "alt": ""}, # Empty alt
            {"src": "http://images.com/default_alt.jpeg", "alt": None}, # None alt
        ]
        
        mock_response = MagicMock()
        mock_response.read.return_value = b"image_data"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        asana_helpers.create_attachments(
            body_text="This body should not be used for extraction",
            task_id=task_id,
            parsed_images=parsed_images,
        )

        mock_extract_attachments.assert_not_called()
        self.assertEqual(mock_urlopen.call_count, 4)
        self.assertEqual(mock_create_asana_attachment.call_count, 4)

        expected_calls = [
            unittest.mock.call(task_id, b"image_data", "Nice PNG.png", "image/png"),
            unittest.mock.call(task_id, b"image_data", "Cool JPEG.jpg", "image/jpeg"),
            unittest.mock.call(task_id, b"image_data", "image_attachment.gif", "image/gif"),
            unittest.mock.call(task_id, b"image_data", "image_attachment.jpeg", "image/jpeg"),
        ]
        mock_create_asana_attachment.assert_has_calls(expected_calls, any_order=False)
    
    @patch("src.asana.helpers.logger.warning")
    @patch("src.asana.helpers.asana_client.create_attachment_on_task")
    @patch("urllib.request.urlopen")
    def test_create_attachments_with_parsed_images_unsupported_extension(
        self, mock_urlopen, mock_create_asana_attachment, mock_logger_warning
    ):
        task_id = "task_456"
        parsed_images = [
            {"src": "http://example.com/image.tiff", "alt": "Unsupported TIFF"},
            {"src": "http://example.com/image.png", "alt": "Supported PNG"},
        ]
        mock_response = MagicMock()
        mock_response.read.return_value = b"png_data"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        asana_helpers.create_attachments(task_id=task_id, body_text="", parsed_images=parsed_images)

        mock_urlopen.assert_called_once_with("http://example.com/image.png")
        mock_create_asana_attachment.assert_called_once_with(
            task_id, b"png_data", "Supported PNG.png", "image/png"
        )
        mock_logger_warning.assert_any_call(
            "Could not determine image type for http://example.com/image.tiff, extension .tiff. Skipping attachment."
        )

    @patch("src.asana.helpers.logger.warning")
    @patch("src.asana.helpers.asana_client.create_attachment_on_task")
    @patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Failed to open"))
    def test_create_attachments_with_parsed_images_urlopen_failure(
        self, mock_urlopen_failure, mock_create_asana_attachment, mock_logger_warning
    ):
        task_id = "task_789"
        parsed_images = [{"src": "http://example.com/image.jpg", "alt": "A JPG"}]

        asana_helpers.create_attachments(task_id=task_id, body_text="", parsed_images=parsed_images)

        mock_urlopen_failure.assert_called_once_with("http://example.com/image.jpg")
        mock_create_asana_attachment.assert_not_called()
        mock_logger_warning.assert_called_once_with(
            "Attachment creation failed. Creating task comment anyway."
        )

    @patch("src.asana.helpers._extract_attachments")
    @patch("src.asana.helpers.asana_client.create_attachment_on_task") 
    @patch("urllib.request.urlopen") 
    def test_create_attachments_no_parsed_images_fallback_to_extract(
        self, mock_urlopen, mock_asana_create, mock_extract_attachments
    ):
        task_id = "task_abc"
        body_text_for_extraction = "Some body with ![img](url.png)"
        
        extracted_data = [
            asana_helpers.AttachmentData(
                file_name="extracted.png",
                file_url="http://extracted_url.com/extracted.png",
                image_type="image/png",
            )
        ]
        mock_extract_attachments.return_value = extracted_data
        
        mock_response = MagicMock()
        mock_response.read.return_value = b"extracted_data_bytes"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Test with parsed_images = None
        asana_helpers.create_attachments(body_text=body_text_for_extraction, task_id=task_id, parsed_images=None)
        mock_extract_attachments.assert_called_once_with(body_text_for_extraction)
        mock_urlopen.assert_called_once_with("http://extracted_url.com/extracted.png")
        mock_asana_create.assert_called_once_with(
            task_id, b"extracted_data_bytes", "extracted.png", "image/png"
        )
        
        mock_extract_attachments.reset_mock()
        mock_urlopen.reset_mock()
        mock_asana_create.reset_mock()

        # Test with parsed_images = [] (empty list)
        asana_helpers.create_attachments(body_text=body_text_for_extraction, task_id=task_id, parsed_images=[])
        mock_extract_attachments.assert_called_with(body_text_for_extraction) # Should be called again
        # Ensure urlopen and create_attachment are not called again if extract_attachments returns empty or different data
        # For this specific setup, if it returns the same, it would be called again.
        # If the goal is to ensure it's called and then its output is processed:
        mock_urlopen.assert_called_once_with("http://extracted_url.com/extracted.png")
        mock_asana_create.assert_called_once_with(
            task_id, b"extracted_data_bytes", "extracted.png", "image/png"
        )

if __name__ == "__main__":
    unittest.main()
