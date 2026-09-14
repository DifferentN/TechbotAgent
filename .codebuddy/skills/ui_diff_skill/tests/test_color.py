from ui_diff_skill.diff.color import delta_e
def test_delta_e_same():
    assert delta_e((255,255,255),(255,255,255)) == 0.0
