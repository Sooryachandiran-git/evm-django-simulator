import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evm_project.settings')
django.setup()

from evm.models import Booth, Candidate

# Create booth
booth, _ = Booth.objects.get_or_create(
    booth_id='TN-01-001',
    defaults={
        'evm_id': 'EVM-TN-01-001',
        'state': 'Tamil Nadu',
        'ac_name': 'Cuddalore'
    }
)

# Create candidates
candidates = [
    ('CAND_A', 'Candidate A (Party 1)', '\u03B1'),
    ('CAND_B', 'Candidate B (Party 2)', '\u03B2'),
    ('CAND_C', 'Candidate C (Party 3)', '\u03B3'),
    ('CAND_D', 'Candidate D (Party 4)', '\u03B4'),
    ('NOTA', 'None of the Above', 'X'),
]

for cand_id, name, symbol in candidates:
    Candidate.objects.get_or_create(
        booth=booth,
        candidate_id=cand_id,
        defaults={'name': name, 'symbol': symbol}
    )

print("Test booth TN-01-001 and 5 candidates created!")
