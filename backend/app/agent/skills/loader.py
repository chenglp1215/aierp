import re
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

FRONT_MATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)


def parse_front_matter(content: str) -> tuple[Dict[str, Any], str]:
    match = FRONT_MATTER_PATTERN.match(content)
    if not match:
        return {}, content

    front_matter_text = match.group(1)
    body = content[match.end():]

    result = {}
    for line in front_matter_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            if value.startswith('[') and value.endswith(']'):
                value = [v.strip().strip('"\'') for v in value[1:-1].split(',')]
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]

            result[key] = value

    return result, body


def parse_skill_markdown(markdown_content: str) -> Dict[str, Any]:
    front_matter, body = parse_front_matter(markdown_content)

    name = front_matter.get('name', '')
    description = front_matter.get('description', '')
    parameters_str = front_matter.get('parameters', '')
    enabled = front_matter.get('enabled', 'true').lower() == 'true'
    priority = int(front_matter.get('priority', 5))

    parameters = {}
    if parameters_str:
        try:
            import json
            parameters = json.loads(parameters_str)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse parameters JSON: {parameters_str}")

    return {
        "name": name,
        "description": description,
        "parameters": parameters,
        "enabled": enabled,
        "priority": priority,
        "content": body.strip()
    }


def load_skill_from_db(skill_data: Dict[str, Any]) -> Dict[str, Any]:
    md_content = skill_data.get('markdown', '')
    if not md_content:
        return skill_data

    parsed = parse_skill_markdown(md_content)
    skill_data.update(parsed)
    return skill_data
