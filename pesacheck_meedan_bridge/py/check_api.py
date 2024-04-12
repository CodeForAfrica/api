import json

import requests
import settings
import sentry_sdk


def create_mutation_query(
    media_type="Blank",
    channel=None,
    set_tags=[],
    set_status="",
    set_claim_description="",
    title="",
    summary="",
    url="",
    language="",
    publish_report=False,
):
    mutation_query = f"""
      mutation create {{
        createProjectMedia(input: {{
          media_type: "{media_type}",
          channel: {{ main: {channel} }},
          set_tags: {json.dumps(set_tags)},
          set_status: "{set_status}",
          set_claim_description: \"\"\"{set_claim_description}\"\"\",
          set_fact_check: {{
            title: \"\"\"{title}\"\"\",
            summary: \"\"\"{summary}\"\"\",
            url: "{url}",
            language: "{language}",
            publish_report: {str(publish_report).lower()}
          }}
        }}) {{
          project_media {{
            id
            full_url
            claim_description {{
              fact_check {{
                id
              }}
            }}
          }}
        }}
      }}
    """

    return mutation_query


def delete_mutation_query(id):
    mutation_query = f"""
    mutation {{
      destroyFactCheck(input: {{
        id: "{id}"
      }}) {{ deletedId }}
    }}
    """
    return mutation_query


def post_to_check(data):
    query = create_mutation_query(**data)
    headers = {
        "Content-Type": "application/json",
        "X-Check-Token": settings.PESACHECK_CHECK_TOKEN,
        "X-Check-Team": settings.PESACHECK_CHECK_WORKSPACE_SLUG,
    }
    body = dict(query=query)
    url = settings.PESACHECK_CHECK_URL
    response = requests.post(url, headers=headers, json=body, timeout=60)
    res = response.json()
    if res.get("errors"):
        sentry_sdk.capture_exception(Exception(str(res.get("errors"))))
        return None
    if response.status_code == 200:
        return res
    sentry_sdk.capture_exception(Exception(response.text))
    return None
