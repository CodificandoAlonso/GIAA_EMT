### 10.1/10.2 Recomputed table vs paper

| variable | direction | paper_% | recomputed_% | k | N | match |
|---|---|---|---|---|---|---|
| boardings | toA | 90.60 | 90.98 | 242 | 266 | False |
| boardings | toB | 87.56 | 87.08 | 182 | 209 | False |
| alightings | toA | 93.61 | 93.61 | 249 | 266 | True |
| alightings | toB | 90.91 | 90.91 | 190 | 209 | True |
| travel times | toA | 95.49 | 95.86 | 255 | 266 | False |
| travel times | toB | 90.43 | 90.43 | 189 | 209 | True |
| occupation | toA | 94.39 | 94.74 | 270 | 285 | False |
| occupation | toB | 88.60 | 87.28 | 199 | 228 | False |

### 10.3 Binomial test against 0.95 and Wilson 95 % CI (all variants)

| variable | direction | variant | n_not_rejected | N | pct_not_rejected | wilson95_low | wilson95_high | binom_test_p_vs_0.95 | note |
|---|---|---|---|---|---|---|---|---|---|
| boardings | toA | as published (terminal counted as always non-rejected) | 242 | 266 | 90.977 | 86.926 | 93.862 | 0.007 | reproduces paper |
| boardings | toA | corrected (terminal with its real test result) | 240 | 266 | 90.226 | 86.064 | 93.242 | 0.001 |  |
| boardings | toA | main-loop stops only (terminals excluded) | 223 | 247 | 90.283 | 85.950 | 93.383 | 0.002 |  |
| boardings | toB | as published (terminal counted as always non-rejected) | 182 | 209 | 87.081 | 81.857 | 90.968 | 0.000 | reproduces paper |
| boardings | toB | corrected (terminal with its real test result) | 182 | 209 | 87.081 | 81.857 | 90.968 | 0.000 |  |
| boardings | toB | main-loop stops only (terminals excluded) | 163 | 190 | 85.789 | 80.114 | 90.046 | 0.000 |  |
| alightings | toA | as published (terminal counted as always non-rejected) | 249 | 266 | 93.609 | 90.005 | 95.972 | 0.322 | reproduces paper |
| alightings | toA | corrected (terminal with its real test result) | 248 | 266 | 93.233 | 89.558 | 95.677 | 0.202 |  |
| alightings | toA | main-loop stops only (terminals excluded) | 230 | 247 | 93.117 | 89.255 | 95.659 | 0.186 |  |
| alightings | toB | as published (terminal counted as always non-rejected) | 190 | 209 | 90.909 | 86.239 | 94.103 | 0.011 | reproduces paper |
| alightings | toB | corrected (terminal with its real test result) | 190 | 209 | 90.909 | 86.239 | 94.103 | 0.011 |  |
| alightings | toB | main-loop stops only (terminals excluded) | 171 | 190 | 90.000 | 84.910 | 93.504 | 0.004 |  |
| occupation | toA | all stops incl. terminals (as published) | 270 | 285 | 94.737 | 91.499 | 96.785 | 0.786 | reproduces paper |
| occupation | toA | terminals excluded (as the text states) | 241 | 247 | 97.571 | 94.803 | 98.882 | 0.077 |  |
| travel times | toA | as published | 255 | 266 | 95.865 | 92.748 | 97.675 | 0.672 | reproduces paper |
| travel times | toA | combinations with n>0 only | 255 | 266 | 95.865 | 92.748 | 97.675 | 0.672 |  |
| occupation | toB | all stops incl. terminals (as published) | 199 | 228 | 87.281 | 82.330 | 90.996 | 0.000 | reproduces paper |
| occupation | toB | terminals excluded (as the text states) | 176 | 190 | 92.632 | 88.013 | 95.560 | 0.133 |  |
| travel times | toB | as published | 189 | 209 | 90.431 | 85.682 | 93.720 | 0.006 | reproduces paper |
| travel times | toB | combinations with n>0 only | 189 | 198 | 95.455 | 91.588 | 97.590 | 1.000 |  |

### 10.4 Occupation, non-rejection by slot (both directions)

| slot | N | n_not_rejected | pct | n_rejected |
|---|---|---|---|---|
| 5.0 | 27.0 | 22.0 | 81.5 | 5.0 |
| 6.0 | 27.0 | 25.0 | 92.6 | 2.0 |
| 7.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 8.0 | 27.0 | 24.0 | 88.9 | 3.0 |
| 9.0 | 27.0 | 25.0 | 92.6 | 2.0 |
| 10.0 | 27.0 | 25.0 | 92.6 | 2.0 |
| 11.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 12.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 13.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 14.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 15.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 16.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 17.0 | 27.0 | 27.0 | 100.0 | 0.0 |
| 18.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 19.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 20.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 21.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 22.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 23.0 | 27.0 | 9.0 | 33.3 | 18.0 |

By direction and slot (only slots with any rejection):

| direction | slot | N | n_not_rejected | pct |
|---|---|---|---|---|
| toA | 6 | 15 | 14 | 93.3 |
| toA | 7 | 15 | 14 | 93.3 |
| toA | 8 | 15 | 13 | 86.7 |
| toA | 9 | 15 | 14 | 93.3 |
| toA | 10 | 15 | 14 | 93.3 |
| toA | 13 | 15 | 14 | 93.3 |
| toA | 14 | 15 | 14 | 93.3 |
| toA | 23 | 15 | 8 | 53.3 |
| toB | 5 | 12 | 7 | 58.3 |
| toB | 6 | 12 | 11 | 91.7 |
| toB | 8 | 12 | 11 | 91.7 |
| toB | 9 | 12 | 11 | 91.7 |
| toB | 10 | 12 | 11 | 91.7 |
| toB | 11 | 12 | 11 | 91.7 |
| toB | 12 | 12 | 11 | 91.7 |
| toB | 15 | 12 | 11 | 91.7 |
| toB | 16 | 12 | 11 | 91.7 |
| toB | 18 | 12 | 11 | 91.7 |
| toB | 19 | 12 | 11 | 91.7 |
| toB | 20 | 12 | 11 | 91.7 |
| toB | 21 | 12 | 11 | 91.7 |
| toB | 22 | 12 | 11 | 91.7 |
| toB | 23 | 12 | 1 | 8.3 |

All rejected occupation combinations:

| direction | stop | slot | n |
|---|---|---|---|
| toA | 5727 | 6 | 620 |
| toA | 5727 | 7 | 829 |
| toA | 2646 | 8 | 745 |
| toA | 5727 | 8 | 562 |
| toA | 5727 | 9 | 526 |
| toA | 5727 | 10 | 538 |
| toA | 5727 | 13 | 709 |
| toA | 5727 | 14 | 664 |
| toA | 2535 | 23 | 111 |
| toA | 2539 | 23 | 109 |
| toA | 2646 | 23 | 108 |
| toA | 3903 | 23 | 111 |
| toA | 3995 | 23 | 111 |
| toA | 4090 | 23 | 110 |
| toA | 562 | 23 | 109 |
| toB | 2646 | 5 | 120 |
| toB | 3929 | 5 | 118 |
| toB | 3990 | 5 | 118 |
| toB | 3994 | 5 | 118 |
| toB | 5938 | 5 | 118 |
| toB | 2646 | 6 | 512 |
| toB | 2646 | 8 | 691 |
| toB | 2646 | 9 | 587 |
| toB | 2646 | 10 | 614 |
| toB | 2646 | 11 | 574 |
| toB | 2646 | 12 | 573 |
| toB | 2646 | 15 | 752 |
| toB | 2646 | 16 | 755 |
| toB | 2646 | 18 | 666 |
| toB | 2646 | 19 | 568 |
| toB | 2646 | 20 | 503 |
| toB | 2646 | 21 | 412 |
| toB | 2646 | 22 | 217 |
| toB | 1167 | 23 | 186 |
| toB | 2538 | 23 | 231 |
| toB | 2964 | 23 | 216 |
| toB | 3929 | 23 | 229 |
| toB | 3990 | 23 | 231 |
| toB | 3994 | 23 | 227 |
| toB | 4187 | 23 | 220 |
| toB | 5727 | 23 | 216 |
| toB | 5938 | 23 | 225 |
| toB | 649 | 23 | 210 |
| toB | 81 | 23 | 224 |

Share of all occupation rejections falling in slot 23: **40.9%** (18 of 44); slot 23 holds 5.3% of the combinations.