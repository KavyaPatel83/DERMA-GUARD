with open('scripts/generate_bcse335l_final_review_ppt.py', 'r', encoding='utf-8') as f:
    ppt = f.read()

# Remove the orphan empty-string add() call left from Sindhu removal (line 162)
old = ('add(tfp, "\u2022 Patel Kavya Vipulkumar \u2014 B.Tech Data Science (patel.kavya2023@vitstudent.ac.in)", FONT_B, 11, bold=True, color=WHITE, sb=2)\n'
       'add(tfp, "\u2022 Aarav Prawin \u2014 B.Tech Data Science (aarav.prawin2023@vitstudent.ac.in)", FONT_B, 11, bold=True, color=WHITE, sb=2)\n'
       'add(tfp, "", FONT_B, 11, bold=True, color=TEAL_SOFT, sb=2)\n'
       'add(tfp, "School of Computer Science and Engineering (SCOPE), VIT Chennai", FONT_B, 10, color=MUTED, sb=2)')

new = ('add(tfp, "\u2022 Patel Kavya Vipulkumar \u2014 B.Tech Data Science (patel.kavya2023@vitstudent.ac.in)", FONT_B, 12, bold=True, color=WHITE, sb=4)\n'
       'add(tfp, "\u2022 Aarav Prawin \u2014 B.Tech Data Science (aarav.prawin2023@vitstudent.ac.in)", FONT_B, 12, bold=True, color=WHITE, sb=4)\n'
       'add(tfp, "School of Computer Science and Engineering (SCOPE), VIT Chennai", FONT_B, 10.5, color=MUTED, sb=6)')

if old in ppt:
    ppt = ppt.replace(old, new)
    print('Replaced author section')
else:
    # line by line approach
    lines = ppt.splitlines(keepends=True)
    out = []
    skip_next = False
    for line in lines:
        if 'bold=True, color=TEAL_SOFT' in line and 'add(tfp' in line:
            skip_next = True   # skip the empty line
            continue
        out.append(line)
    ppt = ''.join(out)
    print('Removed orphan line via scan')

with open('scripts/generate_bcse335l_final_review_ppt.py', 'w', encoding='utf-8') as f:
    f.write(ppt)
print('Done')

