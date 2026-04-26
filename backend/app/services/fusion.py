def reciprocal_rank_fusion(result_lists: list[list[dict]], k: int = 60) -> list[dict]:
    """
    Merge multiple ranked result lists using Reciprocal Rank Fusion (RRF).
    
    Each result list is a list of dicts. We use the 'url' + 'child_text' (or 'url'
    for graph results) as a unique key. Each result gets a score of 1/(k + rank).
    
    Args:
        result_lists: A list of ranked result lists to fuse.
        k: Constant to prevent high ranks from dominating. Default 60.
    
    Returns:
        A merged, re-ranked list of results sorted by fused score.
    """
    fused_scores = {}  # key -> {"score": float, "data": dict}

    for results in result_lists:
        for rank, item in enumerate(results):
            # Create a unique key per result
            key = item.get("url", "") + "|" + item.get("child_text", item.get("fingerprint", ""))
            
            rrf_score = 1.0 / (k + rank + 1)
            
            if key in fused_scores:
                fused_scores[key]["score"] += rrf_score
            else:
                fused_scores[key] = {"score": rrf_score, "data": item}

    # Sort by fused score descending
    ranked = sorted(fused_scores.values(), key=lambda x: x["score"], reverse=True)
    
    # Attach the fused score into the data dict
    output = []
    for entry in ranked:
        result = entry["data"].copy()
        result["rrf_score"] = round(entry["score"], 6)
        output.append(result)

    return output
