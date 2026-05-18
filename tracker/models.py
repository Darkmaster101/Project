from django.db import models
import socket


class AppSession(models.Model):
    username = models.CharField(max_length=200)
    hostname = models.CharField(max_length=200)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-opened_at"]

    def __str__(self):
        return f"{self.username}@{self.hostname} — {self.opened_at:%Y-%m-%d %H:%M:%S}"
