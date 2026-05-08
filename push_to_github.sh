#!/bin/bash

echo "🚀 Pushing portfolio to GitHub..."

# Initialize git
git init

# Add all files
git add .

# Check status
echo ""
echo "Files to be committed:"
git status --short

# Commit
git commit -m "🎉 Initial commit: Django Portfolio Website

- Complete portfolio with Django backend
- Skills, Projects, Experience sections
- Contact form with validation
- Responsive design with Bootstrap 5
- SEO optimized
- Clean and modern UI"

# Add remote
git remote add origin https://github.com/ebayahforom123/portfolio.git 2>/dev/null || echo "Remote already exists"

# Push
git branch -M main
git push -u origin main

echo ""
echo "✅ Successfully pushed to GitHub!"
echo "🌐 Visit: https://github.com/ebayahforom123/portfolio"
