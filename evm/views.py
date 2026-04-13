from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import hashlib
import time
import hmac
from datetime import datetime, timezone
from django.db.models import Count

from .models import Booth, Candidate, VoteEvent, Signal, VVPATSlip, AuditSession, LedgerBlock
from .serializers import BoothSerializer, VoteEventSerializer, SignalSerializer

# ========================================
# CONSTANTS (simulated hardware secrets)
# ========================================
DEVICE_SECRET = "K9F82M3X"
DEVICE_PRIVATE_KEY = "EVM_PRIVATE_KEY_SIM_2026"
MACHINE_ID = "EVM1023"

# ========================================
# HELPER: Compute SHA-256
# ========================================
def sha256(*parts):
    combined = "".join(str(p) for p in parts)
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

# ========================================
# HELPER: Build & save a VOTE block
# ========================================
def create_vote_block(booth, candidate_id, timestamp):
    last = LedgerBlock.objects.filter(booth=booth).order_by('-block_number').first()
    block_number = (last.block_number + 1) if last else 1
    previous_hash = last.current_hash if last else ("0" * 64)

    # current_hash = SHA256(block_number + candidate_id + timestamp + previous_hash)
    current_hash = sha256(block_number, candidate_id, timestamp, previous_hash)

    return LedgerBlock.objects.create(
        booth=booth,
        block_number=block_number,
        block_type=LedgerBlock.BLOCK_TYPE_VOTE,
        candidate_id=candidate_id,
        timestamp=timestamp,
        previous_hash=previous_hash,
        current_hash=current_hash,
    )

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
def cast_vote(request, booth_id):
    """Pure Django view - cast a vote and create a ledger block"""
    if request.method != 'POST':
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))

        if not data.get('candidateID'):
            return JsonResponse({"error": "candidateID required"}, status=400)

        booth = Booth.objects.get(booth_id=booth_id)

        # PHASE 1: Check voting status
        if booth.voting_status != 'OPEN':
            return JsonResponse({"error": "Voting is CLOSED. No more votes can be cast."}, status=403)

        candidate = Candidate.objects.get(booth=booth, candidate_id=data['candidateID'])

        timestamp = int(time.time() * 1000)
        sequence = VoteEvent.objects.filter(booth=booth).count() + 1
        voter_token_hash = hashlib.sha256(str(timestamp).encode()).hexdigest()

        # 1. Create EVM Vote
        vote = VoteEvent.objects.create(
            booth=booth,
            candidate=candidate,
            timestamp=timestamp,
            sequence=sequence,
            voter_token_hash=voter_token_hash
        )

        # 2. Update Candidate Count
        candidate.vote_count += 1
        candidate.save()

        # 3. VVPAT Slip
        VVPATSlip.objects.create(
            vote=vote,
            slip_id=f"{booth_id}-SLIP-{sequence:04d}"
        )

        # 4. BAM Signal
        signal_data = {
            "boothID": booth_id,
            "evmID": booth.evm_id,
            "candidateID": data['candidateID'],
            "timestamp": timestamp,
            "sequence": sequence
        }
        signal_json = json.dumps(signal_data, sort_keys=True)
        signal_hash = hashlib.sha256(signal_json.encode()).hexdigest()

        Signal.objects.create(
            vote=vote,
            raw_signal=signal_json,
            signal_hash=signal_hash
        )

        # 5. Create ledger block
        block = create_vote_block(booth, data['candidateID'], timestamp)

        return JsonResponse({
            "status": "SUCCESS",
            "sequence": sequence,
            "signal_hash": signal_hash[:16] + "...",
            "block_number": block.block_number,
            "block_hash": block.current_hash[:16] + "...",
        })

    except Booth.DoesNotExist:
        return JsonResponse({"error": "Booth not found"}, status=404)
    except Candidate.DoesNotExist:
        return JsonResponse({"error": "Candidate not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ========================================
# PHASE 3 HELPER: Real Hash Chain Verify
# Returns dict with integrity result + tamper block number
# ========================================
def _verify_chain_internal(booth):
    """
    Recompute the hash chain for all VOTE blocks.

    Returns:
        {
          "integrity_flag": "PASS" | "FAIL",
          "tamper_block_number": <int>|None,
          "tamper_detail": "..." | None,
          "last_vote_block_hash": "<hex>",   # Hn - for Final Commitment
          "total_vote_blocks": <int>,
        }
    """
    blocks = list(
        LedgerBlock.objects.filter(booth=booth, block_type=LedgerBlock.BLOCK_TYPE_VOTE)
        .order_by('block_number')
    )

    prev_hash = "0" * 64
    last_good_hash = "0" * 64

    for blk in blocks:
        # Recompute exactly as done in create_vote_block
        expected = sha256(blk.block_number, blk.candidate_id, blk.timestamp, prev_hash)

        if expected != blk.current_hash:
            return {
                "integrity_flag": "FAIL",
                "tamper_block_number": blk.block_number,
                "tamper_detail": (
                    f"Block #{blk.block_number}: "
                    f"stored hash {blk.current_hash[:20]}... "
                    f"does not match recomputed hash {expected[:20]}... "
                    f"(candidate_id='{blk.candidate_id}', timestamp={blk.timestamp})"
                ),
                "last_vote_block_hash": last_good_hash,
                "total_vote_blocks": len(blocks),
            }

        prev_hash = blk.current_hash
        last_good_hash = blk.current_hash

    return {
        "integrity_flag": "PASS",
        "tamper_block_number": None,
        "tamper_detail": None,
        "last_vote_block_hash": last_good_hash,
        "total_vote_blocks": len(blocks),
    }


# ========================================
# /verify-chain/<booth_id>/
# Called by the frontend during Phase 2
# animation to get REAL tamper detection.
# ========================================
@csrf_exempt
def verify_chain_view(request, booth_id):
    """
    PHASE 3: Real hash-chain verification endpoint.
    Frontend calls this during the progress animation to get live tamper detection.
    """
    if request.method not in ('GET', 'POST'):
        return JsonResponse({"error": "GET or POST required"}, status=405)

    try:
        booth = Booth.objects.get(booth_id=booth_id)
        result = _verify_chain_internal(booth)
        return JsonResponse(result)
    except Booth.DoesNotExist:
        return JsonResponse({"error": "Booth not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ========================================
# MAIN: /close-voting/<booth_id>/
# Executes all 10 phases and seals the blockchain.
# ========================================
@csrf_exempt
def close_voting(request, booth_id):
    """
    Presiding Officer presses CLOSE.
    Executes all 10 phases per the full cryptographic spec and seals the blockchain.

    PHASE 0  - Pre-conditions (checked implicitly)
    PHASE 1  - Hardware-level trigger:      Voting_Enabled = FALSE, status = CLOSED
    PHASE 2  - Freeze Vote Ledger:          Memory read-only (enforced by status check)
    PHASE 3  - Validate Hash Chain:         _verify_chain_internal() - detect tamper + block#
    PHASE 4  - Sort Party IDs:              lexicographic ordering of candidate_id
    PHASE 5  - Deterministic Result String: EVM_ID|01:x1|02:x2|...|Device_Secret
    PHASE 6  - Result Hash:                 SHA256(Result_String)
    PHASE 7  - Bind to vote chain:          SHA256(Last_Vote_Block_Hash || Result_Hash)
    PHASE 8  - Digital Signature:           HMAC-SHA256(Final_Commitment_Hash, Device_Private_Key)
    PHASE 9  - Create Final Block:          append block n+1 with all cryptographic fields
    PHASE 10 - Lock Entire System:          status = SEALED, VVPAT final slip
    """
    if request.method != 'POST':
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        booth = Booth.objects.get(booth_id=booth_id)

        if booth.voting_status != 'OPEN':
            return JsonResponse({"error": "Voting already closed/sealed."}, status=400)

        # ─────────────────────────────────────────────
        # PHASE 1 - HARDWARE TRIGGER / VOTING FREEZE
        # Interrupt generation: Voting_Enabled = FALSE
        # System_State = FINALIZING → CLOSED
        # ─────────────────────────────────────────────
        booth.voting_status = 'CLOSED'
        booth.save()

        # ─────────────────────────────────────────────
        # PHASE 2 - FREEZE VOTE LEDGER
        # Write-protection enabled (simulated: CLOSED status prevents cast_vote)
        # cast_vote() checks booth.voting_status != 'OPEN' and returns 403
        # ─────────────────────────────────────────────

        # ─────────────────────────────────────────────
        # PHASE 3 - VALIDATE INTERNAL CONSISTENCY
        # Recompute entire hash chain.
        # Detect first tampered block by block_number.
        # ─────────────────────────────────────────────
        chain_result = _verify_chain_internal(booth)
        integrity_flag = chain_result["integrity_flag"]
        tamper_block_number = chain_result["tamper_block_number"]
        tamper_detail = chain_result["tamper_detail"]
        last_vote_block_hash = chain_result["last_vote_block_hash"]   # Hn

        # ─────────────────────────────────────────────
        # PHASE 4 - SORT PARTY IDs (lexicographic)
        # Assign fixed ordered IDs: 01→PartyA, 02→PartyB, etc.
        # ─────────────────────────────────────────────
        candidates = Candidate.objects.filter(booth=booth).order_by('candidate_id')

        # ─────────────────────────────────────────────
        # PHASE 5 - CREATE DETERMINISTIC RESULT STRING
        # Format: EVM_ID|01:x1|02:x2|03:x3|...|Private_key
        # No spaces. Fixed separators. ASCII only.
        # ─────────────────────────────────────────────
        result_parts = [f"{c.candidate_id}:{c.vote_count}" for c in candidates]
        result_string = "|".join(result_parts)
        total_votes = VoteEvent.objects.filter(booth=booth).count()
        close_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Full result string with EVM_ID prefix and device secret (per spec)
        full_result_string = f"{booth.evm_id}|{result_string}|{DEVICE_SECRET}"

        # ─────────────────────────────────────────────
        # PHASE 6 - COMPUTE RESULT HASH
        # Result_Hash = SHA256(Result_String)
        # ─────────────────────────────────────────────
        result_hash = hashlib.sha256(full_result_string.encode('utf-8')).hexdigest()

        # ─────────────────────────────────────────────
        # PHASE 7 - BIND TO VOTE CHAIN
        # Final_Commitment_Input = Last_Vote_Block_Hash || Result_Hash
        # Final_Commitment_Hash  = SHA256(Final_Commitment_Input)
        # This prevents replacing only the result string without breaking the chain.
        # Even a single vote change alters Hn which alters Final_Commitment_Hash.
        # ─────────────────────────────────────────────
        final_commitment_input = last_vote_block_hash + result_hash
        final_commitment_hash = hashlib.sha256(
            final_commitment_input.encode('utf-8')
        ).hexdigest()

        # ─────────────────────────────────────────────
        # PHASE 8 - HARDWARE-ROOTED DIGITAL SIGNATURE
        # Signature = Sign(Final_Commitment_Hash, Device_Private_Key)
        # Simulated via HMAC-SHA256 (real system uses HSM/secure element).
        # Private key: burned at manufacturing, not extractable.
        # ─────────────────────────────────────────────
        digital_signature = hmac.new(
            DEVICE_PRIVATE_KEY.encode('utf-8'),
            final_commitment_hash.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # ─────────────────────────────────────────────
        # PHASE 9 - CREATE FINAL BLOCK STRUCTURE
        # Append as block n+1 in chain.
        # Final_Block_Hash ties together all state.
        # ─────────────────────────────────────────────
        last_block = LedgerBlock.objects.filter(booth=booth).order_by('-block_number').first()
        final_block_number = (last_block.block_number + 1) if last_block else 1
        previous_hash = last_block.current_hash if last_block else ("0" * 64)

        timestamp_close = int(time.time() * 1000)
        final_block_hash = sha256(
            booth.evm_id,
            total_votes,
            result_hash,
            last_vote_block_hash,
            timestamp_close
        )

        final_block = LedgerBlock.objects.create(
            booth=booth,
            block_number=final_block_number,
            block_type=LedgerBlock.BLOCK_TYPE_FINAL,
            candidate_id="",
            timestamp=timestamp_close,
            total_votes=total_votes,
            result_hash=result_hash,
            integrity_flag=integrity_flag,
            result_string=result_string,
            last_vote_block_hash=last_vote_block_hash,
            final_commitment_hash=final_commitment_hash,
            digital_signature=digital_signature,
            tamper_block_number=tamper_block_number,
            previous_hash=previous_hash,
            current_hash=final_block_hash,
        )

        # ─────────────────────────────────────────────
        # PHASE 10 - LOCK ENTIRE SYSTEM
        # System_State = SEALED
        # Bootloader prevents firmware rewrite (simulated).
        # Generate VVPAT final commitment slip.
        # ─────────────────────────────────────────────
        booth.voting_status = 'SEALED'
        booth.save()

        # VVPAT Final Commitment Slip (last slip printed by VVPAT per spec Phase 10)
        vvpat_slip_lines = [
            f"EVM_ID: {booth.evm_id}",
            f"Total Votes: {total_votes}",
            f"Final Block: #{final_block_number}",
            f"Commitment: {final_commitment_hash[:24]}...",
            f"Signature: {digital_signature[:16]}...",
            f"Timestamp: {close_ts}",
            f"Integrity: {integrity_flag}",
        ]
        if tamper_block_number is not None:
            vvpat_slip_lines.append(f"TAMPER DETECTED: Block #{tamper_block_number}")

        return JsonResponse({
            "status": "SEALED",
            # Phase 3 - chain integrity
            "integrity_flag": integrity_flag,
            "tamper_block_number": tamper_block_number,
            "tamper_detail": tamper_detail,
            "total_vote_blocks": chain_result["total_vote_blocks"],
            # Phase 5 - result
            "result_string": result_string,
            "total_votes": total_votes,
            "close_timestamp": close_ts,
            # Phase 6 - result hash
            "result_hash": result_hash,
            # Phase 7 - chain binding
            "last_vote_block_hash": last_vote_block_hash,
            "final_commitment_hash": final_commitment_hash,
            # Phase 8 - signature
            "digital_signature": digital_signature[:32] + "...",
            "digital_signature_full": digital_signature,
            # Phase 9 - final block
            "final_block_number": final_block.block_number,
            "final_block_hash": final_block_hash,
            # Phase 10 - VVPAT final slip
            "vvpat_slip": "\n".join(vvpat_slip_lines),
        })

    except Booth.DoesNotExist:
        return JsonResponse({"error": "Booth not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def publish_result(request, booth_id):
    if request.method != 'POST':
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        booth = Booth.objects.get(booth_id=booth_id)

        if booth.voting_status != 'SEALED':
            return JsonResponse({"error": "Voting must be SEALED before publishing result."}, status=400)

        # ── Phase 1: Recompute Per-Vote Hash Chain ──
        chain_result = _verify_chain_internal(booth)
        recomputed_last_vote_hash = chain_result["last_vote_block_hash"]
        
        final_block = LedgerBlock.objects.get(booth=booth, block_type=LedgerBlock.BLOCK_TYPE_FINAL)

        if recomputed_last_vote_hash != final_block.last_vote_block_hash:
            return JsonResponse({"error": "TAMPER DETECTED: Last Vote Block Hash Mismatch", "phase": 1}, status=400)

        # ── Phase 2 & 3: Form Result String & Compute Result Hash ──
        candidates = Candidate.objects.filter(booth=booth).order_by('candidate_id')
        result_parts = [f"{c.candidate_id}:{c.vote_count}" for c in candidates]
        result_string = "|".join(result_parts)
        full_result_string = f"{booth.evm_id}|{result_string}|{DEVICE_SECRET}"
        
        recomputed_result_hash = hashlib.sha256(full_result_string.encode('utf-8')).hexdigest()

        if recomputed_result_hash != final_block.result_hash:
            return JsonResponse({"error": "COUNTER TAMPER DETECTED: Result Hash Mismatch", "phase": 3}, status=400)

        # ── Phase 4: Recompute Final Block Hash ──
        recomputed_final_block_hash = sha256(
            booth.evm_id,
            final_block.total_votes,
            recomputed_result_hash,
            final_block.last_vote_block_hash,
            final_block.timestamp
        )

        if recomputed_final_block_hash != final_block.current_hash:
            return JsonResponse({"error": "FINAL BLOCK MISMATCH", "phase": 4}, status=400)

        # ── Phase 5: Verify Signature ──
        expected_digital_signature = hmac.new(
            DEVICE_PRIVATE_KEY.encode('utf-8'),
            final_block.final_commitment_hash.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if final_block.digital_signature != expected_digital_signature:
            return JsonResponse({"error": "SIGNATURE INVALID", "phase": 5}, status=400)

        # All verifications OK
        return JsonResponse({
            "status": "SUCCESS",
            "results": [{"id": c.candidate_id, "name": c.name, "votes": c.vote_count} for c in candidates],
            "commitment_token": final_block.final_commitment_hash,
            "timestamp_close": datetime.fromtimestamp(final_block.timestamp / 1000.0, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_votes": final_block.total_votes
        })

    except Booth.DoesNotExist:
        return JsonResponse({"error": "Booth not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def ledger_view(request):
    """Render the ledger visualization page"""
    booth = Booth.objects.first()
    if not booth:
        return render(request, 'evm/ledger.html', {"error": "No booth configured"})
    context = {"booth": BoothSerializer(booth).data}
    return render(request, 'evm/ledger.html', context)


@api_view(['GET'])
@permission_classes([AllowAny])
def ledger_blocks(request, booth_id):
    """Return all ledger blocks as JSON for visualization"""
    booth = Booth.objects.get(booth_id=booth_id)
    blocks = LedgerBlock.objects.filter(booth=booth).order_by('block_number')
    data = []
    for b in blocks:
        data.append({
            "block_number": b.block_number,
            "block_type": b.block_type,
            "candidate_id": b.candidate_id,
            "timestamp": b.timestamp,
            "total_votes": b.total_votes,
            "result_hash": b.result_hash,
            "integrity_flag": b.integrity_flag,
            "result_string": b.result_string,
            "last_vote_block_hash": b.last_vote_block_hash,
            "final_commitment_hash": b.final_commitment_hash,
            "digital_signature": b.digital_signature,
            "tamper_block_number": b.tamper_block_number,
            "previous_hash": b.previous_hash,
            "current_hash": b.current_hash,
            "created_at": b.created_at.isoformat(),
        })
    return JsonResponse({
        "booth_id": booth_id,
        "voting_status": booth.voting_status,
        "total_blocks": len(data),
        "blocks": data,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def booth_status(request, booth_id):
    """Current status for booth"""
    booth = Booth.objects.get(booth_id=booth_id)
    votes = VoteEvent.objects.filter(booth=booth).count()
    signals = Signal.objects.filter(vote__booth=booth).count()
    vvpat = VVPATSlip.objects.filter(vote__booth=booth).count()

    return Response({
        "booth_id": booth_id,
        "evm_votes": votes,
        "vvpat_slips": vvpat,
        "bam_signals": signals,
        "all_match": votes == vvpat == signals,
        "voting_status": booth.voting_status,
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def booth_signals(request, booth_id):
    """Signals for BAM (Pi to read)"""
    booth = Booth.objects.get(booth_id=booth_id)
    signals = Signal.objects.filter(vote__booth=booth).order_by('vote__sequence')

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
    ).annotate(count=Count('id'))

    return Response({
        "booth_id": booth_id,
        "results": list(counts),
        "total_votes": VoteEvent.objects.filter(booth=booth).count()
    })
