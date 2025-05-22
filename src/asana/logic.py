from src.github.models import PullRequest
from src.github.helpers import pull_request_has_label
from enum import Enum, unique
from src.config import (
    SGTM_FEATURE__AUTOCOMPLETE_ENABLED,
    SGTM_FEATURE__ALLOW_PERSISTENT_TASK_ASSIGNEE,
)
from typing import Dict, List, Optional, Tuple, Any # Added
import src.asana.helpers as asana_helpers # Added
import src.asana.client as asana_client # Added
from src.github.models import Comment as GithubComment # Added
from src.github.models import Review as GithubReview # Added
from src.logger import logger # Added


@unique
class AutocompleteLabel(Enum):
    COMPLETE_ON_MERGE = "complete tasks on merge"


@unique
class TaskAssigneeLabel(Enum):
    PERSISTENT = "persistent task assignee"


def should_autocomplete_tasks_on_merge(pull_request: PullRequest) -> bool:
    return (
        SGTM_FEATURE__AUTOCOMPLETE_ENABLED
        and pull_request.merged()
        and pull_request_has_label(
            pull_request, AutocompleteLabel.COMPLETE_ON_MERGE.value
        )
    )


def should_set_task_owner_to_pr_author(pull_request: PullRequest) -> bool:
    return SGTM_FEATURE__ALLOW_PERSISTENT_TASK_ASSIGNEE and pull_request_has_label(
        pull_request, TaskAssigneeLabel.PERSISTENT.value
    )


# Hypothetical functions based on subtask description - actual implementation might vary
def _add_comment_to_task_from_github_comment(task_id: str, comment: GithubComment):
    logger.info(
        f"Adding comment to task {task_id} from github comment {comment.id()}"
    )
    html_body, images_to_attach = asana_helpers.asana_comment_from_github_comment(
        comment
    )
    asana_client.add_comment_to_task(task_id, html_body)
    # Always call create_attachments, it will handle empty images_to_attach
    asana_helpers.create_attachments(
        body_text=comment.body(), task_id=task_id, parsed_images=images_to_attach
    )


def _add_comment_to_task_from_github_review(task_id: str, review: GithubReview):
    logger.info(f"Adding comment to task {task_id} from github review {review.id()}")
    html_body, images_to_attach = asana_helpers.asana_comment_from_github_review(
        review
    )
    asana_client.add_comment_to_task(task_id, html_body)
    # Always call create_attachments, it will handle empty images_to_attach
    asana_helpers.create_attachments(
        body_text=review.body(), task_id=task_id, parsed_images=images_to_attach
    )


def _create_task_from_pull_request(
    pull_request: PullRequest, project_id: str
) -> Optional[str]:
    logger.info(
        f"Creating task for pull_request {pull_request.id()} in project {project_id}"
    )
    task_fields = asana_helpers.extract_task_fields_from_pull_request(pull_request)

    description_html = task_fields.pop("html_notes", None) # Use .pop to remove for clarity
    images_for_description = task_fields.pop("images_to_attach", []) # Default to empty list

    # Ensure essential fields like 'name' are present
    task_name = task_fields.get("name")
    if not task_name:
        logger.error("Task name is missing. Cannot create task.")
        return None

    # Remaining fields in task_fields are passed directly to create_task
    new_task_id = asana_client.create_task(
        project_id=project_id,
        name=task_name,
        html_notes=description_html,
        **task_fields # Pass remaining fields like assignee, followers, custom_fields, completed
    )

    if new_task_id: # new_task_id could be None if creation fails
        # Always call create_attachments, it will handle empty images_for_description
        asana_helpers.create_attachments(
            body_text=pull_request.body(), 
            task_id=new_task_id,
            parsed_images=images_for_description,
        )
    return new_task_id


def _update_task_from_pull_request(
    task_id: str, pull_request: PullRequest, existing_task: Dict[str, Any] # existing_task is not used here, consider removing if not needed elsewhere
):
    logger.info(f"Updating task {task_id} from pull_request {pull_request.id()}")
    updated_task_fields = asana_helpers.extract_task_fields_from_pull_request(
        pull_request
    )

    description_html = updated_task_fields.pop("html_notes", None)
    images_for_description = updated_task_fields.pop("images_to_attach", []) # Default to empty list

    # Fields to update are those remaining in updated_task_fields plus html_notes if present
    fields_to_update = updated_task_fields
    if description_html is not None:
        fields_to_update["html_notes"] = description_html
    
    # Remove images_to_attach if it was added to fields_to_update by mistake
    fields_to_update.pop("images_to_attach", None)


    if fields_to_update:
        asana_client.update_task(task_id=task_id, **fields_to_update)
    else:
        logger.info(f"No fields to update for task {task_id}")

    # Always call create_attachments, it will handle empty images_for_description
    # This ensures attachments are updated if the PR body changes.
    asana_helpers.create_attachments(
        body_text=pull_request.body(), 
        task_id=task_id,
        parsed_images=images_for_description,
    )
