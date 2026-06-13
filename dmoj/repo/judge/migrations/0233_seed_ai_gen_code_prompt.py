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
        'The total number of testcases is N (you do NOT know N, but assume N ~ {num_cases}).\n'
        'If the problem defines subtasks with score percentages, you MUST distribute testcases proportionally by score.\n'
        '\n'
        'Example: 4 subtasks with scores 10%, 30%, 30%, 30% and N=20:\n'
        '  - Subtask 1 (10%) -> 2 testcases: T=1..2\n'
        '  - Subtask 2 (30%) -> 6 testcases: T=3..8\n'
        '  - Subtask 3 (30%) -> 6 testcases: T=9..14\n'
        '  - Subtask 4 (30%) -> 6 testcases: T=15..20\n'
        '\n'
        'Implementation pattern — compute subtask boundaries from percentages:\n'
        '  const int N_TOTAL = {num_cases};\n'
        '  // scores[] = percentage of each subtask from problem description\n'
        '  // Compute prefix-sum boundaries, then: if (T <= boundary[0]) subtask 1; else if (T <= boundary[1]) subtask 2; ...\n'
        '\n'
        'Rules:\n'
        '- For each subtask, generate inputs at or near the MAXIMUM allowed constraints of that subtask.\n'
        '- If a subtask has special properties (e.g., "all elements are equal", "tree is a chain"), the generated input MUST satisfy those properties.\n'
        '- Each testcase within a subtask should be different (use T as random seed).\n'
        '- The last (hardest) subtask range extends to cover any remaining T values beyond N_TOTAL.\n'
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
        '=== VALIDATION ===\n'
        'Before generating code, verify the problem description is a COMPLETE competitive programming problem with:\n'
        '- A clear problem statement\n'
        '- Input format specification\n'
        '- Output format specification\n'
        '- Constraints (value ranges, sizes, etc.)\n'
        'If ANY of these are missing or the description is not a valid problem, respond with ONLY:\n'
        '  ERROR: <reason why the description is invalid>\n'
        'Do NOT generate code for invalid or incomplete problems. Do NOT invent constraints that are not stated.\n'
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
        'Testcases are distributed across subtasks proportionally by score percentage.\n'
        '\n'
        'Available variables:\n'
        '- {problem_description} \u2014 the full problem description (markdown)\n'
        '- {num_cases} \u2014 the total number of testcases to generate'
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
