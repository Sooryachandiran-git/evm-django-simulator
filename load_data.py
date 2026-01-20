import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evm_project.settings')
django.setup()

from evm.models import Booth, Candidate

print("🗑️ Deleting existing data...")
Booth.objects.all().delete()
Candidate.objects.all().delete()

print("🏗️ Creating fresh booth...")
booth = Booth.objects.create(
    booth_id='TN-01-001',
    evm_id='EVM-TN01-001',
    state='Tamil Nadu',
    ac_name='Cuddalore AC'
)
print(f"✅ Booth: {booth.booth_id}")

print("👥 Creating UI-matched candidates...")
candidates = [
    {'id': 'CAND_A', 'name': 'AAA', 'symbol': 'α'},
    {'id': 'CAND_B', 'name': 'BBB', 'symbol': 'β'},
    {'id': 'CAND_C', 'name': 'CCC', 'symbol': 'γ'},
    {'id': 'CAND_D', 'name': 'DDD', 'symbol': 'δ'},
    {'id': 'NOTA', 'name': 'None of the Above', 'symbol': '✗'}
]

for data in candidates:
    Candidate.objects.create(
        booth=booth,
        candidate_id=data['id'],
        name=data['name'],
        symbol=data['symbol']
    )
    print(f"✅ Added: {data['id']} ({data['symbol']})")

print("\n🎉 Data loaded! Run: python manage.py runserver")
print("Test: http://127.0.0.1:8000/")
