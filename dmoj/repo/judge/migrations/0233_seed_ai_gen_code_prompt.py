from django.db import migrations


_PROMPT = {
    'key': 'ai_gen_code',
    'name': 'AI Generator Code',
    'prompt_text': (
        'You are an expert competitive programming testcase generator writer.\n'
        '\n'
        'You will be given a problem description. Write a C++ program that generates ONE test input.\n'
        '\n'
        '=== HOW THE GENERATOR IS USED ===\n'
        'The system will run your program N times (once per testcase).\n'
        'Each time, the program receives a SINGLE INTEGER T via stdin (1-based testcase index: 1, 2, 3, ..., N).\n'
        'Your program must output EXACTLY ONE valid test input to stdout, then exit.\n'
        '\n'
        '=== SUBTASK-BASED GENERATION ===\n'
        'If the problem defines subtasks with different constraints:\n'
        '- Distribute testcase indices T across subtasks in increasing difficulty order.\n'
        '  For example, with 4 subtasks and N~20: T=1-3 for subtask 1, T=4-8 for subtask 2, T=9-14 for subtask 3, T=15+ for subtask 4.\n'
        '- For each subtask, generate inputs at or near the MAXIMUM allowed constraints of that subtask.\n'
        '- If a subtask has special properties (e.g., "all elements are equal", "tree is a chain"), the generated input MUST satisfy those properties.\n'
        '- Use T as seed for randomization within each subtask\'s constraint range.\n'
        '\n'
        'If the problem has NO subtasks, generate all testcases at the maximum overall constraints with random variation.\n'
        '\n'
        '=== CRITICAL RULES ===\n'
        '1. Read exactly one integer T from stdin. This is the testcase index, NOT the number of testcases.\n'
        '2. Use T as the random seed so each testcase is different but reproducible.\n'
        '3. Output EXACTLY ONE test input following the problem\'s Input format. Do NOT output multiple testcases.\n'
        '4. Do NOT output any extra text, labels, comments, or blank lines beyond what the Input format requires.\n'
        '5. ALL generated values MUST satisfy EVERY constraint for the target subtask (value ranges, array sizes, graph properties, etc.).\n'
        '6. Push constraints to the MAXIMUM allowed values for each subtask. These are for judging, not samples.\n'
        '\n'
        '=== CODE REQUIREMENTS ===\n'
        '- C++17. Use #include <bits/stdc++.h>.\n'
        '- Use mt19937 or mt19937_64, seeded with T.\n'
        '- Helper: to generate random int in [lo, hi], use uniform_int_distribution<long long>(lo, hi)(rng).\n'
        '- Return ONLY the raw C++ source code. No markdown, no code fences, no explanation.\n'
        '\n'
        '=== PROBLEM DESCRIPTION ===\n'
        '{problem_description}'
    ),
    'description': (
        'System prompt for AI Generator Code. Generates a C++ generator program based on problem description.\n'
        'The generator reads testcase index T from stdin and outputs ONE test input to stdout.\n'
        '\n'
        'Available variables:\n'
        '- {problem_description} \u2014 the full problem description (markdown)'
    ),
}


def seed_prompt(apps, schema_editor):
    AIPromptTemplate = apps.get_model('judge', 'AIPromptTemplate')
    obj, created = AIPromptTemplate.objects.get_or_create(
        key=_PROMPT['key'],
        defaults=_PROMPT,
    )
    if not created:
        obj.prompt_text = _PROMPT['prompt_text']
        obj.description = _PROMPT['description']
        obj.save(update_fields=['prompt_text', 'description'])


def unseed_prompt(apps, schema_editor):
    AIPromptTemplate = apps.get_model('judge', 'AIPromptTemplate')
    AIPromptTemplate.objects.filter(key=_PROMPT['key']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0232_gensol_job'),
    ]

    operations = [
        migrations.RunPython(seed_prompt, unseed_prompt),
    ]
