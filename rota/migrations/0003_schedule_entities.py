from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_role_team_skill_models'),
        ('rota', '0002_leaverequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='shift',
            name='is_on_call',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='shift',
            name='role_required',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.role'),
        ),
        migrations.AddField(
            model_name='shift',
            name='team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.team'),
        ),
        migrations.CreateModel(
            name='AvailabilitySlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('slot_type', models.CharField(choices=[('available', 'Available'), ('unavailable', 'Unavailable'), ('on_call', 'On Call'), ('leave', 'Leave')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='availability', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['start'],
            },
        ),
        migrations.CreateModel(
            name='ChangeLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entity_type', models.CharField(max_length=100)),
                ('entity_id', models.CharField(max_length=100)),
                ('action', models.CharField(choices=[('create', 'Create'), ('update', 'Update'), ('delete', 'Delete')], max_length=20)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('details', models.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='Holiday',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('date', models.DateField()),
                ('region', models.CharField(default='UK', max_length=100)),
            ],
            options={
                'ordering': ['date'],
                'unique_together': {('date', 'region')},
            },
        ),
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assignment_type', models.CharField(choices=[('primary', 'Primary'), ('backup', 'Backup'), ('on_call', 'On Call')], default='primary', max_length=20)),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='rota.shift')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name='availabilityslot',
            index=models.Index(fields=['user', 'start', 'end'], name='rota_avail_user_st_90c39d_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='assignment',
            unique_together={('shift', 'user', 'assignment_type')},
        ),
    ]
