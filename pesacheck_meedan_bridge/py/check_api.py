import json

import requests
import settings

# Check refuses a fact-check it already has, via a unique index on the
# fact-check signature. The article is in Check, so there is nothing to retry.
# This is Check's own Postgres index name, surfaced in the GraphQL error text:
# it is not part of any API contract, so a rename upstream would stop it
# matching and duplicates would go back to being retried every run.
DUPLICATE_CONSTRAINT = "index_fact_checks_on_signature"


def error_message(error):
    """The text of one GraphQL error, whatever shape the server sent."""
    if isinstance(error, dict):
        return str(error.get("message") or "")
    return str(error or "")


def is_duplicate(errors):
    """True when the ONLY thing wrong is that Check already has this one.

    A response can carry several errors; treating it as a duplicate because one
    of them matches would mark the row terminally and silently drop the rest.
    """
    if not errors:
        return False
    return all(DUPLICATE_CONSTRAINT in error_message(error) for error in errors)


class DuplicateFactCheckError(Exception):
    pass


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
    errors = res.get("errors") or []
    if is_duplicate(errors):
        raise DuplicateFactCheckError(response.text)
    if response.status_code != 200 or errors:
        raise Exception(response.text)
    project_media = ((res.get("data") or {}).get("createProjectMedia") or {}).get(
        "project_media"
    )
    if not project_media:
        # e.g. a field-level rejection: HTTP 200 with a null createProjectMedia.
        raise Exception(response.text)
    return res
