from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import hashlib
import time
from datetime import datetime
import os

from .models import Booth, Candidate, VoteEvent, Signal, VVPATSlip, AuditSession
from .serializers import BoothSerializer, VoteEventSerializer, SignalSerializer

# ========================================
# EVM SIMULATOR VIEWS (Laptop Django)
# ========================================

@api_view(['GET'])
@permission_classes([AllowAny])
def index(request):
    """Main EVM dashboard"""
    booth = Booth.objects.first()
    if not booth:
        return render(request, 'evm/index.html', {"error": "No booth configured"})
    
    context = {
        "booth": BoothSerializer(booth).data,
        "total_votes": VoteEvent.objects.filter(booth=booth).count()
    }
    return render(request, 'evm/index.html', context)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def cast_vote(request, booth_id):
    """Simulate casting a vote (EVM + VVPAT + Signal)"""
    try:
        data = json.loads(request.body)
        booth = Booth.objects.get(booth_id=booth_id)
        candidate = Candidate.objects.get(booth=booth, candidate_id=data['candidateID'])
        
        timestamp = int(time.time() * 1000)
        sequence = VoteEvent.objects.filter(booth=booth).count() + 1
        voter_token_hash = hashlib.sha256(data['voterToken'].encode()).hexdigest()
        
        # 1. EVM Vote Event
        vote = VoteEvent.objects.create(
            booth=booth,
            candidate=candidate,
            timestamp=timestamp,
            sequence=sequence,
            voter_token_hash=voter_token_hash
        )
        
        # 2. VVPAT Slip
        VVPATSlip.objects.create(
            vote=vote,
            slip_id=f"{booth_id}-SLIP-{sequence:04d}"
        )
        
        # 3. Signal for BAM (encrypted-like)
        signal_data = {
            "boothID": booth_id,
            "evmID": booth.evm_id,
            "candidateID": data['candidateID'],
            "timestamp": timestamp,
            "sequence": sequence,
            "voterToken": data['voterToken']
        }
        signal_json = json.dumps(signal_data, sort_keys=True)
        signal_hash = hashlib.sha256(signal_json.encode()).hexdigest()
        
        Signal.objects.create(
            vote=vote,
            raw_signal=signal_json,
            signal_hash=signal_hash
        )
        
        return Response({
            "status": "SUCCESS",
            "message": "Vote recorded: EVM + VVPAT + Signal generated",
            "vote": VoteEventSerializer(vote).data,
            "signal_hash": signal_hash
        })
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def booth_status(request, booth_id):
    """Current status for booth"""
    booth = Booth.objects.get(booth_id=booth_id)
    votes = VoteEvent.objects.filter(booth=booth).count()
    signals = Signal.objects.filter(booth=booth).count()
    vvpat = VVPATSlip.objects.filter(booth=booth).count()
    
    return Response({
        "booth_id": booth_id,
        "evm_votes": votes,
        "vvpat_slips": vvpat,
        "bam_signals": signals,
        "all_match": votes == vvpat == signals
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def booth_signals(request, booth_id):
    """Signals for BAM (Pi to read)"""
    booth = Booth.objects.get(booth_id=booth_id)
    signals = Signal.objects.filter(booth=booth).order_by('vote__sequence')
    
    return Response({
        "booth_id": booth_id,
        "total_signals": signals.count(),
        "signals": [SignalSerializer(s).data for s in signals]
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def booth_results(request, booth_id):
    """Final election results"""
    booth = Booth.objects.get(booth_id=booth_id)
    counts = VoteEvent.objects.filter(booth=booth).values(
        'candidate__candidate_id'
    ).annotate(count=models.Count('id'))
    
    return Response({
        "booth_id": booth_id,
        "results": list(counts),
        "total_votes": VoteEvent.objects.filter(booth=booth).count()
    })

