# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-03 05:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Change',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ChangeSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(max_length=512)),
                ('author', models.CharField(max_length=512, null=True)),
                ('message', models.TextField(null=True)),
                ('timestamp', models.DateTimeField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(max_length=512, null=True)),
                ('revision', models.CharField(max_length=512, null=True)),
                ('checksum', models.CharField(max_length=32, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='History',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Repository',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(blank=True, max_length=512, null=True)),
                ('password', models.CharField(blank=True, max_length=512, null=True)),
                ('workspace', models.CharField(blank=True, max_length=512, null=True)),
                ('origin', models.CharField(max_length=512)),
                ('name', models.CharField(max_length=512)),
                ('repository_type', models.IntegerField()),
            ],
        ),
        migrations.AddField(
            model_name='history',
            name='repository',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Repository'),
        ),
        migrations.AddField(
            model_name='file',
            name='repository',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Repository'),
        ),
        migrations.AddField(
            model_name='changeset',
            name='history',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='main.History'),
        ),
        migrations.AddField(
            model_name='changeset',
            name='repository',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Repository'),
        ),
        migrations.AddField(
            model_name='change',
            name='changeset',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.ChangeSet'),
        ),
        migrations.AddField(
            model_name='change',
            name='current_file',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='main.File'),
        ),
        migrations.AddField(
            model_name='change',
            name='previous_file',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='main.File'),
        ),
    ]
