# Seed the client's 10 training modules (from the Excel catalogue). Idempotent.
from django.db import migrations

MODULES = [
    ("TR001", "CRM Lead Journey Fundamentals", "Systems", "All Employees", "Classroom + LMS", 2, True, "Onboarding", 0.80, "Lead lifecycle, statuses, ownership and data discipline.", "Manage every lead without missing next actions.", "1.0"),
    ("TR002", "Ethical Selling & Compliance", "Compliance", "Sales / Leaders", "Workshop", 3, True, "Annual", 0.85, "Suitability, disclosures and documentation.", "Sell responsibly and maintain evidence.", "1.0"),
    ("TR003", "High-Performance Calling", "Sales Skill", "Sales", "Role-play", 2, True, "Quarterly", 0.80, "Opening, discovery, objections and closure.", "Improve call quality and conversion.", "1.1"),
    ("TR004", "Meeting Excellence", "Sales Skill", "Sales", "Workshop", 2, True, "Quarterly", 0.80, "Preparation, agenda and follow-through.", "Convert booked meetings into outcomes.", "1.0"),
    ("TR005", "Post-Sales Customer Care", "Customer Success", "Post Sales / Sales", "Classroom", 2, True, "Annual", 0.80, "Onboarding, service, renewal and referral.", "Protect customer value after closure.", "1.0"),
    ("TR006", "Data Privacy & Cyber Safety", "IT / Compliance", "All Employees", "eLearning", 1.5, True, "Annual", 0.85, "Passwords, phishing, data and incidents.", "Reduce operational information risk.", "2.0"),
    ("TR007", "KPI & Performance Literacy", "Performance", "All Employees", "Workshop", 1.5, True, "Annual", 0.75, "Targets, conversion, quality and health score.", "Understand how work affects company health.", "1.0"),
    ("TR008", "Leadership Coaching Rhythm", "Leadership", "Team Leaders", "Workshop", 3, True, "Half-Yearly", 0.80, "One-to-ones, call coaching and pipeline reviews.", "Run accountable and supportive teams.", "1.0"),
    ("TR009", "Finance for Non-Finance", "Finance", "Leaders", "Classroom", 2, False, "Annual", 0.75, "Revenue, costs, profit, cash and forecast.", "Make commercially sound decisions.", "1.0"),
    ("TR010", "Product Knowledge Certification", "Product", "Sales / Post Sales", "Blended", 4, True, "Half-Yearly", 0.85, "Product structure, suitability and use cases.", "Recommend the right solution confidently.", "3.0"),
]


def seed(apps, schema_editor):
    TrainingModule = apps.get_model("hr", "TrainingModule")
    for m in MODULES:
        TrainingModule.objects.get_or_create(module_id=m[0], defaults={
            "title": m[1], "category": m[2], "audience": m[3], "delivery_mode": m[4],
            "duration_hours": m[5], "mandatory": m[6], "frequency": m[7], "pass_mark": m[8],
            "content_summary": m[9], "learning_outcome": m[10], "version": m[11], "active": True,
        })


def unseed(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("hr", "0020_trainingmodule_trainingassignment_assessment")]
    operations = [migrations.RunPython(seed, unseed)]
