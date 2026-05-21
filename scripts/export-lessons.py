#!/usr/bin/env python3
"""
Extract all lessons from curs.html and export as Markdown.
Usage: python3 scripts/export-lessons.py
Outputs:
  - exports/all-lessons.md (single file with all modules)
  - exports/module-N.md (one file per module)
"""

import re
import os
import sys
from pathlib import Path
from html import unescape

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'curs.html'
OUT_DIR = ROOT / 'exports'

def html_to_markdown(html: str) -> str:
    s = html

    # Block-level boxes (must run before <div> stripping)
    s = re.sub(r'<div class="highlight-box"[^>]*>(.*?)</div>', r'\n> 💡 \1\n', s, flags=re.DOTALL)
    s = re.sub(r'<div class="warning-box"[^>]*>(.*?)</div>', r'\n> ⚠️ \1\n', s, flags=re.DOTALL)
    s = re.sub(r'<div class="success-box"[^>]*>(.*?)</div>', r'\n> ✓ \1\n', s, flags=re.DOTALL)

    # Prompt box: convert label + content to a code block
    def prompt_box(m):
        inner = m.group(1)
        label_match = re.search(r'<span class="prompt-copy-label">(.*?)</span>', inner)
        label = label_match.group(1) if label_match else 'PROMPT'
        body = re.sub(r'<span class="prompt-copy-label">.*?</span>', '', inner)
        body = re.sub(r'<span class="fill-in">(.*?)</span>', r'\1', body, flags=re.DOTALL)
        body = re.sub(r'<br\s*/?>', '\n', body)
        body = re.sub(r'<[^>]+>', '', body).strip()
        return f'\n```\n[{label}]\n{body}\n```\n'
    s = re.sub(r'<div class="prompt-box"[^>]*>(.*?)</div>', prompt_box, s, flags=re.DOTALL)

    # Exercise blocks: just title + content
    def exercise_block(m):
        inner = m.group(1)
        label_match = re.search(r'<span class="exercise-label">(.*?)</span>', inner)
        label = label_match.group(1) if label_match else 'Exercise'
        body = re.sub(r'<span class="exercise-label">.*?</span>', '', inner)
        return f'\n### {label}\n{body}\n'
    s = re.sub(r'<div class="exercise-block"[^>]*>(.*?)</div>', exercise_block, s, flags=re.DOTALL)

    # Diagnostic cards with <details>
    def diag_card(m):
        inner = m.group(1)
        prompt_m = re.search(r'<div class="diagnostic-prompt">(.*?)</div>', inner, flags=re.DOTALL)
        details_m = re.search(r'<details>(.*?)</details>', inner, flags=re.DOTALL)
        prompt_text = prompt_m.group(1).strip() if prompt_m else ''
        details_text = details_m.group(1) if details_m else ''
        details_text = re.sub(r'<summary>(.*?)</summary>', r'**\1**', details_text, flags=re.DOTALL)
        return f'\n**Prompt:** {prompt_text}\n{details_text}\n'
    s = re.sub(r'<div class="diagnostic-card"[^>]*>(.*?)</div>', diag_card, s, flags=re.DOTALL)

    # Tab labels
    s = re.sub(r'<p class="tab-label">(.*?)</p>', r'\n**\1**\n', s, flags=re.DOTALL)

    # Steps-list items: just convert to numbered/bulleted
    def step_item(m):
        inner = m.group(1)
        num_m = re.search(r'<div class="step-num">(.*?)</div>', inner, flags=re.DOTALL)
        content_m = re.search(r'<div class="step-content">(.*?)</div>', inner, flags=re.DOTALL)
        num = num_m.group(1).strip() if num_m else '•'
        content = content_m.group(1) if content_m else ''
        h4_m = re.search(r'<h4>(.*?)</h4>', content, flags=re.DOTALL)
        p_m = re.search(r'<p>(.*?)</p>', content, flags=re.DOTALL)
        title = h4_m.group(1).strip() if h4_m else ''
        desc = p_m.group(1).strip() if p_m else ''
        return f'\n**{num}. {title}** — {desc}\n'
    s = re.sub(r'<div class="step-item"[^>]*>(.*?)</div>(?=\s*</?div)', step_item, s, flags=re.DOTALL)

    # Formula box items
    def formula_item(m):
        inner = m.group(1)
        num_m = re.search(r'<div class="fi-num">(.*?)</div>', inner, flags=re.DOTALL)
        title_m = re.search(r'<div class="fi-title">(.*?)</div>', inner, flags=re.DOTALL)
        desc_m = re.search(r'<div class="fi-desc">(.*?)</div>', inner, flags=re.DOTALL)
        num = num_m.group(1).strip() if num_m else ''
        title = title_m.group(1).strip() if title_m else ''
        desc = desc_m.group(1).strip() if desc_m else ''
        return f'\n**{num}** — {title}: {desc}\n'
    s = re.sub(r'<div class="formula-item"[^>]*>(.*?)</div>(?=\s*</?div)', formula_item, s, flags=re.DOTALL)

    # Tool cards
    def tool_card(m):
        inner = m.group(1)
        h4_m = re.search(r'<h4>(.*?)</h4>', inner, flags=re.DOTALL)
        p_m = re.search(r'<p>(.*?)</p>', inner, flags=re.DOTALL)
        title = h4_m.group(1).strip() if h4_m else ''
        desc = p_m.group(1).strip() if p_m else ''
        return f'\n- **{title}** — {desc}\n'
    s = re.sub(r'<div class="tool-card"[^>]*>(.*?)</div>(?=\s*</?div)', tool_card, s, flags=re.DOTALL)

    # Compare grid
    def compare_item(m):
        cls = m.group(1)
        inner = m.group(2)
        label_m = re.search(r'<span class="compare-label">(.*?)</span>', inner, flags=re.DOTALL)
        label = label_m.group(1).strip() if label_m else cls
        body = re.sub(r'<span class="compare-label">.*?</span>', '', inner).strip()
        return f'\n**{label}:** {body}\n'
    s = re.sub(r'<div class="compare-item (\w+)"[^>]*>(.*?)</div>', compare_item, s, flags=re.DOTALL)

    # Headers and inline
    s = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', s, flags=re.DOTALL)
    s = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', s, flags=re.DOTALL)
    s = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n**\1**\n', s, flags=re.DOTALL)
    s = re.sub(r'<strong>(.*?)</strong>', r'**\1**', s, flags=re.DOTALL)
    s = re.sub(r'<em>(.*?)</em>', r'*\1*', s, flags=re.DOTALL)
    s = re.sub(r'<code>(.*?)</code>', r'`\1`', s, flags=re.DOTALL)

    # Lists
    s = re.sub(r'<li>(.*?)</li>', r'- \1', s, flags=re.DOTALL)
    s = re.sub(r'</?ul[^>]*>', '\n', s)
    s = re.sub(r'</?ol[^>]*>', '\n', s)
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = re.sub(r'</?p[^>]*>', '\n\n', s)

    # Strip remaining tags
    s = re.sub(r'<[^>]+>', '', s)

    # Decode HTML entities
    s = unescape(s)

    # Cleanup whitespace
    s = re.sub(r'\n{3,}', '\n\n', s)
    s = re.sub(r'[ \t]+', ' ', s)
    s = '\n'.join(line.rstrip() for line in s.split('\n'))

    return s.strip()


def extract_lessons():
    src = SOURCE.read_text()
    # Find the curriculum array between `const curriculum = [` and `];`
    match = re.search(r'const curriculum = \[(.*?)\n\];', src, re.DOTALL)
    if not match:
        print('ERROR: could not find curriculum array')
        sys.exit(1)
    curriculum_src = match.group(1)

    # Extract modules: { id: N, title: "...", sub: "...", lessons: [ ... ] }
    modules = []
    # Match each module block
    module_pattern = re.compile(
        r'\{\s*id:\s*(\d+),\s*title:\s*"([^"]+)",\s*sub:\s*"([^"]+)",\s*lessons:\s*\[(.*?)\n\s*\]\s*\}',
        re.DOTALL
    )
    for m in module_pattern.finditer(curriculum_src):
        mod_id, mod_title, mod_sub, lessons_src = m.groups()
        # Extract each lesson within
        lesson_pattern = re.compile(
            r'\{\s*id:\s*"([^"]+)",\s*title:\s*"([^"]+)",\s*duration:\s*"([^"]+)",\s*body:\s*`(.*?)`(?:\s*,\s*quiz:\s*(\{.*?\}))?\s*\}',
            re.DOTALL
        )
        lessons = []
        for lm in lesson_pattern.finditer(lessons_src):
            lid, ltitle, lduration, lbody, lquiz = lm.groups()
            lessons.append({
                'id': lid,
                'title': ltitle,
                'duration': lduration,
                'body': lbody,
                'quiz': lquiz,
            })
        modules.append({
            'id': int(mod_id),
            'title': mod_title,
            'sub': mod_sub,
            'lessons': lessons,
        })
    return modules


def format_module(mod):
    out = []
    out.append(f'# Modulul {mod["id"]} — {mod["title"]}')
    out.append(f'*{mod["sub"]}*\n')
    for lesson in mod['lessons']:
        out.append(f'\n---\n')
        out.append(f'## Lecția {lesson["id"]} — {lesson["title"]}')
        out.append(f'**Durată:** {lesson["duration"]}\n')
        out.append(html_to_markdown(lesson['body']))
        if lesson.get('quiz'):
            out.append(f'\n### Quiz\n')
            # Extract quiz fields with a simpler regex
            q_match = re.search(r'q:\s*"([^"]+)"', lesson['quiz'])
            opts_match = re.search(r'opts:\s*\[(.*?)\]', lesson['quiz'], re.DOTALL)
            correct_match = re.search(r'correct:\s*(\d+)', lesson['quiz'])
            if q_match:
                out.append(f'**Întrebare:** {q_match.group(1)}')
            if opts_match:
                opts = re.findall(r'"([^"]+)"', opts_match.group(1))
                correct_idx = int(correct_match.group(1)) if correct_match else -1
                for i, opt in enumerate(opts):
                    marker = '✓' if i == correct_idx else '○'
                    out.append(f'- {marker} {opt}')
    return '\n'.join(out)


def main():
    OUT_DIR.mkdir(exist_ok=True)
    modules = extract_lessons()
    print(f'Found {len(modules)} modules with {sum(len(m["lessons"]) for m in modules)} lessons')

    # Per-module exports
    for mod in modules:
        path = OUT_DIR / f'module-{mod["id"]}.md'
        path.write_text(format_module(mod))
        print(f'  Wrote {path.name} ({len(mod["lessons"])} lessons)')

    # Combined export
    combined = '\n\n'.join(format_module(m) for m in modules)
    path = OUT_DIR / 'all-lessons.md'
    path.write_text(combined)
    print(f'  Wrote {path.name} ({len(combined.splitlines())} lines)')

    print('\n✓ Done. Files in:', OUT_DIR)


if __name__ == '__main__':
    main()
