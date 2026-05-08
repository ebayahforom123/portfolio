from django.test import TestCase, Client
from django.urls import reverse
from apps.portfolio.models import Project, Skill, SkillCategory
from datetime import date


class HomeViewTest(TestCase):
    """Test home view"""

    def setUp(self):
        self.client = Client()

        # Create test projects
        for i in range(5):
            Project.objects.create(
                title=f'Project {i}',
                short_description=f'Description {i}',
                description=f'Detailed description {i}',
                is_published=True,
                is_featured=(i < 3),
                start_date=date(2023, 1, 1),
                end_date=date(2023, 12, 31)
            )

    def test_home_view_status_code(self):
        """Test home page returns 200"""
        response = self.client.get(reverse('portfolio:home'))
        self.assertEqual(response.status_code, 200)

    def test_home_view_template(self):
        """Test home view uses correct template"""
        response = self.client.get(reverse('portfolio:home'))
        self.assertTemplateUsed(response, 'pages/home.html')

    def test_home_view_context(self):
        """Test home view context data"""
        response = self.client.get(reverse('portfolio:home'))
        self.assertIn('featured_projects', response.context)
        self.assertIn('stats', response.context)
        self.assertEqual(len(response.context['featured_projects']), 3)

    def test_home_view_stats(self):
        """Test stats calculation"""
        response = self.client.get(reverse('portfolio:home'))
        stats = response.context['stats']
        self.assertEqual(stats['projects_count'], 5)


class ProjectListViewTest(TestCase):
    """Test project list view"""

    def setUp(self):
        self.client = Client()

        # Create test projects
        for i in range(15):
            Project.objects.create(
                title=f'Project {i}',
                short_description=f'Description {i}',
                description=f'Detailed description {i}',
                is_published=True,
                is_featured=(i < 5),
                start_date=date(2023, 1, 1),
                end_date=date(2023, 12, 31)
            )

    def test_project_list_view(self):
        """Test project list page"""
        response = self.client.get(reverse('portfolio:projects'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/projects.html')

    def test_project_list_pagination(self):
        """Test pagination"""
        response = self.client.get(reverse('portfolio:projects'))
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['projects']), 9)  # paginate_by=9

    def test_project_list_second_page(self):
        """Test second page of pagination"""
        response = self.client.get(reverse('portfolio:projects') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['projects']), 6)  # Remaining 6 items

    def test_project_search(self):
        """Test search functionality"""
        response = self.client.get(
            reverse('portfolio:projects') + '?q=Project+5'
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.context['projects']), 1)


class ProjectDetailViewTest(TestCase):
    """Test project detail view"""

    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(
            title='Test Project',
            short_description='A test project',
            description='Detailed description',
            is_published=True,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )

    def test_project_detail_view(self):
        """Test project detail page"""
        response = self.client.get(
            reverse('portfolio:project_detail', kwargs={'slug': self.project.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/project_detail.html')

    def test_project_detail_404(self):
        """Test 404 for non-existent project"""
        response = self.client.get(
            reverse('portfolio:project_detail', kwargs={'slug': 'non-existent'})
        )
        self.assertEqual(response.status_code, 404)

    def test_project_view_count_increment(self):
        """Test view count increments"""
        initial_count = self.project.view_count
        self.client.get(
            reverse('portfolio:project_detail', kwargs={'slug': self.project.slug})
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.view_count, initial_count + 1)


class ContactViewTest(TestCase):
    """Test contact view"""

    def setUp(self):
        self.client = Client()

    def test_contact_view_get(self):
        """Test contact page GET"""
        response = self.client.get(reverse('portfolio:contact'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/contact.html')
        self.assertIn('form', response.context)

    def test_contact_view_post_valid(self):
        """Test contact form POST with valid data"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'subject': 'Test Subject',
            'message': 'This is a test message that is long enough',
        }
        response = self.client.post(
            reverse('portfolio:contact'),
            data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thank you')

    def test_contact_view_post_invalid(self):
        """Test contact form POST with invalid data"""
        data = {
            'name': 'J',
            'email': 'invalid-email',
            'subject': '',
            'message': 'Short',
        }
        response = self.client.post(reverse('portfolio:contact'), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)


class AboutViewTest(TestCase):
    """Test about view"""

    def setUp(self):
        self.client = Client()

    def test_about_view(self):
        """Test about page"""
        response = self.client.get(reverse('portfolio:about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/about.html')

    def test_about_view_context(self):
        """Test about page context"""
        response = self.client.get(reverse('portfolio:about'))
        self.assertIn('experiences', response.context)
        self.assertIn('education_list', response.context)
        self.assertIn('skill_categories', response.context)


class SearchViewTest(TestCase):
    """Test search view"""

    def setUp(self):
        self.client = Client()

        # Create test data
        Project.objects.create(
            title='Django Project',
            short_description='A Django web application',
            description='Detailed Django project description',
            is_published=True
        )

        Project.objects.create(
            title='React App',
            short_description='A React application',
            description='Detailed React project description',
            is_published=True
        )

    def test_search_view(self):
        """Test search functionality"""
        response = self.client.get(
            reverse('portfolio:search') + '?q=Django'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/search_results.html')
        self.assertIn('projects', response.context)
        self.assertEqual(len(response.context['projects']), 1)

    def test_search_no_results(self):
        """Test search with no results"""
        response = self.client.get(
            reverse('portfolio:search') + '?q=nonexistent'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['projects']), 0)