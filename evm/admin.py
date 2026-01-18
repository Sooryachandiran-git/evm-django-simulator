from django.contrib import admin
from .models import Booth, VoteEvent, Signal, VVPATSlip, AuditSession, Candidate
# Register your models here.
admin.site.register([Booth, VoteEvent, Signal, VVPATSlip, AuditSession, Candidate])