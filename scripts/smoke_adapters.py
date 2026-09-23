import sys
sys.path.insert(0, "src")
from time_machine.prompt_adapters import prepare_input
from time_machine.registry import load_cohort

c = load_cohort("registry/cohort-local-v1.yaml")
m = [x for x in c.models if x.id == "qwen25-7b-instruct-2024"][0]
p = prepare_input("Hello there", m)
print(repr(p.prepared_text))
assert "Hello there" in p.prepared_text
assert p.was_truncated is False
print("qwen adapter ok")
