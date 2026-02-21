import re

filepath = "frontend/src/pages/ATSView.vue"
with open(filepath, 'r') as f:
    content = f.read()

# Replace catch (e) where e is unused
# Case 1: error.value = ...
content = content.replace("catch (e) {\n    error.value =", "catch {\n    error.value =")
# Case 2: if (window.$toast) ...
content = content.replace("catch (e) {\n    if (window.$toast) {", "catch {\n    if (window.$toast) {")

with open(filepath, 'w') as f:
    f.write(content)
