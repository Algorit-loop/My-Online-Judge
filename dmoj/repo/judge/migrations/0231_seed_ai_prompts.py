from django.db import migrations


_PROMPTS = [
    {
        'key': 'ai_problem_creator',
        'name': 'AI Problem Creator',
        'prompt_text': (
            'You are an expert at reading competitive programming problem statements from images or PDFs.\n'
            '\n'
            'Extract the problem content and return it as clean Markdown suitable for an Online Judge website.\n'
            '\n'
            'The output MUST follow this exact structure:\n'
            '\n'
            '<problem statement here \u2014 describe the problem clearly>\n'
            '\n'
            '## **Input**\n'
            '\n'
            '<describe input format, constraints inline>\n'
            '\n'
            '## **Output**\n'
            '\n'
            '<describe output format>\n'
            '\n'
            '## **Scoring**\n'
            '\n'
            '| Subtask | Score | Additional Constraints |\n'
            '| ------- | ----- | ---------------------- |\n'
            '| ~1~     | ~...~ | ~constraints~          |\n'
            '\n'
            '(If there is no subtask/scoring info, omit this section entirely.)\n'
            '\n'
            '## **Example**\n'
            '\n'
            '### **Sample input 1**\n'
            '```\n'
            '<sample input>\n'
            '```\n'
            '\n'
            '### **Sample output 1**\n'
            '```\n'
            '<sample output>\n'
            '```\n'
            '\n'
            '(Include ALL sample test cases from the problem.)\n'
            '\n'
            '### **Explanation**\n'
            '\n'
            '<explanation of sample, if provided in the original problem>\n'
            '\n'
            'Formatting rules:\n'
            '- Use ~variable~ for inline math (NOT $variable$). Example: ~N~, ~1 \\\\leq N \\\\leq 10^6~, ~O(N \\\\log N)~.\n'
            '- Use standard Markdown: **bold**, tables with |, code blocks with ```.\n'
            '- Keep the original problem\'s meaning exactly. Do not add or remove information.\n'
            '- Output language: {output_language}.\n'
            '- Return ONLY the markdown content. No extra commentary, no wrapping in code fences.'
        ),
        'description': (
            'System prompt for AI Problem Creator. Extracts problem statements from images/PDFs into Markdown.\n'
            '\n'
            'Available variables:\n'
            '- {output_language} — the language for the output (e.g. "English", "Vietnamese")'
        ),
    },
    {
        'key': 'ai_code_review',
        'name': 'AI Code Review',
        'prompt_text': (
            'You are an expert competitive programming analyst.\n'
            'Analyze the following code submission.\n'
            '\n'
            'Problem: "{problem_name}"\n'
            'Language: {language_name}\n'
            'Submission result: {result} ({points}/{total_points} points)\n'
            '\n'
            'Provide analysis covering:\n'
            '1. Algorithm & Data Structures - identify the main algorithm used\n'
            '2. Execution Flow - step-by-step explanation of how the code works\n'
            '3. Time Complexity - with justification\n'
            '4. Space Complexity - with justification\n'
            '5. Code Quality - readability, edge cases, potential improvements\n'
            '\n'
            'Output in plain text format. Do NOT use markdown formatting, HTML, or code blocks.\n'
            'Use simple text formatting: headers with "===", lists with "- ", indentation for structure.\n'
            '\n'
            'Output language: {output_language}'
        ),
        'description': (
            'System prompt for AI Code Review. Analyzes submission code.\n'
            '\n'
            'Available variables:\n'
            '- {problem_name} — name of the problem\n'
            '- {language_name} — programming language\n'
            '- {result} — submission result (AC, WA, TLE, etc.)\n'
            '- {points} — points scored\n'
            '- {total_points} — total possible points\n'
            '- {output_language} — output language (e.g. "Vietnamese", "English")'
        ),
    },
    {
        'key': 'api_key_test',
        'name': 'API Key Test',
        'prompt_text': 'Reply exactly: OK',
        'description': (
            'Simple prompt used to test if an API key is valid.\n'
            'Should be very short — response is limited to 5 tokens.\n'
            '\n'
            'No variables available.'
        ),
    },
]


def seed_prompts(apps, schema_editor):
    AIPromptTemplate = apps.get_model('judge', 'AIPromptTemplate')
    for prompt_data in _PROMPTS:
        AIPromptTemplate.objects.get_or_create(
            key=prompt_data['key'],
            defaults=prompt_data,
        )


def unseed_prompts(apps, schema_editor):
    AIPromptTemplate = apps.get_model('judge', 'AIPromptTemplate')
    AIPromptTemplate.objects.filter(key__in=[p['key'] for p in _PROMPTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0230_ai_prompt_template'),
    ]

    operations = [
        migrations.RunPython(seed_prompts, unseed_prompts),
    ]
