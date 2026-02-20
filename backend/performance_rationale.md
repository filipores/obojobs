# Performance Optimization Rationale: N+1 Query in `save_extracted_skills_for_upload`

## Problem
The original implementation of `save_extracted_skills_for_upload` had an N+1 query pattern. For every skill extracted from a document (N), a separate database query was executed to check if the user already possessed that skill.

```python
    for skill_data in extracted_skills:
        existing = UserSkill.query.filter_by(user_id=user_id, skill_name=skill_data["skill_name"]).first()
        # ... process existing or create new
```

If a document contains 50 skills, this results in 50 individual `SELECT` queries. This is inefficient due to:
1. **Network Latency**: Each query incurs a round-trip between the application and the database.
2. **Database Overhead**: The database must parse, optimize, and execute each query individually.
3. **Connection Pool Pressure**: Holding a connection for many small queries can lead to exhaustion in high-concurrency environments.

## Solution
The optimization fetches all existing skills for the user that match the names in the `extracted_skills` list in a **single query**.

```python
    skill_names = [s["skill_name"] for s in extracted_skills]
    existing_skills = UserSkill.query.filter(
        UserSkill.user_id == user_id,
        UserSkill.skill_name.in_(skill_names)
    ).all()

    # Create a lookup map for O(1) access
    existing_map = {s.skill_name: s for s in existing_skills}
```

The loop then uses the `existing_map` to perform lookups in memory, reducing the number of database queries from **O(N)** to **O(1)**.

## Expected Impact
- **Reduced Latency**: Significant reduction in total time for document processing, especially for documents with many skills.
- **Improved Scalability**: Fewer database resources consumed per request.
- **Deterministic Performance**: The number of queries no longer grows with the number of skills in the document.

## Note on Environment
Due to the absence of the required dependencies (Flask, SQLAlchemy, etc.) in the sandbox environment, a live benchmark was not possible. However, the N+1 query pattern and its bulk-fetching solution are well-established performance best practices.
