from rest_framework import serializers
from .models import Booth, VoteEvent, Signal, VVPATSlip, AuditSession

class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ['candidate_id', 'name', 'symbol', 'vote_count']

class BoothSerializer(serializers.ModelSerializer):
    candidates = CandidateSerializer(many=True, read_only=True)
    total_votes = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Booth
        fields = ['booth_id', 'evm_id', 'state', 'ac_name', 'candidates', 'total_votes']

class VoteEventSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    
    class Meta:
        model = VoteEvent
        fields = ['sequence', 'candidate_id', 'candidate_name', 'timestamp', 'voter_token_hash']

class SignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signal
        fields = ['raw_signal', 'signal_hash', 'captured_at']

class AuditSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditSession
        fields = '__all__'
