from __future__ import unicode_literals

from django.db import models

# Create your models here.


class MenuItems(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500, blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True,null=True)


class OrderId(models.Model):
    orderId = models.AutoField(primary_key=True)


class TableInstance(models.Model):
    tableId = models.IntegerField(default=0)
    state = models.IntegerField(default=0)
    orderId = models.ForeignKey(OrderId, default=0)
    cancel = models.BooleanField(default=False)


class Order(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    orderId = models.ForeignKey(OrderId, default=0)


class Logging(models.Model):
    action = models.IntegerField(null=True)
    count = models.IntegerField(null=True)
    pre = models.IntegerField(null=True)
    errorCode = models.IntegerField()
    asr_text = models.CharField(max_length=255, null=True, blank=True)
    nlu_text = models.CharField(max_length=255, null=True, blank=True)
    asr_time = models.CharField(max_length=255, null=True, blank=True)
    nlu_time = models.CharField(max_length=255, null=True, blank=True)
