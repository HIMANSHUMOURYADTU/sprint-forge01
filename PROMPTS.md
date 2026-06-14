# PROMPTS.md - Internal Linking Intelligence Engine

This log tracks the pivotal prompts and iterations that evolved the Link Intel Suite from a basic crawler summary to a professional SEO recommendation engine.

---

## 1. Anchor Text Audit Extension
- **Prompt:** "Extend `analyzer.py` over_optimized_anchors: flag a destination where one non-generic anchor is >= 60% of all internal anchors pointing at it AND count >= 10."
- **For:** Completing the deterministic anchor classification rules.
- **Revised?** Yes. The first version flagged tiny destinations (low sample size); added the `count >= 10` floor to ensure statistical significance.

## 2. Semantic Clustering Transition
- **Prompt:** "Replace URL-folder clustering with `SentenceTransformer('all-MiniLM-L6-v2')` and `AgglomerativeClustering`. Use semantic embeddings of page content (Title + H1 + H2 + Body) for grouping."
- **For:** Moving from fragile path-based clustering to a semantic approach that groups pages by actual topic.
- **Revised?** No. The embedding model provided a strong baseline for topicality.

## 3. Dynamic Cluster Selection
- **Prompt:** "Replace the current sqrt(N)-based cluster count selection with silhouette-score-based automatic cluster selection. Evaluate k from 5 to min(30, n_samples // 4), compute silhouette_score for every k, and select the k with the highest score."
- **For:** Removing arbitrary math in favor of data-driven cluster optimization.
- **Revised?** Yes. Added a fallback for very small datasets where the specified range was invalid.

## 4. Embedding-Based Relatedness
- **Prompt:** "Replace keyword-overlap relatedness with embedding-based relatedness. Compute cosine similarity between page embeddings. Reuse embeddings from the clustering step to avoid redundant model calls."
- **For:** Upgrading the "relatedness" signal from simple word matching to semantic similarity.
- **Revised?** Yes. Kept keyword intersection as a secondary field (`shared_topics`) to preserve report schema compatibility.

## 5. Weighted Recommendation Ranking
- **Prompt:** "Improve recommendation quality. Replace hard filtering of low-value URLs (/author/, /tag/) with a weighted score: 0.45*semantic + 0.20*cluster_bonus + 0.15*underlinked + 0.10*orphan + 0.15*high_value_reward - 0.40*low_value_penalty."
- **For:** Generating "SEO consultant" grade recommendations that prioritize high-value targets (services, solutions) and a la a "push" to orphans, without zeroing out results.
- **Revised?** Yes. Iterated from a hard `continue` (which caused zero results on some sites) to a negative penalty.

## 6. Automatic Anchor Generation
- **Prompt:** "Create an automatic anchor generation system based on priority: 1. Clean H1, 2. Clean Title, 3. Shared topic phrase, 4. Top target keywords. Ensure 2-6 words, lowercase, no URLs, no generic 'click here' text."
- **For:** Turning raw "target URLs" into ready-to-paste recommendations for the final report.
- **Revised?** No. The priority chain effectively handled most page types deterministically.

## 7. Automated Cluster Naming
- **Prompt:** "Implement cluster naming using the top 2 most representative keywords from the cluster. Convert to Title Case. Fallback to 'General Topic'."
- **For:** Replacing `name: None` with descriptive topic labels for the dashboard and report.
- **Revised?** No. Using the top 2 TF-keywords provided a clear, descriptive label.
