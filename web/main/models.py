from django.db import models


class Task(models.Model):
    task_id = models.CharField(max_length=40)
    task_type = models.CharField(max_length=30)
    data_input = models.TextField()
    data_output = models.TextField()
    status = models.CharField(max_length=15)
