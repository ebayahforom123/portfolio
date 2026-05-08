from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.portfolio.models import (
    Project, Skill, SkillCategory, Technology,
    Experience, Education, Testimonial, Service
)
from datetime import date, timedelta


class ProjectModelTest(TestCase):
    """Test Project model"""

    def setUp(self):
        self.project = Project.objects.create(
            title='Test Project',
            short_description='A test project',
            description='Detailed description of test project',
            status='completed',
            is_published=True,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 6, 30)
        )

    def test_project_creation(self):
        """Test project is created correctly"""
        self.assertEqual(self.project.title, 'Test Project')
        self.assertTrue(self.project.slug)
        self.assertTrue(self.project.uuid)

    def test_slug_auto_generation(self):
        """Test slug is automatically generated"""
        self.project.save()
        self.assertEqual(self.project.slug, 'test-project')

    def test_get_absolute_url(self):
        """Test absolute URL generation"""
        url = self.project.get_absolute_url()
        self.assertIn(self.project.slug, url)

    def test_get_duration(self):
        """Test project duration calculation"""
        duration = self.project.get_duration()
        self.assertIsNotNone(duration)
        self.assertIn('6 months', duration)

    def test_project_is_ongoing(self):
        """Test ongoing project"""
        ongoing_project = Project.objects.create(
            title='Ongoing Project',
            short_description='An ongoing project',
            description='Description',
            is_ongoing=True,
            is_published=True,
            start_date=date(2023, 1, 1)
        )
        self.assertTrue(ongoing_project.is_ongoing)
        self.assertIsNone(ongoing_project.end_date)

    def test_increment_view_count(self):
        """Test view count increment"""
        initial_views = self.project.view_count
        self.project.increment_view_count()
        self.project.refresh_from_db()
        self.assertEqual(self.project.view_count, initial_views + 1)


class SkillModelTest(TestCase):
    """Test Skill model"""

    def setUp(self):
        self.category = SkillCategory.objects.create(
            name='Backend',
            order=1
        )
        self.skill = Skill.objects.create(
            name='Python',
            category=self.category,
            proficiency=90,
            level='expert',
            years_of_experience=5
        )

    def test_skill_creation(self):
        """Test skill creation"""
        self.assertEqual(self.skill.name, 'Python')
        self.assertEqual(self.skill.category.name, 'Backend')
        self.assertEqual(self.skill.proficiency, 90)

    def test_proficiency_validation(self):
        """Test proficiency validation"""
        with self.assertRaises(ValidationError):
            skill = Skill(
                name='Invalid',
                category=self.category,
                proficiency=150
            )
            skill.full_clean()

    def test_get_proficiency_class(self):
        """Test proficiency CSS class"""
        self.assertEqual(self.skill.get_proficiency_class(), 'expert')

        self.skill.proficiency = 80
        self.assertEqual(self.skill.get_proficiency_class(), 'advanced')

        self.skill.proficiency = 60
        self.assertEqual(self.skill.get_proficiency_class(), 'intermediate')

        self.skill.proficiency = 40
        self.assertEqual(self.skill.get_proficiency_class(), 'beginner')


class ExperienceModelTest(TestCase):
    """Test Experience model"""

    def setUp(self):
        self.experience = Experience.objects.create(
            company='Tech Corp',
            position='Senior Developer',
            employment_type='full_time',
            description='Worked on various projects',
            start_date=date(2020, 1, 1),
            is_current=True
        )

    def test_experience_creation(self):
        """Test experience creation"""
        self.assertEqual(self.experience.company, 'Tech Corp')
        self.assertTrue(self.experience.is_current)

    def test_current_experience_end_date(self):
        """Test current experience has no end date"""
        self.assertIsNone(self.experience.end_date)

    def test_get_duration_display(self):
        """Test duration display"""
        display = self.experience.get_duration_display()
        self.assertIn('Jan 2020', display)
        self.assertIn('Present', display)

    def test_achievements_list(self):
        """Test achievements parsing"""
        self.experience.achievements = 'Achievement 1\nAchievement 2\nAchievement 3'
        achievements = self.experience.get_achievements_list()
        self.assertEqual(len(achievements), 3)
        self.assertEqual(achievements[0], 'Achievement 1')


class EducationModelTest(TestCase):
    """Test Education model"""

    def setUp(self):
        self.education = Education.objects.create(
            institution='University of Technology',
            degree='Bachelor of Science',
            degree_type='bachelor',
            field_of_study='Computer Science',
            start_date=date(2016, 9, 1),
            end_date=date(2020, 6, 30),
            gpa=3.8
        )

    def test_education_creation(self):
        """Test education creation"""
        self.assertEqual(self.education.institution, 'University of Technology')
        self.assertEqual(self.education.gpa, 3.8)

    def test_get_duration_display(self):
        """Test duration display"""
        display = self.education.get_duration_display()
        self.assertIn('2016', display)
        self.assertIn('2020', display)


class TestimonialModelTest(TestCase):
    """Test Testimonial model"""

    def setUp(self):
        self.testimonial = Testimonial.objects.create(
            client_name='John Doe',
            client_title='CEO, Tech Inc',
            content='Great work!',
            rating=5
        )

    def test_testimonial_creation(self):
        """Test testimonial creation"""
        self.assertEqual(self.testimonial.client_name, 'John Doe')
        self.assertEqual(self.testimonial.rating, 5)

    def test_rating_validation(self):
        """Test rating validation"""
        with self.assertRaises(ValidationError):
            testimonial = Testimonial(
                client_name='Jane',
                content='Test',
                rating=10
            )
            testimonial.full_clean()

    def test_get_stars(self):
        """Test star rating"""
        stars = self.testimonial.get_stars()
        self.assertEqual(len(list(stars)), 5)