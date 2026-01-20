
import re

def check_template(filepath):
    print(f"Checking {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    stack = []
    # Regex to capture tags like {% if ... %}, {% endif %}, {% for ... %}, {% endfor %}, {% block ... %}, {% endblock %}
    # We carefully ignore variables {{ ... }} and comments {# ... #}
    tag_pattern = re.compile(r'{%\s*(\w+)(?:\s+[^%]+)?\s*%}')

    # Tags that open a block
    open_tags = {'if', 'for', 'block', 'with', 'while', 'autoescape', 'filter', 'spaceless', 'comment', 'cache'}
    # Tags that close a block
    close_tags = {'endif', 'endfor', 'endblock', 'endwith', 'endwhile', 'endautoescape', 'endfilter', 'endspaceless', 'endcomment', 'endcache'}
    
    # Mapping
    pair_map = {
        'endif': 'if',
        'endfor': 'for',
        'endblock': 'block',
        'endwith': 'with',
        'endwhile': 'while',
        'endautoescape': 'autoescape',
        'endfilter': 'filter',
        'endspaceless': 'spaceless',
        'endcomment': 'comment',
        'endcache': 'cache'
    }

    for i, line in enumerate(lines):
        line_num = i + 1
        matches = tag_pattern.finditer(line)
        for match in matches:
            tag_name = match.group(1)
            
            # Special case: {% else %} and {% elif %} check
            if tag_name in ['else', 'elif']:
                if not stack:
                    print(f"ERROR: Line {line_num}: Unexpected '{tag_name}' at top level")
                elif stack[-1][0] not in ['if', 'for', 'changed']: # 'for' for 'empty' clause, but 'else' works for 'for' too
                     # Note: 'changed' is not a standard block tag that uses else/elif usually, but let's stick to if/for
                     if stack[-1][0] == 'if':
                         pass # OK
                     elif stack[-1][0] == 'for' and tag_name == 'else':
                         pass # OK
                     else:
                         print(f"WARNING: Line {line_num}: '{tag_name}' found inside '{stack[-1][0]}' block")
                continue

            if tag_name in open_tags:
                stack.append((tag_name, line_num))
                # print(f"DEBUG: Line {line_num}: Opened {tag_name}")
            elif tag_name in close_tags:
                if not stack:
                    print(f"ERROR: Line {line_num}: Unexpected {tag_name} (Stack empty)")
                    return
                
                last_tag, start_line = stack.pop()
                expected_open = pair_map.get(tag_name)
                
                if last_tag != expected_open:
                    print(f"ERROR: Line {line_num}: Found {tag_name}, but expected closing for '{last_tag}' (opened at line {start_line})")
                    # Put it back to show we are still inside the previous one? 
                    # No, usually this means a mismatch order or missing tag.
                    # We'll stop here as this is likely the syntax error source.
                    return
                # print(f"DEBUG: Line {line_num}: Closed {tag_name} (opened at {start_line})")

    if stack:
        print("\n=== UNCLOSED TAGS REMAINING ===")
        for tag, line in stack:
            print(f"Tag '{tag}' opened at line {line} is not closed.")

check_template(r'c:\Users\sucol\OneDrive\Escritorio\segurov2\templates\claims\claim_detail.html')
