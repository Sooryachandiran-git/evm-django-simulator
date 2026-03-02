"""
reset_and_load.py
-------------------------------------------------
Wipes ALL EVM data (votes, blocks, signals, etc.)
and seeds a fresh booth with candidates.

Run this whenever you want a completely clean session.
"""
import os
import sys
import django

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evm_project.settings')
django.setup()

from evm.models import (
    Booth, Candidate, VoteEvent,
    VVPATSlip, Signal, AuditSession, LedgerBlock
)

print("=" * 50)
print("  EVM SIMULATOR -- FULL RESET")
print("=" * 50)

# Wipe ALL data (order matters for FK constraints)
print("\n[STEP 1] Clearing all data...")

LedgerBlock.objects.all().delete()
Signal.objects.all().delete()
VVPATSlip.objects.all().delete()
VoteEvent.objects.all().delete()
AuditSession.objects.all().delete()
Candidate.objects.all().delete()
Booth.objects.all().delete()

print("   OK  LedgerBlocks  -> deleted")
print("   OK  Signals       -> deleted")
print("   OK  VVPAT Slips   -> deleted")
print("   OK  Vote Events   -> deleted")
print("   OK  Audit Sessions-> deleted")
print("   OK  Candidates    -> deleted")
print("   OK  Booths        -> deleted")

# Create fresh booth
print("\n[STEP 2] Creating fresh booth...")
booth = Booth.objects.create(
    booth_id='TN-01-001',
    evm_id='EVM-TN01-001',
    state='Tamil Nadu',
    ac_name='Cuddalore AC',
    voting_status='OPEN'
)
print(f"   OK  Booth:  {booth.booth_id}")
print(f"   OK  EVM ID: {booth.evm_id}")
print(f"   OK  Status: {booth.voting_status}")

# Create candidates
print("\n[STEP 3] Creating candidates...")
candidates = [
    {'id': 'CAND_A', 'name': 'AAA Party',         'symbol': 'A'},
    {'id': 'CAND_B', 'name': 'BBB Party',         'symbol': 'B'},
    {'id': 'CAND_C', 'name': 'CCC Alliance',      'symbol': 'C'},
    {'id': 'CAND_D', 'name': 'DDD Front',         'symbol': 'D'},
    {'id': 'NOTA',   'name': 'None of the Above', 'symbol': 'X'},
]

for data in candidates:
    Candidate.objects.create(
        booth=booth,
        candidate_id=data['id'],
        name=data['name'],
        symbol=data['symbol']
    )
    print(f"   OK  {data['id']:10s}  [{data['symbol']}]  {data['name']}")

print("\n" + "=" * 50)
print("  RESET COMPLETE - Fresh session ready!")
print("=" * 50)
print()
print("  Next steps:")
print("  1. venv\\Scripts\\python.exe manage.py runserver")
print("  2. Open : http://127.0.0.1:8000/")
print("  3. Ledger: http://127.0.0.1:8000/ledger/")
print()
