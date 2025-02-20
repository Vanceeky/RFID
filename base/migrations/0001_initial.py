# Generated by Django 4.2.7 on 2023-11-24 13:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Adviser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar', models.ImageField(blank=True, default='/static/default_avatar.png', null=True, upload_to='avatars/')),
                ('contact_number', models.CharField(blank=True, max_length=15, null=True)),
                ('address', models.TextField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=30, null=True)),
                ('last_name', models.CharField(blank=True, max_length=30, null=True)),
                ('email', models.EmailField(blank=True, max_length=255, null=True)),
                ('address', models.CharField(blank=True, max_length=255, null=True)),
                ('contact_number', models.CharField(blank=True, max_length=15, null=True)),
                ('avatar', models.ImageField(blank=True, default='/static/default_avatar.png', null=True, upload_to='student_avatars/')),
                ('student_id', models.CharField(max_length=12, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='StudentClassification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.CharField(choices=[('1st', '1st Year'), ('2nd', '2nd Year'), ('3rd', '3rd Year'), ('4th', '4th Year')], max_length=3)),
                ('block', models.CharField(choices=[('A', 'Block A'), ('B', 'Block B'), ('C', 'Block C')], default='A', max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('time_in_grace_period_minutes', models.PositiveIntegerField(default=0, help_text='Time in grace period for attendance in minutes')),
                ('time_out_grace_period_minutes', models.PositiveIntegerField(default=0, help_text='Time out grace period for attendance in minutes')),
                ('semester', models.CharField(blank=True, choices=[('1st', '1st Semester'), ('2nd', '2nd Semester')], max_length=3, null=True)),
                ('year_level', models.CharField(blank=True, choices=[('1st', '1st Year'), ('2nd', '2nd Year'), ('3rd', '3rd Year'), ('4th', '4th Year')], max_length=3, null=True)),
                ('adviser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='base.adviser')),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('adviser', 'Adviser'), ('secretary', 'Secretary'), ('dean', 'Dean'), ('admin', 'Admin')], max_length=20)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SubjectSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('class_code', models.CharField(editable=False, max_length=6, null=True, unique=True)),
                ('day', models.CharField(max_length=100, null=True)),
                ('start_time', models.TimeField(blank=True, null=True)),
                ('end_time', models.TimeField(blank=True, null=True)),
                ('classification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.studentclassification')),
                ('students', models.ManyToManyField(blank=True, related_name='subject_schedules', to='base.student')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.subject')),
            ],
        ),
        migrations.AddField(
            model_name='student',
            name='classification',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.studentclassification'),
        ),
        migrations.CreateModel(
            name='RFIDCard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('card_number', models.CharField(max_length=255, unique=True)),
                ('student', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='base.student')),
            ],
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_in', models.DateTimeField()),
                ('time_out', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(blank=True, choices=[('absent', 'Absent'), ('late', 'Late'), ('present', 'Present'), ('excused', 'Excused')], max_length=10, null=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.student')),
                ('subject_schedule', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='base.subjectschedule')),
            ],
        ),
    ]
