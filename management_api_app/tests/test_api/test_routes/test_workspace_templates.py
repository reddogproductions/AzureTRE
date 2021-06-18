import json
import pytest
from mock import patch

from fastapi import FastAPI
from starlette import status
from httpx import AsyncClient

from db.errors import EntityDoesNotExist, UnableToAccessDatabase
from models.domain.resource_template import ResourceTemplate, Parameter, ResourceType
from models.schemas.workspace_template import get_sample_workspace_template_object, WorkspaceTemplateInCreate
from resources import strings


pytestmark = pytest.mark.asyncio


def sample_workspace_template() -> ResourceTemplate:
    return ResourceTemplate(
        id="1234",
        name="my-tre-workspace",
        version="0.0.1",
        description="workspace template for great product",
        parameters=[Parameter(name="azure_location", type="string", default=None, applyTo="All Actions", description="", required=False)],
        resourceType=ResourceType.Workspace,
        current=True)


@pytest.fixture
def input_workspace_template() -> dict:
    return WorkspaceTemplateInCreate(
        name="my-tre-workspace",
        version="0.0.1",
        description="workspace template for great product",
        parameters=[Parameter(name="azure_location", type="string")],
        current=True).dict()


@pytest.fixture
def output_workspace_template() -> dict:
    return sample_workspace_template().dict()


# [GET] /workspace-templates
@patch("api.routes.workspace_templates.WorkspaceTemplateRepository.get_workspace_template_names")
async def test_workspace_templates_returns_template_names(get_workspace_template_names_mock, app: FastAPI, client: AsyncClient):
    expected_template_names = ["template1", "template2"]
    get_workspace_template_names_mock.return_value = expected_template_names

    response = await client.get(app.url_path_for(strings.API_GET_WORKSPACE_TEMPLATES))

    actual_template_names = response.json()["templateNames"]
    assert len(actual_template_names) == len(expected_template_names)
    for name in expected_template_names:
        assert name in actual_template_names


async def test_post_does_not_create_a_template_with_bad_payload(app: FastAPI, client: AsyncClient):
    input_data = """
                    {
                        "blah": "blah"
                    }
    """

    response = await client.post(app.url_path_for(strings.API_CREATE_WORKSPACE_TEMPLATES), json=input_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@patch("api.routes.workspace_templates.WorkspaceTemplateRepository.create_workspace_template_item")
@patch("api.routes.workspace_templates.WorkspaceTemplateRepository.get_current_workspace_template_by_name")
@patch("api.routes.workspace_templates.WorkspaceTemplateRepository.get_workspace_template_by_name_and_version")
async def test_when_updating_current_and_template_not_found_create_one(get_name_ver_mock,
                                                                       get_current_mock,
                                                                       create_item_mock,
                                                                       app: FastAPI,
                                                                       client: AsyncClient,
                                                                       input_workspace_template: dict,
                                                                       output_workspace_template: dict):
    get_name_ver_mock.side_effect = EntityDoesNotExist
    get_current_mock.side_effect = EntityDoesNotExist

    response_content = output_workspace_template
    create_item_mock.return_value = response_content

    response = await client.post(app.url_path_for(strings.API_CREATE_WORKSPACE_TEMPLATES), json=input_workspace_template)

    assert response.status_code == status.HTTP_201_CREATED
    assert json.loads(response.text)["workspaceTemplate"] == response_content


@patch("api.routes.workspace_templates.WorkspaceTemplateRepository.create_workspace_template_item")
@patch("api.routes.workspace_templates.WorkspaceTemplateRepository.update_item")
@patch("api.routes.workspace_templates.WorkspaceTemplateRepository.get_current_workspace_template_by_name")
@patch("api.routes.workspace_templates.WorkspaceTemplateRepository.get_workspace_template_by_name_and_version")
async def test_when_updating_current_and_template_found_update_and_add(get_name_ver_mock,
                                                                       get_current_mock,
                                                                       update_item_mock,
                                                                       create_item_mock,
                                                                       app: FastAPI,
                                                                       client: AsyncClient,
                                                                       input_workspace_template: dict,
                                                                       output_workspace_template: dict):
    get_name_ver_mock.side_effect = EntityDoesNotExist

    response_content = output_workspace_template
    create_item_mock.return_value = response_content

    existing_current_workspace_template = sample_workspace_template()
    get_current_mock.return_value = existing_current_workspace_template

    response = await client.post(app.url_path_for(strings.API_CREATE_WORKSPACE_TEMPLATES), json=input_workspace_template)

    updated_current_workspace_template = existing_current_workspace_template
    updated_current_workspace_template.current = False
    update_item_mock.assert_called_once_with(updated_current_workspace_template.dict())
    assert response.status_code == status.HTTP_201_CREATED
    assert json.loads(response.text)["workspaceTemplate"] == response_content


@patch("api.routes.workspace_templates.WorkspaceTemplateRepository.get_workspace_template_by_name_and_version")
async def test_same_name_and_version_template_not_allowed(mock, app: FastAPI, client: AsyncClient, input_workspace_template: dict):
    mock.return_value = ["exists"]

    response = await client.post(app.url_path_for(strings.API_CREATE_WORKSPACE_TEMPLATES), json=input_workspace_template)

    assert response.status_code == status.HTTP_409_CONFLICT


@patch("api.routes.workspace_templates.WorkspaceTemplateRepository.create_workspace_template_item")
@patch("api.routes.workspace_templates.WorkspaceTemplateRepository.get_workspace_template_by_name_and_version")
async def test_when_not_updating_current_a_unique_template_is_saved(get_mock, create_mock, app: FastAPI, client: AsyncClient, input_workspace_template: dict, output_workspace_template: dict):
    input_workspace_template["current"] = False
    get_mock.side_effect = EntityDoesNotExist

    response_content = output_workspace_template
    create_mock.return_value = response_content

    response = await client.post(app.url_path_for(strings.API_CREATE_WORKSPACE_TEMPLATES), json=input_workspace_template)

    assert response.status_code == status.HTTP_201_CREATED
    assert json.loads(response.text)["workspaceTemplate"] == response_content


@patch("api.routes.workspace_templates.WorkspaceTemplateRepository.get_current_workspace_template_by_name")
async def test_workspace_templates_by_name_returns_workspace_template(get_workspace_template_by_name_mock, app: FastAPI, client: AsyncClient):
    get_workspace_template_by_name_mock.return_value = get_sample_workspace_template_object(template_name="template1")

    response = await client.get(app.url_path_for(strings.API_GET_WORKSPACE_TEMPLATE_BY_NAME, template_name="tre-workspace-vanilla"))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["workspaceTemplate"]["name"] == "template1"


@patch("api.routes.workspace_templates.WorkspaceTemplateRepository.get_current_workspace_template_by_name")
async def test_workspace_templates_by_name_returns_404_if_template_does_not_exist(get_workspace_template_by_name_mock, app: FastAPI, client: AsyncClient):
    get_workspace_template_by_name_mock.side_effect = EntityDoesNotExist

    response = await client.get(app.url_path_for(strings.API_GET_WORKSPACE_TEMPLATE_BY_NAME, template_name="tre-workspace-vanilla"))

    assert response.status_code == status.HTTP_404_NOT_FOUND


@patch("api.routes.workspace_templates.WorkspaceTemplateRepository.get_current_workspace_template_by_name")
async def test_workspace_templates_by_name_returns_503_on_database_error(get_workspace_template_by_name_mock, app: FastAPI, client: AsyncClient):
    get_workspace_template_by_name_mock.side_effect = UnableToAccessDatabase

    response = await client.get(app.url_path_for(strings.API_GET_WORKSPACE_TEMPLATE_BY_NAME, template_name="tre-workspace-vanilla"))

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
