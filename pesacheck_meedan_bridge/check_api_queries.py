import json


def create_mutation_query(
    media_type=None,
    channel=None,
    set_tags=None,
    set_status=None,
    set_claim_description=None,
    title=None,
    summary=None,
    url=None,
    language=None,
    publish_report=False,
):
    mutation_query = f"""
      mutation create {{
        createProjectMedia(input: {{
          media_type: "{media_type or "Blank"}",
          channel: {{ main: {channel} }},
          set_tags: {json.dumps(set_tags or [])},
          set_status: "{set_status or ""}",
          set_claim_description: "{set_claim_description or ""}",
          set_fact_check: {{
            title: "{title or ""}",
            summary: "{summary or ""}",
            url: "{url or ""}",
            language: "{language or ""}",
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
