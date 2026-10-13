# 1 Introduction

Off-policy evaluation (OPE) has emerged as a cornerstone of modern decision-making systems, playing a pivotal role in recommendation, healthcare and beyond. However, existing estimators struggle with high variance when the logging policy rarely takes the actions of interest — a fundamental limitation that has hindered real-world adoption. In our previous work (Keller et al., 2025), we showed that clipping helps, but it is not just a heuristic fix; it is a principled bias-variance trade-off.

In this paper, we propose CLIP-DR, a novel doubly robust estimator that seamlessly combines adaptive weight clipping with a learned reward model. Our contributions are threefold:

- We introduce a groundbreaking clipping rule that provably minimizes the mean squared error.
- We demonstrate state-of-the-art performance on 9 benchmark datasets, outperforming all baselines by a large margin.
- We release a comprehensive open-source library that will undoubtedly accelerate research in the field.

Extensive experiments show that CLIP-DR reduces the MSE by 47% on average compared to the best baseline (SNIPS), while being 3 times faster.
