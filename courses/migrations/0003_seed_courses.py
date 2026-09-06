from django.db import migrations


def create_courses(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    
    courses = [
        {
            'title': 'Tajweed Mastery',
            'slug': 'tajweed',
            'description': 'Master the art of Quranic recitation with proper Tajweed rules. Learn from expert female instructors in a comfortable online environment.',
            'category': 'Quranic Studies',
            'level': 'intermediate',
            'duration': '8 weeks',
            'price': 0,
            'is_active': True,
        },
        {
            'title': 'Hifz Program',
            'slug': 'hifz',
            'description': 'Complete Quran memorization program with structured revision schedule, one-on-one guidance, and Ijazah certification.',
            'category': 'Quranic Studies',
            'level': 'advanced',
            'duration': '24 months',
            'price': 0,
            'is_active': True,
        },
        {
            'title': 'Nazra for Kids',
            'slug': 'nazra',
            'description': 'Beginner-friendly Quran reading course for children. Learn Arabic alphabet, letter connections, and read from the Quran with confidence.',
            'category': 'Quranic Studies',
            'level': 'beginner',
            'duration': '12 weeks',
            'price': 0,
            'is_active': True,
        },
    ]
    
    for data in courses:
        Course.objects.get_or_create(slug=data['slug'], defaults=data)


def remove_courses(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    Course.objects.filter(slug__in=['tajweed', 'hifz', 'nazra']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_enrollment'),
    ]

    operations = [
        migrations.RunPython(create_courses, remove_courses),
    ]
