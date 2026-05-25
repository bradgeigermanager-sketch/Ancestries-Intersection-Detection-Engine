"""
MODULE: ancestry_intersection_engine
VERSION: 1.0.0
TYPE: Service Router Layer (FastAPI) & Execution Pipeline
USE: Traces parental lineages backwards to identify common ancestors.
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Set, Any

app = FastAPI(title="Ancestries Intersection Detection Engine", version="1.0.0")

# --- Presentation Models ---
class CommonAncestorDetail(BaseModel):
    ancestor_id: str
    display_name: str
    historical_marker: str  # e.g., "Born 1842 in Virginia"
    origin_generations_back: int
    target_generations_back: int
    kinship_coefficient: float

class AncestryIntersectionResponse(BaseModel):
    status: str
    origin_id: str
    target_id: str
    common_ancestors_count: int
    closest_relationship_summary: str
    intersection_map: List[CommonAncestorDetail]

# --- Mock Context Graph Loader ---
def mock_load_lineage_dag() -> Dict[str, Dict[str, Any]]:
    """
    Simulated Directed Acyclic Graph (DAG) for lineage mapping.
    Format: 'node_id': {'name': str, 'father': str|None, 'mother': str|None, 'meta': str}
    """
    return {
        "p_self_1":  {"name": "User Alpha", "father": "p_fa_1", "mother": "p_mo_1", "meta": "Born 1985"},
        "p_self_2":  {"name": "User Beta",  "father": "p_fa_2", "mother": "p_mo_2", "meta": "Born 1988"},
        
        # Alpha's side
        "p_fa_1":    {"name": "Charles Alpha", "father": "p_gfa_shared", "mother": "p_gmo_alpha", "meta": "Born 1960"},
        "p_mo_1":    {"name": "Diana Alpha",   "father": None, "mother": None, "meta": ""},
        
        # Beta's side
        "p_fa_2":    {"name": "Edward Beta",   "father": None, "mother": None, "meta": ""},
        "p_mo_2":    {"name": "Fiona Beta",    "father": "p_gfa_shared", "mother": "p_gmo_beta", "meta": "Born 1962"},
        
        # Shared Ancestor Node (Common Grandfather)
        "p_gfa_shared": {"name": "George Root", "father": None, "mother": None, "meta": "Born 1930 in Ohio"},
        "p_gmo_alpha":  {"name": "Helen Alpha", "father": None, "mother": None, "meta": ""},
        "p_gmo_beta":   {"name": "Irene Beta",  "father": None, "mother": None, "meta": ""}
    }

# --- Traversal Pipeline Core ---
def trace_ancestors(person_id: str, graph: Dict[str, Dict[str, Any]], current_gen: int, max_gen: int, history: Dict[str, int]) -> Dict[str, int]:
    """
    Recursive or iterative BFS/DFS to build an ancestor dictionary mapping {node_id: generations_removed}
    """
    if not person_id or person_id not in graph or current_gen > max_gen:
        return history
    
    node = graph[person_id]
    if person_id not in history or current_gen < history[person_id]:
        history[person_id] = current_gen
        
    if node["father"]:
        trace_ancestors(node["father"], graph, current_gen + 1, max_gen, history)
    if node["mother"]:
        trace_ancestors(node["mother"], graph, current_gen + 1, max_gen, history)
        
    return history

# --- Router Endpoints ---
@app.get("/api/v1/ancestry/intersect", response_model=AncestryIntersectionResponse)
async def intersect_ancestries(
    origin_id: str = Query(..., description="ID of first person"),
    target_id: str = Query(..., description="ID of second person"),
    max_generations: int = Query(8, description="Maximum generational depth limit to trace back")
):
    dag = mock_load_lineage_dag()
    if origin_id not in dag or target_id not in dag:
        raise HTTPException(status_code=404, detail="One or both individuals not found in lineage graph.")
        
    # 1. Map entire tree backwards for both individuals
    origin_tree = trace_ancestors(origin_id, dag, 0, max_generations, {})
    target_tree = trace_ancestors(target_id, dag, 0, max_generations, {})
    
    # Remove self-references from the ancestor lists
    origin_tree.pop(origin_id, None)
    target_tree.pop(target_id, None)
    
    # 2. Intersect sets to pinpoint shared biological roots
    shared_ancestor_ids = set(origin_tree.keys()).intersection(set(target_tree.keys()))
    
    intersection_payload = []
    closest_relationship = "No shared ancestors detected within threshold limit."
    min_combined_distance = float('inf')
    
    for anc_id in shared_ancestor_ids:
        gen_back_origin = origin_tree[anc_id]
        gen_back_target = target_tree[anc_id]
        
        # Calculate standard Wright's Kinship Coefficient component
        # Formula segment: 0.5 raised to the power of total structural edge steps between them
        total_steps = gen_back_origin + gen_back_target
        kinship_coef = (0.5) ** total_steps
        
        if total_steps < min_combined_distance:
            min_combined_distance = total_steps
            # Simple conversion rule for display (e.g., 2 steps away back to grandfather = First Cousins)
            if gen_back_origin == 2 and gen_back_target == 2:
                closest_relationship = "First Cousins (Shared Grandparent)"
            else:
                closest_relationship = f"Common ancestors found at generational depth {gen_back_origin}:{gen_back_target}"

        intersection_payload.append(
            CommonAncestorDetail(
                ancestor_id=anc_id,
                display_name=dag[anc_id]["name"],
                historical_marker=dag[anc_id]["meta"] or "No historical metadata logged.",
                origin_generations_back=gen_back_origin,
                target_generations_back=gen_back_target,
                kinship_coefficient=round(kinship_coef, 6)
            )
        )
        
    # Sort payload closest matching generation path first
    intersection_payload.sort(key=lambda x: (x.origin_generations_back + x.target_generations_back))
    
    return AncestryIntersectionResponse(
        status="SUCCESS",
        origin_id=origin_id,
        target_id=target_id,
        common_ancestors_count=len(shared_ancestor_ids),
        closest_relationship_summary=closest_relationship,
        intersection_map=intersection_payload
    )
  
