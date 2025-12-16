from django.db import migrations, models
import django.db.models.deletion

def seed_roles_and_teams(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Team = apps.get_model('accounts', 'Team')

    roles = [
        ('team_member', 'Team Member', 'Update availability, request leave, view calendar', 'Own data only', True),
        ('rota_manager', 'Rota Manager / Team Lead', 'Assign shifts, approve leave, resolve conflicts, run reports', 'Team edit', False),
        ('service_manager', 'Service Manager / Stakeholder', 'View team schedules and utilisation metrics', 'Read-only', False),
        ('system_admin', 'System Administrator', 'Manage users, roles, teams, calendars, audits', 'Full system access', False),
        ('automation_bot', 'Automation Bot / Integration Client', 'Scoped API access for integrations', 'Scoped API', False),
    ]
    for code, name, responsibilities, access_level, is_default in roles:
        Role.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'responsibilities': responsibilities,
                'access_level': access_level,
                'is_default': is_default,
            },
        )

    for team_name in ['Alpha', 'Bravo', 'Charlie', 'Delta']:
        Team.objects.get_or_create(name=f"Team {team_name}")


def map_role_profiles(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    CustomUser = apps.get_model('accounts', 'CustomUser')
    default_role = Role.objects.filter(code='team_member').first()
    for user in CustomUser.objects.all():
        if default_role and user.role_profile_id is None:
            user.role_profile = default_role
            user.save(update_fields=['role_profile'])


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_alter_customuser_email'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=30, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('responsibilities', models.TextField(blank=True)),
                ('access_level', models.CharField(blank=True, max_length=50)),
                ('is_default', models.BooleanField(default=False)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('timezone', models.CharField(default='Europe/London', max_length=50)),
                ('default_start_time', models.TimeField(blank=True, null=True)),
                ('default_end_time', models.TimeField(blank=True, null=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='team',
        ),
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(choices=[('team_member', 'Team Member'), ('rota_manager', 'Rota Manager'), ('service_manager', 'Service Manager'), ('system_admin', 'System Admin'), ('automation_bot', 'Automation Bot')], default='team_member', max_length=20),
        ),
        migrations.AddField(
            model_name='customuser',
            name='role_profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.role'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='members', to='accounts.team'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='skills',
            field=models.ManyToManyField(blank=True, to='accounts.skill'),
        ),
        migrations.RunPython(seed_roles_and_teams, reverse_noop),
        migrations.RunPython(map_role_profiles, reverse_noop),
    ]
