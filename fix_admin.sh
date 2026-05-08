#!/bin/bash
echo "Fixing admin errors..."

# Fix portfolio/admin.py
python3 << 'PYFIX'
import re

# Fix SkillAdmin
with open('apps/portfolio/admin.py', 'r') as f:
    content = f.read()

# Fix SkillAdmin list_display
content = content.replace(
    "list_display = ('name', 'category', 'proficiency_bar', 'level', 'is_featured', 'order')",
    "list_display = ('name', 'category', 'proficiency_bar', 'proficiency', 'level', 'is_featured', 'order')"
)

# Fix ProjectAdmin list_display  
content = content.replace(
    "list_display = (\n        'title', 'project_type', 'status_badge', 'is_featured',\n        'is_published', 'technologies_list', 'created_at'\n    )",
    "list_display = (\n        'title', 'project_type', 'status', 'status_badge', 'is_featured',\n        'is_published', 'technologies_list', 'created_at'\n    )"
)

with open('apps/portfolio/admin.py', 'w') as f:
    f.write(content)

print("✅ portfolio/admin.py fixed")

PYFIX

# Fix blog/admin.py
python3 << 'PYFIX'
with open('apps/blog/admin.py', 'r') as f:
    content = f.read()

# Fix PostAdmin list_display
content = content.replace(
    "list_display = (\n        'title', 'author', 'category', 'status_badge',",
    "list_display = (\n        'title', 'author', 'category', 'status', 'status_badge',"
)

with open('apps/blog/admin.py', 'w') as f:
    f.write(content)

print("✅ blog/admin.py fixed")
PYFIX

echo "✅ All admin files fixed!"
