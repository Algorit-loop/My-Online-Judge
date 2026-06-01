import base64
import json
import urllib.error
import urllib.request

from django.conf import settings
from django.utils.translation import gettext as _

from judge.models.api_key import AI_PROVIDER_CONFIGS, VISION_PROVIDERS

# Timeout for AI API calls (vision/PDF processing can be slow)
_AI_CREATE_TIMEOUT = 120

SYSTEM_PROMPT = """You are an expert at reading competitive programming problem statements (from images or PDFs) and converting them into structured JSON for an Online Judge system.

Extract all information from the problem and return ONLY a single JSON object matching this exact structure:

{
  "name": "Sum of Two Numbers",
  "description": "Given two integers $A$ and $B$, compute their sum.\n\n## Input\n\nThe first line contains two integers $A$ and $B$ ($1 \\le A, B \\le 10^9$).\n\n## Output\n\nPrint a single integer — the sum $A + B$.\n\n## Constraints\n\n- $1 \\le A, B \\le 10^9$\n\n## Examples\n\n### Input\n\n```\n3 5\n```\n\n### Output\n\n```\n8\n```",
  "time_limit": 1.0,
  "memory_limit": 256,
  "points": 10.0,
  "difficulty_label": "Easy",
  "problem_types": ["Implementation", "Math"],
  "sample_input": "3 5",
  "sample_output": "8"
}

Field rules:
- "name": problem title, max 100 characters.
- "description": full problem statement in Markdown. Must contain sections ## Input, ## Output, ## Constraints, ## Examples. Use LaTeX for math: $N$, $10^9+7$, $O(N \\log N)$. Include ALL sample test cases inside the description under ## Examples.
- "time_limit": float, seconds (e.g. 1.0, 2.0). Default 1.0 if not stated.
- "memory_limit": integer, MB (convert if needed: 262144 KB = 256 MB). Default 256 if not stated.
- "points": float 1–100, estimate difficulty (Easy≈10, Medium≈30, Hard≈60, Very Hard≈90).
- "difficulty_label": one of "Easy", "Medium", "Hard", "Very Hard".
- "problem_types": list of relevant tags from: Implementation, Math, DP, Graph, Greedy, Binary Search, Data Structures, String, Geometry, Number Theory, Combinatorics, Brute Force, Sorting, Two Pointers, BFS/DFS, Tree, Constructive.
- "sample_input": the first sample input as plain text, empty string if none.
- "sample_output": the first sample output as plain text, empty string if none.

Critical rules:
- Output ONLY the raw JSON object. No markdown fences, no explanation, no extra text before or after.
- Output language for "name" and "description": {output_language}."""


def get_system_prompt(output_language='English'):
    return SYSTEM_PROMPT.replace('{output_language}', output_language)


def validate_file(uploaded_file):
    """Validate uploaded file. Returns (is_valid, error_message)."""
    if not uploaded_file:
        return False, _('No file uploaded')

    ext = uploaded_file.name.rsplit('.', 1)[-1].lower() if '.' in uploaded_file.name else ''
    allowed_exts = getattr(settings, 'AI_PROBLEM_CREATOR_ALLOWED_EXTS', {'pdf', 'png', 'jpg', 'jpeg', 'webp'})
    if ext not in allowed_exts:
        return False, _('Invalid file type. Allowed: %s') % ', '.join(sorted(allowed_exts))

    max_size = getattr(settings, 'AI_PROBLEM_CREATOR_MAX_FILE_SIZE', 10 * 1024 * 1024)
    if uploaded_file.size > max_size:
        return False, _('File too large. Maximum size: %d MB') % (max_size // (1024 * 1024))

    return True, ''


def _get_mime_type(filename):
    """Get MIME type from filename."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    mime_map = {
        'pdf': 'application/pdf',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'webp': 'image/webp',
    }
    return mime_map.get(ext, 'application/octet-stream')


def _build_openai_payload(file_data_b64, mime_type, model, system_prompt):
    """Build OpenAI Responses API payload with file input."""
    if mime_type == 'application/pdf':
        input_content = [
            {'type': 'input_text', 'text': system_prompt},
            {
                'type': 'input_file',
                'file_data': f'data:{mime_type};base64,{file_data_b64}',
            },
        ]
    else:
        input_content = [
            {'type': 'input_text', 'text': system_prompt},
            {
                'type': 'input_image',
                'image_url': f'data:{mime_type};base64,{file_data_b64}',
            },
        ]
    return {
        'model': model,
        'input': input_content,
    }


def _build_gemini_payload(file_data_b64, mime_type, model, system_prompt):
    """Build Gemini API payload with inline_data."""
    return {
        'contents': [{
            'parts': [
                {'text': system_prompt},
                {
                    'inline_data': {
                        'mime_type': mime_type,
                        'data': file_data_b64,
                    },
                },
            ],
        }],
    }


def _build_claude_payload(file_data_b64, mime_type, model, system_prompt):
    """Build Claude API payload with image/document content blocks."""
    if mime_type == 'application/pdf':
        file_block = {
            'type': 'document',
            'source': {
                'type': 'base64',
                'media_type': mime_type,
                'data': file_data_b64,
            },
        }
    else:
        file_block = {
            'type': 'image',
            'source': {
                'type': 'base64',
                'media_type': mime_type,
                'data': file_data_b64,
            },
        }
    return {
        'model': model,
        'max_tokens': 4096,
        'messages': [{
            'role': 'user',
            'content': [
                file_block,
                {'type': 'text', 'text': system_prompt},
            ],
        }],
    }


_PAYLOAD_BUILDERS = {
    'openai': _build_openai_payload,
    'gemini': _build_gemini_payload,
    'claude': _build_claude_payload,
}


def _extract_text_from_response(provider, data):
    """Extract text content from provider-specific response format."""
    if provider == 'openai':
        # Responses API: data.output[].content[].text
        for item in data.get('output', []):
            for content in item.get('content', []):
                if content.get('type') == 'output_text':
                    return content.get('text', '')
        return ''
    elif provider == 'gemini':
        # Gemini: data.candidates[0].content.parts[0].text
        candidates = data.get('candidates', [])
        if candidates:
            parts = candidates[0].get('content', {}).get('parts', [])
            if parts:
                return parts[0].get('text', '')
        return ''
    elif provider == 'claude':
        # Claude: data.content[0].text
        content = data.get('content', [])
        if content:
            return content[0].get('text', '')
        return ''
    return ''


def _parse_json_from_text(text):
    """Parse JSON from text, handling markdown code fences."""
    text = text.strip()
    # Try direct parse
    try:
        return json.loads(text), None
    except json.JSONDecodeError:
        pass
    # Try extracting from code fences
    if '```' in text:
        parts = text.split('```')
        for i in range(1, len(parts), 2):
            block = parts[i]
            # Remove language identifier (e.g., "json\n")
            if block.startswith('json'):
                block = block[4:]
            block = block.strip()
            try:
                return json.loads(block), None
            except json.JSONDecodeError:
                continue
    return None, _('AI response is not valid JSON. Please try again.')


def _validate_problem_data(data):
    """Validate parsed problem data has required fields."""
    required_fields = ['name', 'description']
    for field in required_fields:
        if field not in data or not data[field]:
            return False, _('Missing required field: %s') % field

    # Sanitize and set defaults
    data.setdefault('time_limit', 1.0)
    data.setdefault('memory_limit', 256)
    data.setdefault('points', 10.0)
    data.setdefault('difficulty_label', 'Medium')
    data.setdefault('problem_types', [])
    data.setdefault('sample_input', '')
    data.setdefault('sample_output', '')

    # Type coercion
    try:
        data['time_limit'] = float(data['time_limit'])
    except (TypeError, ValueError):
        data['time_limit'] = 1.0
    try:
        data['memory_limit'] = int(data['memory_limit'])
    except (TypeError, ValueError):
        data['memory_limit'] = 256
    try:
        data['points'] = float(data['points'])
    except (TypeError, ValueError):
        data['points'] = 10.0

    # Clamp values
    data['time_limit'] = max(0.1, min(data['time_limit'], 30.0))
    data['memory_limit'] = max(16, min(data['memory_limit'], 1024))
    data['points'] = max(1.0, min(data['points'], 100.0))

    # Truncate name
    data['name'] = str(data['name'])[:100]

    if not isinstance(data['problem_types'], list):
        data['problem_types'] = []

    return True, ''


def call_ai_provider(provider, model, api_key, uploaded_file, output_language='English'):
    """
    Call the AI provider with the uploaded file and return parsed problem data.

    Returns (success, data_or_error):
        - (True, dict) on success
        - (False, str) on error
    """
    if provider not in VISION_PROVIDERS:
        return False, _('Provider "%s" does not support image/PDF input') % provider

    builder = _PAYLOAD_BUILDERS.get(provider)
    if not builder:
        return False, _('Unsupported provider')

    # Read and encode file
    file_content = uploaded_file.read()
    file_data_b64 = base64.b64encode(file_content).decode('ascii')
    mime_type = _get_mime_type(uploaded_file.name)

    system_prompt = get_system_prompt(output_language)
    payload = builder(file_data_b64, mime_type, model, system_prompt)

    # Build request
    config = AI_PROVIDER_CONFIGS[provider]
    url = config['base_url'] + config['endpoint']
    if '{model}' in url:
        url = url.replace('{model}', model)

    headers = {
        'Content-Type': 'application/json',
        config['auth_header']: config['auth_format'].format(key=api_key),
    }
    headers.update(config.get('extra_headers', {}))

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
    )

    try:
        with urllib.request.urlopen(req, timeout=_AI_CREATE_TIMEOUT) as resp:
            response_data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            error_body = json.loads(e.read())
            error_msg = error_body.get('error', {}).get('message', str(e))
        except Exception:
            error_msg = str(e)
        return False, _('API error (%d): %s') % (e.code, error_msg)
    except Exception as e:
        return False, _('Connection error: %s') % str(e)

    # Extract text from response
    text = _extract_text_from_response(provider, response_data)
    if not text:
        return False, _('Empty response from AI provider')

    return True, text


def parse_ai_response(text):
    """
    Parse AI response text into structured problem data.
    Returns (success, data_or_error).
    """
    parsed, error = _parse_json_from_text(text)
    if error:
        return False, error

    valid, error = _validate_problem_data(parsed)
    if not valid:
        return False, error

    return True, parsed
