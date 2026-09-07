"""
ZeroGraph AI — Audit Mode Prompt Templates & Schema Definition
Provides specialized prompt instructions and JSON schema specs for all 8 analysis modes.
Developer: kzsamir
"""

import json

ANALYSIS_MODES = {
    "general": "General Intelligence Query",
    "persuasion": "Persuasion and Communication Analysis",
    "operational_risk": "Operational Risk Detection",
    "task_accountability": "Task and Accountability Analysis",
    "decision_tracking": "Decision Tracking",
    "timeline": "Timeline Reconstruction",
    "policy_compliance": "Policy Compliance Analysis",
    "conflict_detection": "Conflict and Contradiction Detection"
}

BRIEF_JSON_SCHEMA_EXAMPLE = {
  "query_type": "persuasion",
  "executive_status": {
    "level": "AMBER",
    "priority": "MEDIUM",
    "human_review_required": True,
    "evidence_coverage_percent": 94
  },
  "executive_summary_bn": "নির্বাচিত আলোচনায় নির্দেশনামূলক যোগাযোগের প্রবণতা পাওয়া গেছে। উপলব্ধ প্রমাণ অনুযায়ী মানব পর্যালোচনা প্রয়োজন।",
  "findings": [
    {
      "finding_id": "F-001",
      "title_en": "Directive Task Assignment",
      "title_bn": "নির্দেশনামূলক কাজ বণ্টন",
      "severity": "MEDIUM",
      "confidence": 0.86,
      "status": "NEEDS_REVIEW",
      "observation_bn": "নির্দিষ্ট কাজ সরাসরি বরাদ্দ করা হয়েছে এবং সমাপ্তির সময় উল্লেখ করা হয়েছে।",
      "interpretation_bn": "এটি directive communication pattern-এর সঙ্গে সামঞ্জস্যপূর্ণ।",
      "impact_bn": "স্বল্পমেয়াদে কাজের গতি বাড়তে পারে, তবে consultation সীমিত হলে ownership gap তৈরি হতে পারে।",
      "risk": {
        "operational": "MEDIUM",
        "people": "MEDIUM",
        "governance": "LOW",
        "likelihood": 3,
        "impact": 3,
        "exposure": 2,
        "score": 18,
        "band": "MEDIUM"
      },
      "evidence_ids": [
        "msg_004588",
        "msg_004418"
      ],
      "recommended_action_bn": "প্রতিটি task assignment-এ owner, deadline এবং rationale নথিভুক্ত করুন।",
      "suggested_owner_role": "Team Lead",
      "priority": "P2",
      "human_review_required": True
    }
  ],
  "actions": [
    {
      "action_id": "A-001",
      "related_finding_id": "F-001",
      "title_bn": "কাজ বণ্টনের নথিভুক্তকরণ উন্নত করুন",
      "why_it_matters_bn": "স্বচ্ছতা বৃদ্ধি এবং দায়িত্ব নিশ্চিত করতে",
      "owner_role": "Team Lead",
      "priority": "P2",
      "suggested_due_days": 7,
      "verification_method_bn": "পরবর্তী ১০টি কাজ বণ্টনের রেকর্ড রূপায়ন করা",
      "status": "OPEN",
      "evidence_ids": [
        "msg_004588",
        "msg_004418"
      ]
    }
  ],
  "evidence_coverage": {
    "total_factual_claims": 2,
    "supported_factual_claims": 2,
    "unsupported_factual_claims": 0,
    "coverage_percent": 100,
    "citation_precision_percent": 100,
    "warnings_bn": []
  },
  "limitations_bn": [
    "এই বিশ্লেষণ কেবল উপলব্ধ বার্তা ও ইভেন্ট লগের উপর ভিত্তি করে তৈরি।",
    "Text-only evidence থেকে ব্যক্তিগত intent নিশ্চিত করা যায় না।"
  ],
  "requires_human_review": True
}


def build_analysis_prompt(query: str, mode: str, evidence_items: list):
    """Construct formatted JSON prompt for LM Studio based on audit mode and evidence list."""
    mode_name = ANALYSIS_MODES.get(mode, "General Intelligence Query")

    evidence_formatted = []
    for ev in evidence_items:
        msg_id = ev["message_id"]
        speaker = ev["speaker"]
        timestamp = ev.get("timestamp", "N/A")
        text = ev.get("text", "")
        evidence_formatted.append(f"[{msg_id}] ({timestamp}) {speaker}: {text}")

    evidence_block = "\n".join(evidence_formatted) if evidence_formatted else "No evidence records retrieved."

    prompt_body = f"""ANALYSIS MODE: {mode_name}
USER AUDIT QUERY: {query}

RETRIEVED LOCAL EVIDENCE RECORDS:
{evidence_block}

REQUIRED OUTPUT FORMAT:
You MUST respond with a single valid JSON object matching this structure EXACTLY (no outer markdown code fences):

{json.dumps(BRIEF_JSON_SCHEMA_EXAMPLE, indent=2, ensure_ascii=False)}

CRITICAL INSTRUCTIONS FOR THIS RUN:
1. Executive summary must be maximum 3 short, professional Bengali sentences.
2. Every finding and action MUST cite only real evidence IDs present in the retrieved list above (e.g. "msg_004588"). Never invent message IDs.
3. Compute risk score = likelihood (1-5) * impact (1-5) * exposure (1-5). Bands: 1-15 Low, 16-35 Medium, 36-60 High, 61-125 Critical.
4. Output professional business Bengali for all '_bn' fields.
5. If evidence is insufficient to answer the query, set status to 'AMBER', state 'Insufficient evidence' in executive summary, and leave findings empty.
"""

    return prompt_body
