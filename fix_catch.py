import os
import re

# Files that reported no-undef errors
files_to_fix = [
    "frontend/src/components/InterviewTracker.vue",
    "frontend/src/components/SalaryCoach.vue",
    "frontend/src/components/SkillsOverview.vue",
    "frontend/src/composables/useJobRecommendations.js",
    "frontend/src/pages/ATSView.vue",
    "frontend/src/pages/AdminUserDetail.vue",
    "frontend/src/pages/Documents.vue",
    "frontend/src/pages/InterviewPrep.vue",
    "frontend/src/pages/MockInterview.vue",
    "frontend/src/pages/NewApplication.vue",
    "frontend/src/pages/Settings.vue",
    "frontend/src/pages/SubscriptionSuccess.vue",
]

for filepath in files_to_fix:
    if not os.path.exists(filepath):
        continue

    with open(filepath, 'r') as f:
        content = f.read()

    # We need to find "catch {" and check the following block.
    # This is tricky with regex. simpler approach:
    # If the file has "err" undefined error, it likely uses "err" inside a catch block that lost its argument.
    # We can try to assume that if we replaced `catch (err) {` with `catch {`, we can reverse it if `err` is found nearby.
    # But simpler: Just search for `catch {` and if the block looks like it uses a variable, restore it.

    # Since we can't easily parse blocks, let's look for common patterns.
    # Most usages are `err.message` or `e.response`.

    # Heuristic 1: If we see `catch {` and then `err` usage before the next `}`, restore `catch (err) {`.
    # This assumes no nested catch blocks or weird formatting.

    new_content = ""
    last_pos = 0
    for match in re.finditer(r'catch\s*\{', content):
        start = match.start()
        end = match.end()
        new_content += content[last_pos:start]

        # Look ahead until next closing brace (approximate)
        # This is very rough but might work for simple code
        # Find next '}'
        next_brace = content.find('}', end)
        if next_brace != -1:
            block_content = content[end:next_brace]

            if re.search(r'\berr\b', block_content):
                new_content += "catch (err) {"
            elif re.search(r'\berror\b', block_content):
                new_content += "catch (error) {"
            elif re.search(r'\be\b', block_content):
                new_content += "catch (e) {"
            else:
                new_content += "catch {"
        else:
             new_content += "catch {"

        last_pos = end

    new_content += content[last_pos:]

    if new_content != content:
        print(f"Patched {filepath}")
        with open(filepath, 'w') as f:
            f.write(new_content)

print("Finished restoring catch variables.")
