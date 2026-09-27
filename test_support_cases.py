import os

from laya import Router

model_path = os.environ.get("LAYA_ENGLISH_MODEL", "convaiinnovations/laya")

questions = {
    "department": {
        "type": "choice",
        "instructions": "Which department should handle this support request?",
        "criteria": {
            "billing": "invoices, payments, refunds, subscriptions, and account charges",
            "technical": "bugs, outages, login failures, and integrations",
        },
    },
    "urgency": {
        "type": "score",
        "instructions": "How urgent is the support request?",
        "criteria": [
            "routine, no time pressure",
            "time-sensitive, needs attention soon",
            "urgent, blocking work or customers",
        ],
    },
    "churn_risk": {
        "type": "noul",
        "instructions": "Does the customer suggest they may cancel or leave?",
    },
}

cases = [
    (
        "CASE 1",
        "Hi, we were billed twice for March. Please refund the duplicate today or we will cancel our plan.",
        "billing", 1.7722, 0.8790,
    ),
    (
        "CASE 2",
        "Our app is down and customers cannot log in. This is blocking all sales.",
        "technical", 1.9303, 0.1426,
    ),
    (
        "CASE 3",
        "Can you tell me how to export my invoices as CSV?",
        "billing", 0.8009, 0.0000,
    ),
    (
        "CASE 4",
        "Thanks for the help, I have a quick question about my subscription renewal date.",
        "billing", 0.6653, 0.0450,
    ),
    (
        "CASE 5",
        "The login page fails after the latest update and our team cannot work.",
        "technical", 1.8166, 0.3534,
    ),
]

router = Router(
    models={"english": model_path},
    device="cpu",
    max_loaded=1,
)

for name, message, expected_department, expected_urgency, expected_churn in cases:
    result = router.predict({"message": message}, questions)
    answers = result["answers"]
    department = answers["department"]["choice"]
    urgency = answers["urgency"]["score"]
    churn = answers["churn_risk"]["noul"]
    routing_model = result["routing"]["model"]

    passed = (
        department == expected_department
        and abs(urgency - expected_urgency) <= 0.1
        and abs(churn - expected_churn) <= 0.1
        and routing_model == "english"
    )

    print(f"\n{name}: {'PASS' if passed else 'CHECK'}")
    print(f"  message:       {message}")
    print(f"  department:    {department} (expected {expected_department})")
    print(f"  urgency:       {urgency:.4f} (expected {expected_urgency:.4f})")
    print(f"  churn_risk:    {churn:.4f} (expected {expected_churn:.4f})")
    print(f"  routing_model: {routing_model} (expected english)")