"""Parse current catalog selections and legacy proposal checkboxes."""
import re


def proposal_collection(value: str) -> str:
    text = value.strip().lower()
    selected = re.findall(r'^\s*- \[[xX]\]\s*(.+)', text, re.M)
    if selected:
        choices = {'applied' if 'applied' in line else 'formal' if 'formal' in line else 'topical'
                   for line in selected}
        if len(choices) != 1:
            raise ValueError('Choose one catalog table for the proposal')
        return choices.pop()
    if text in {'applied', 'applied studies'}:
        return 'applied'
    if text in {'formal', 'formal studies'}:
        return 'formal'
    return 'topical'
