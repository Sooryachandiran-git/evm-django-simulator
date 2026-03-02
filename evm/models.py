from django.db import models
import hashlib
from datetime import datetime

# ====================================
# EVM SIMULATOR MODELS (DJANGO)
# ====================================

class Booth(models.Model):
    """Polling booth (one Django record = one physical booth)"""
    booth_id = models.CharField(max_length=50, unique=True)
    evm_id = models.CharField(max_length=50)
    state = models.CharField(max_length=100)
    ac_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Voting status: OPEN / CLOSED / SEALED
    voting_status = models.CharField(max_length=20, default='OPEN')
    
    class Meta:
        ordering = ['booth_id']
    
    def __str__(self):
        return self.booth_id

class Candidate(models.Model):
    """Candidate for a booth"""
    booth = models.ForeignKey(Booth, on_delete=models.CASCADE, related_name='candidates')
    candidate_id = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    symbol = models.CharField(max_length=10)
    vote_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('booth', 'candidate_id')
    
    def __str__(self):
        return f"{self.candidate_id} ({self.vote_count})"

class VoteEvent(models.Model):
    """Single vote cast in EVM"""
    booth = models.ForeignKey(Booth, on_delete=models.CASCADE, related_name='votes')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    timestamp = models.BigIntegerField(help_text="ms since epoch")
    sequence = models.IntegerField(help_text="Vote sequence number")
    voter_token_hash = models.CharField(max_length=64, help_text="SHA256(voter_token)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('booth', 'sequence')
        ordering = ['sequence']
    
    def __str__(self):
        return f"Vote #{self.sequence} - {self.candidate.name}"

class VVPATSlip(models.Model):
    """Simulated VVPAT paper slip"""
    vote = models.OneToOneField(VoteEvent, on_delete=models.CASCADE, related_name='vvpat_slip')
    slip_id = models.CharField(max_length=50, unique=True)
    printed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='SEALED_IN_BOX')
    
    def __str__(self):
        return self.slip_id

class Signal(models.Model):
    """Signal from CU to VVPAT (what BAM captures)"""
    vote = models.OneToOneField(VoteEvent, on_delete=models.CASCADE, related_name='signal')
    raw_signal = models.TextField(help_text="Encrypted signal from EVM")
    signal_hash = models.CharField(max_length=64)
    captured_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Signal for Vote #{self.vote.sequence}"

# ====================================
# LEDGER BLOCK MODEL
# ====================================

class LedgerBlock(models.Model):
    """Internal blockchain block stored per vote or final seal"""
    BLOCK_TYPE_VOTE = 'VOTE'
    BLOCK_TYPE_FINAL = 'FINAL'
    BLOCK_TYPES = [(BLOCK_TYPE_VOTE, 'Vote Block'), (BLOCK_TYPE_FINAL, 'Final Block')]

    booth = models.ForeignKey(Booth, on_delete=models.CASCADE, related_name='ledger_blocks')
    block_number = models.IntegerField()
    block_type = models.CharField(max_length=10, choices=BLOCK_TYPES, default=BLOCK_TYPE_VOTE)

    # Vote block fields
    candidate_id = models.CharField(max_length=20, blank=True)
    timestamp = models.BigIntegerField(default=0)

    # Final block fields
    total_votes = models.IntegerField(default=0)
    result_hash = models.CharField(max_length=64, blank=True)
    integrity_flag = models.CharField(max_length=10, blank=True)
    result_string = models.TextField(blank=True)

    # Cryptographic commitment fields (Phase 6 & 7 of close-voting spec)
    last_vote_block_hash = models.CharField(max_length=64, blank=True,
        help_text="Hash of last VOTE block (Hn) — anchor for final commitment")
    final_commitment_hash = models.CharField(max_length=64, blank=True,
        help_text="SHA256(Last_Vote_Block_Hash || Result_Hash) — binds tally to chain")
    digital_signature = models.CharField(max_length=64, blank=True,
        help_text="HMAC-SHA256 of Final_Block_Hash using Device Private Key")

    # Tamper detection
    tamper_block_number = models.IntegerField(null=True, blank=True,
        help_text="Block number where hash mismatch was detected (null = no tamper)")

    # Common
    previous_hash = models.CharField(max_length=64)
    current_hash = models.CharField(max_length=64)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('booth', 'block_number')
        ordering = ['block_number']

    def __str__(self):
        return f"Block #{self.block_number} [{self.block_type}]"


# ====================================
# AUDIT MODELS (Django)
# ====================================

class AuditSession(models.Model):
    """Audit session for a booth"""
    booth = models.ForeignKey(Booth, on_delete=models.CASCADE)
    session_start = models.DateTimeField(auto_now_add=True)
    evm_count = models.IntegerField()
    vvpat_count = models.IntegerField()
    bam_count = models.IntegerField()
    chain_count = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, default='PENDING')
    discrepancy = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"Audit {self.booth.booth_id} - {self.status}"
