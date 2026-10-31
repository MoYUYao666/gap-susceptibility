# -*- coding: utf-8 -*-
"""Drop the unsupported accuracy-causation clause from the A23 objection records.

Evidence (`docs/a23_margin_negative_control_paragraph.md`, `outputs/analysis/a23_margin_negative_control.json`):
the saturation is the margin CDF evaluated at a coarse epsilon grid, not a consequence of low accuracy --
the 59.1%-accurate ImageNet-5k reference saturates identically for epsilon >= 0.05 (66/66 arms M(0.10)=1.0).
"""
import io

P = "docs/A23_REVIEWER_OBJECTIONS.md"
t = io.open(P, encoding="utf-8").read()

old1 = ("a positive certificate (margin mass) was tested on a generic CLIP control and **saturated** because the "
        "frozen model's accuracy is too low for small margins to separate rows.")
new1 = ("a positive certificate (margin mass) was tested on a generic CLIP control and **saturated** at that "
        "operating point, because the statistic is the margin CDF evaluated at $2\\varepsilon$ and the frozen "
        "margin bulk lies below $0.02$ CLIP-score units; the 59.1%-accurate ImageNet-5k reference saturates "
        "identically for $\\varepsilon\\ge0.05$, so this is a property of the resolution, not of accuracy.")
assert old1 in t, "objection row pattern not found"
t = t.replace(old1, new1, 1)

old2 = ("margin mass saturates ($M\\approx1$ at every $\\lambda$; correlation undefined) because the frozen accuracy "
        "is only $20$--$27\\%$. Recorded as a negative control; OceanCLIP weights are not present locally, so the "
        "adapted-model version of this test is deferred until the weights are available.")
new2 = ("margin mass saturates ($M\\approx1$ at every $\\lambda$; correlation undefined); this is the margin CDF at "
        "a coarse $\\varepsilon$ grid rather than an accuracy effect, since the 59.1%-accurate ImageNet-5k reference "
        "saturates identically for $\\varepsilon\\ge0.05$. The control is in the **main text** of the working "
        "manuscript (since 2026-10-19, reworded 2026-10-24), and the adapted-encoder version was run: BioCLIP "
        "$r=-0.346$, OceanCLIP $r=-0.564$ at $\\varepsilon=0.05$.")
assert old2 in t, "certificate-control row pattern not found"
t = t.replace(old2, new2, 1)

io.open(P, "w", encoding="utf-8", newline="").write(t)
print("A23 objection records corrected")