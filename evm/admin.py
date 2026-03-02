from django.contrib import admin
from .models import Booth, VoteEvent, Signal, VVPATSlip, AuditSession, Candidate, LedgerBlock


@admin.register(LedgerBlock)
class LedgerBlockAdmin(admin.ModelAdmin):
    """
    LedgerBlock is displayed in admin for audit visibility.
    Fields are NOT read-only so that a tamperer can edit candidate_id directly
    via the admin panel \u2014 this is intentional for the demo: the close-voting
    hash verification will then catch the mismatch and report the exact block number.
    """
    list_display = [
        'block_number', 'block_type', 'candidate_id', 'timestamp',
        'integrity_flag', 'tamper_block_number', 'current_hash'
    ]
    list_filter = ['block_type', 'integrity_flag']
    search_fields = ['candidate_id', 'current_hash']
    ordering = ['block_number']


admin.site.register([Booth, VoteEvent, Signal, VVPATSlip, AuditSession, Candidate])