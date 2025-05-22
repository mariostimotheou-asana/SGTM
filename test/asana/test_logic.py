from unittest.mock import patch, Mock
from test.impl.builders import builder, build
from test.impl.base_test_case_class import BaseClass
from src.asana import logic as asana_logic


class TestShouldAutocompleteTasksOnMerge(BaseClass):
    @patch("src.asana.logic.SGTM_FEATURE__AUTOCOMPLETE_ENABLED", False)
    def test_false_if_feature_not_enabled(self):
        pull_request = build(
            builder.pull_request()
            .merged(True)
            .label(
                builder.label().name(
                    asana_logic.AutocompleteLabel.COMPLETE_ON_MERGE.value
                )
            )
        )
        self.assertFalse(asana_logic.should_autocomplete_tasks_on_merge(pull_request))

    @patch("src.asana.logic.SGTM_FEATURE__AUTOCOMPLETE_ENABLED", True)
    def test_false_if_pull_request_is_not_merged(self):
        pull_request = build(
            builder.pull_request()
            .merged(False)
            .label(
                builder.label().name(
                    asana_logic.AutocompleteLabel.COMPLETE_ON_MERGE.value
                )
            )
        )
        self.assertFalse(asana_logic.should_autocomplete_tasks_on_merge(pull_request))

    @patch("src.asana.logic.SGTM_FEATURE__AUTOCOMPLETE_ENABLED", True)
    def test_false_if_pull_request_does_not_have_autocomplete_label(self):
        pull_request = build(builder.pull_request().merged(True))
        self.assertFalse(asana_logic.should_autocomplete_tasks_on_merge(pull_request))

    @patch("src.asana.logic.SGTM_FEATURE__AUTOCOMPLETE_ENABLED", True)
    def test_true_if_should_autocomplete(self):
        pull_request = build(
            builder.pull_request()
            .merged(True)
            .label(
                builder.label().name(
                    asana_logic.AutocompleteLabel.COMPLETE_ON_MERGE.value
                )
            )
        )
        self.assertTrue(asana_logic.should_autocomplete_tasks_on_merge(pull_request))

# New Test Class for image attachment handling in logic functions
from unittest.mock import MagicMock
from src.github.models import Comment as GithubComment
from src.github.models import Review as GithubReview
from src.github.models import PullRequest as GithubPullRequest

# Assuming the functions to test are directly in asana_logic
# If they are not (e.g. were hypothetical and added to a different file, adjust import)
# For this test, we assume they are present in asana_logic as per previous steps.
from src.asana.logic import (
    _add_comment_to_task_from_github_comment,
    _add_comment_to_task_from_github_review,
    _create_task_from_pull_request,
    _update_task_from_pull_request,
)

class TestAsanaLogicImageAttachmentHandling(BaseClass):
    @patch('src.asana.logic.asana_helpers.create_attachments')
    @patch('src.asana.logic.asana_helpers.asana_comment_from_github_comment')
    @patch('src.asana.logic.asana_client.add_comment_to_task')
    def test_add_comment_from_github_comment_with_images(
        self, mock_asana_add_comment, mock_helper_comment_format, mock_create_attachments
    ):
        task_id = "task_123"
        mock_github_comment = MagicMock(spec=GithubComment)
        mock_github_comment.id.return_value = "comment_id_1"
        # This body is used as fallback by create_attachments if images are from a different source than body
        mock_github_comment.body.return_value = "Original comment body with <img src='test.png'>"

        expected_html = "<p>Processed comment</p>"
        expected_images = [{"src": "test.png", "alt": "Test Image"}]
        mock_helper_comment_format.return_value = (expected_html, expected_images)

        _add_comment_to_task_from_github_comment(task_id, mock_github_comment)

        mock_helper_comment_format.assert_called_once_with(mock_github_comment)
        mock_asana_add_comment.assert_called_once_with(task_id, expected_html)
        mock_create_attachments.assert_called_once_with(
            body_text=mock_github_comment.body(),
            task_id=task_id,
            parsed_images=expected_images
        )

    @patch('src.asana.logic.asana_helpers.create_attachments')
    @patch('src.asana.logic.asana_helpers.asana_comment_from_github_comment')
    @patch('src.asana.logic.asana_client.add_comment_to_task')
    def test_add_comment_from_github_comment_no_images(
        self, mock_asana_add_comment, mock_helper_comment_format, mock_create_attachments
    ):
        task_id = "task_456"
        mock_github_comment = MagicMock(spec=GithubComment)
        mock_github_comment.id.return_value = "comment_id_2"
        mock_github_comment.body.return_value = "Original comment body no images"

        expected_html = "<p>Processed comment no images</p>"
        expected_images = [] # No images
        mock_helper_comment_format.return_value = (expected_html, expected_images)

        _add_comment_to_task_from_github_comment(task_id, mock_github_comment)

        mock_helper_comment_format.assert_called_once_with(mock_github_comment)
        mock_asana_add_comment.assert_called_once_with(task_id, expected_html)
        mock_create_attachments.assert_called_once_with(
            body_text=mock_github_comment.body(),
            task_id=task_id,
            parsed_images=expected_images
        )

    @patch('src.asana.logic.asana_helpers.create_attachments')
    @patch('src.asana.logic.asana_helpers.asana_comment_from_github_review')
    @patch('src.asana.logic.asana_client.add_comment_to_task')
    def test_add_comment_from_github_review_with_images(
        self, mock_asana_add_comment, mock_helper_review_format, mock_create_attachments
    ):
        task_id = "task_789"
        mock_github_review = MagicMock(spec=GithubReview)
        mock_github_review.id.return_value = "review_id_1"
        mock_github_review.body.return_value = "Original review body with <img src='review.jpg'>"

        expected_html = "<p>Processed review</p>"
        expected_images = [{"src": "review.jpg", "alt": "Review Image"}]
        mock_helper_review_format.return_value = (expected_html, expected_images)

        _add_comment_to_task_from_github_review(task_id, mock_github_review)

        mock_helper_review_format.assert_called_once_with(mock_github_review)
        mock_asana_add_comment.assert_called_once_with(task_id, expected_html)
        mock_create_attachments.assert_called_once_with(
            body_text=mock_github_review.body(),
            task_id=task_id,
            parsed_images=expected_images
        )

    @patch('src.asana.logic.asana_helpers.create_attachments')
    @patch('src.asana.logic.asana_helpers.extract_task_fields_from_pull_request')
    @patch('src.asana.logic.asana_client.create_task')
    def test_create_task_from_pull_request_with_images(
        self, mock_asana_create_task, mock_helper_extract_fields, mock_create_attachments
    ):
        project_id = "project_123"
        mock_pr = MagicMock(spec=GithubPullRequest)
        mock_pr.id.return_value = "pr_id_1"
        mock_pr.body.return_value = "Original PR body with <img src='pr.gif'>" # Fallback for create_attachments

        expected_task_fields_no_images = {
            "name": "Test PR Task",
            "assignee": "user_gid_1",
            # html_notes and images_to_attach are popped, so not in this dict
        }
        expected_html_notes = "<p>PR Description processed</p>"
        expected_images = [{"src": "pr.gif", "alt": "PR GIF"}]
        
        # Mock for extract_task_fields_from_pull_request
        # It should return a dict that includes html_notes and images_to_attach
        mock_helper_extract_fields.return_value = {
            **expected_task_fields_no_images, 
            "html_notes": expected_html_notes,
            "images_to_attach": expected_images
        }
        
        new_task_id = "new_task_abc"
        mock_asana_create_task.return_value = new_task_id

        result_task_id = _create_task_from_pull_request(mock_pr, project_id)

        self.assertEqual(result_task_id, new_task_id)
        mock_helper_extract_fields.assert_called_once_with(mock_pr)
        # Verify create_task was called with html_notes, and other fields via **task_fields
        mock_asana_create_task.assert_called_once_with(
            project_id=project_id,
            name=expected_task_fields_no_images["name"],
            html_notes=expected_html_notes,
            **expected_task_fields_no_images # This will unpack 'assignee' etc.
        )
        mock_create_attachments.assert_called_once_with(
            body_text=mock_pr.body(),
            task_id=new_task_id,
            parsed_images=expected_images
        )

    @patch('src.asana.logic.asana_helpers.create_attachments')
    @patch('src.asana.logic.asana_helpers.extract_task_fields_from_pull_request')
    @patch('src.asana.logic.asana_client.update_task')
    def test_update_task_from_pull_request_with_images(
        self, mock_asana_update_task, mock_helper_extract_fields, mock_create_attachments
    ):
        task_id = "existing_task_def"
        mock_pr = MagicMock(spec=GithubPullRequest)
        mock_pr.id.return_value = "pr_id_2"
        mock_pr.body.return_value = "Updated PR body with <img src='update.bmp'>"

        expected_task_fields_for_update = {
            "name": "Updated PR Task Name",
            "completed": True,
             # html_notes and images_to_attach are popped
        }
        expected_html_notes = "<p>Updated PR Description processed</p>"
        expected_images = [{"src": "update.bmp", "alt": "PR BMP"}]

        mock_helper_extract_fields.return_value = {
            **expected_task_fields_for_update,
            "html_notes": expected_html_notes,
            "images_to_attach": expected_images
        }
        
        # existing_task mock, not strictly used by the current _update_task_from_pull_request logic
        # but good to have if the function evolves to use it.
        mock_existing_task = {"gid": task_id, "name": "Old Name"}

        _update_task_from_pull_request(task_id, mock_pr, mock_existing_task)

        mock_helper_extract_fields.assert_called_once_with(mock_pr)
        
        # Construct what fields_to_update would be inside the function
        final_fields_for_asana_update = {
            **expected_task_fields_for_update,
            "html_notes": expected_html_notes
        }
        mock_asana_update_task.assert_called_once_with(
            task_id=task_id,
            **final_fields_for_asana_update
        )
        mock_create_attachments.assert_called_once_with(
            body_text=mock_pr.body(),
            task_id=task_id,
            parsed_images=expected_images
        )


if __name__ == "__main__":
    from unittest import main as run_tests

    run_tests()
