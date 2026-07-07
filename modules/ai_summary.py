def generate_ai_summary(
    sales_result,
    collections_result,
    construction_result,
    final_dataset
):

    summary = []

    summary.append("========== AI MANAGEMENT SUMMARY ==========\n")

    # Sales
    achievement = float(sales_result["Achievement %"].iloc[0])

    if achievement >= 100:
        summary.append("✅ Sales target achieved.")
    else:
        summary.append(
            f"⚠ Sales achievement is only {achievement:.2f}% of target."
        )

    # Collections
    collection_achievement = float(
        collections_result["Achievement %"].iloc[0]
    )

    if collection_achievement >= 100:
        summary.append("✅ Collections are on track.")
    else:
        summary.append(
            f"⚠ Collections achieved only {collection_achievement:.2f}%."
        )

    # Construction
    construction_achievement = float(
        construction_result["Achievement %"].iloc[0]
    )

    if construction_achievement >= 100:
        summary.append("Construction is ahead of schedule.")
    else:
        summary.append("Construction progress is behind target.")

    # Risk Summary
    summary.append("\nRisk Distribution")

    risk_counts = final_dataset["Risk Level"].value_counts()

    for risk, count in risk_counts.items():
        summary.append(f"{risk}: {count}")

    # Escalation Summary
    summary.append("\nEscalation Summary")

    escalation_counts = final_dataset["Escalation"].value_counts()

    for level, count in escalation_counts.items():
        summary.append(f"{level}: {count}")

    # Business Rules
    summary.append("\nTop Business Issues")

    issues = final_dataset["Business Rule"].value_counts().head(5)

    for issue, count in issues.items():
        summary.append(f"{issue}: {count}")

    summary.append("\nRecommended Actions")

    summary.append("- Recover overdue collections.")
    summary.append("- Focus on high-risk projects.")
    summary.append("- Monitor construction delays.")
    summary.append("- Improve booking performance.")
    summary.append("- Review escalated projects weekly.")

    return "\n".join(summary)