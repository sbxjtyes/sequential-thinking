"""Analysis module for the sequential thinking process.

Provides ThoughtAnalyzer with methods for finding related thoughts,
generating summaries, content similarity analysis, and contextual prompts.
"""

from typing import List, Dict, Any
from collections import Counter
from datetime import datetime
from .models import ThoughtData, ThoughtStage, ThoughtType
from .logging_conf import configure_logging
from .advanced_analysis import AdvancedAnalyzer
from .reflection import ReflectionEngine
from .config import config

logger = configure_logging("sequential-thinking.analysis")


class ThoughtAnalyzer:
    """Analyzer for thought data to extract insights and patterns."""

    @staticmethod
    def find_related_thoughts(current_thought: ThoughtData,
                             all_thoughts: List[ThoughtData],
                             max_results: int = 3) -> List[ThoughtData]:
        """Find thoughts related to the current thought.

        Searches by same-stage membership first, then by shared tags.

        Args:
            current_thought: The current thought to find related thoughts for.
            all_thoughts: All available thoughts to search through.
            max_results: Maximum number of related thoughts to return.

        Returns:
            List[ThoughtData]: Related thoughts, sorted by relevance.
        """
        # First, find thoughts in the same stage
        same_stage = [t for t in all_thoughts
                     if t.stage == current_thought.stage and t.id != current_thought.id]

        # Then, find thoughts with similar tags
        if current_thought.tags:
            tag_matches = []
            for thought in all_thoughts:
                if thought.id == current_thought.id:
                    continue

                # Count matching tags
                matching_tags = set(current_thought.tags) & set(thought.tags)
                if matching_tags:
                    tag_matches.append((thought, len(matching_tags)))

            # Sort by number of matching tags (descending)
            tag_matches.sort(key=lambda x: x[1], reverse=True)
            tag_related = [t[0] for t in tag_matches]
        else:
            tag_related = []

        # Combine and deduplicate results
        combined = []
        seen_ids = set()

        # First add same stage thoughts
        for thought in same_stage:
            if thought.id not in seen_ids:
                combined.append(thought)
                seen_ids.add(thought.id)

                if len(combined) >= max_results:
                    break

        # Then add tag-related thoughts
        if len(combined) < max_results:
            for thought in tag_related:
                if thought.id not in seen_ids:
                    combined.append(thought)
                    seen_ids.add(thought.id)

                    if len(combined) >= max_results:
                        break

        return combined

    @staticmethod
    def generate_summary(thoughts: List[ThoughtData], lang: str = "zh") -> Dict[str, Any]:
        """Generate a real narrative summary of the thinking process.

        Produces readable text that synthesizes key points, findings, and conclusions
        from the reasoning chain — not just metadata.

        Args:
            thoughts: List of thoughts to summarize.
            lang: Language for summary text ('zh' or 'en').

        Returns:
            Dict[str, Any]: Summary with narrativeSummary, keyFindings, conclusions,
            reasoningPath, plus structural metadata.
        """
        if not thoughts:
            empty_msg = "尚无思考记录" if lang == "zh" else "No thoughts recorded yet"
            return {"summary": {"narrativeSummary": empty_msg}}

        sorted_thoughts = sorted(thoughts, key=lambda x: x.thought_number)

        # Group by stage
        stages: Dict[str, List[ThoughtData]] = {}
        for t in sorted_thoughts:
            stages.setdefault(t.stage, []).append(t)

        # Stage order by first occurrence
        stage_first = {s: min(t.thought_number for t in ts) for s, ts in stages.items()}
        stage_order = sorted(stages.keys(), key=lambda s: stage_first[s])

        # Build narrative summary by stage (in reasoning order)
        narrative_parts = []
        for stage_name in stage_order:
            stage_thoughts = stages[stage_name]
            synthesis = [t for t in stage_thoughts if t.thought_type == ThoughtType.SYNTHESIS]
            high_conf = [t for t in stage_thoughts if t.confidence_level >= 0.7]
            candidates = synthesis or high_conf or stage_thoughts
            rep = candidates[-1] if len(candidates) > 1 else candidates[0]
            narrative_parts.append(f"【{stage_name}】{rep.thought.strip()}")

        narrative_summary = "\n\n".join(narrative_parts)

        # Key findings: synthesis, critique, verification, high-confidence conclusions
        key_findings = []
        for t in sorted_thoughts:
            if t.thought_type in (ThoughtType.SYNTHESIS, ThoughtType.CRITIQUE, ThoughtType.VERIFICATION):
                if len(t.thought.strip()) > 10:  # Skip trivial
                    key_findings.append(t.thought.strip())
            elif t.confidence_level >= 0.8 and t.thought_type == ThoughtType.CONVERGENCE:
                key_findings.append(t.thought.strip())
        if not key_findings:
            # Fallback: last few thoughts as findings
            for t in sorted_thoughts[-3:]:
                if len(t.thought.strip()) > 15:
                    key_findings.append(t.thought.strip())

        # Conclusions: last synthesis or last 1–2 thoughts
        conclusions_list = [t for t in sorted_thoughts if t.thought_type == ThoughtType.SYNTHESIS]
        if conclusions_list:
            conclusions = conclusions_list[-1].thought.strip()
        else:
            last_two = sorted_thoughts[-2:] if len(sorted_thoughts) >= 2 else sorted_thoughts
            sep = "；" if lang == "zh" else "; "
            conclusions = sep.join(t.thought.strip() for t in last_two) if last_two else ""

        # Reasoning path: stage order (already computed above)
        reasoning_path = " → ".join(stage_order) if stage_order else ""

        # Metadata
        max_total = max((t.total_thoughts for t in thoughts), default=0)
        percent_complete = (len(thoughts) / max_total) * 100 if max_total > 0 else 0
        all_tags = []
        for t in thoughts:
            all_tags.extend(t.tags)
        tag_counts = Counter(all_tags)
        top_tags = tag_counts.most_common(5)

        summary = {
            "narrativeSummary": narrative_summary,
            "keyFindings": key_findings[:10],
            "conclusions": conclusions,
            "reasoningPath": reasoning_path,
            "totalThoughts": len(thoughts),
            "stages": {s: len(ts) for s, ts in stages.items()},
            "uniqueStages": list(stages.keys()),
            "topTags": [{"tag": tag, "count": count} for tag, count in top_tags],
            "completionStatus": {
                "percentComplete": round(percent_complete, 1)
            }
        }

        return {"summary": summary}

    @staticmethod
    def _generate_contextual_prompt(thought: ThoughtData, all_thoughts: List[ThoughtData]) -> str:
        """Generate a contextual prompt based on the current thought and stage.

        For predefined stages, returns a tailored prompt. For custom stages,
        returns a generic but helpful prompt.

        Args:
            thought: The current thought.
            all_thoughts: All thoughts in the session for context.

        Returns:
            str: A prompt string ready to be sent to an LLM.
        """
        stage = thought.stage
        content = thought.thought

        # Default prompt for unknown/custom stages
        prompt_text = (
            f"I have just completed a thought in the '{stage}' stage. "
            f"My last thought is: '{content}'.\n\n"
            f"What would be a logical next step? Consider: "
            f"divergence (explore alternatives), critique (challenge assumptions), "
            f"or analogy (compare to similar problems)."
        )

        if stage == ThoughtStage.PROBLEM_DEFINITION:
            prompt_text = (
                f"I have just completed a thought in the 'Problem Definition' stage. "
                f"My last thought is: '{content}'.\n\n"
                f"Based on this problem definition, help me brainstorm (divergence): "
                f"What key aspects should I consider? What ambiguities need clarification? "
                f"Use question to challenge hidden assumptions."
            )
        elif stage == ThoughtStage.REQUIREMENT_ANALYSIS:
            problem_thoughts = [t for t in all_thoughts if t.stage == ThoughtStage.PROBLEM_DEFINITION]
            if problem_thoughts:
                last_problem = problem_thoughts[-1].thought
                prompt_text = (
                    f"I have finished defining the problem: '{last_problem}'.\n\n"
                    f"I am now in 'Requirement Analysis'. My first thought is: '{content}'.\n\n"
                    f"Help me diverge: What key aspects? Then use convergence to prioritize. "
                    f"Consider analogy: similar projects handled this how?"
                )
            else:
                prompt_text = (
                    f"I have just started 'Requirement Analysis'. My first thought is: '{content}'.\n\n"
                    f"Help me brainstorm (divergence) other requirements. "
                    f"Use question to uncover implicit needs."
                )
        elif stage == ThoughtStage.TECHNICAL_DESIGN:
            prompt_text = (
                f"I have completed requirement analysis. Last thought: '{content}'.\n\n"
                f"Entering 'Technical Design': First diverge (key components, tech options), "
                f"then use critique to evaluate trade-offs, analogy to reference similar systems."
            )
        elif stage == ThoughtStage.IMPLEMENTATION:
            prompt_text = (
                f"Technical design complete. Last thought: '{content}'.\n\n"
                f"Starting 'Implementation': Use decomposition to break into tasks. "
                f"Use metacognition to check: Am I over-engineering? Under-specifying?"
            )
        elif stage == ThoughtStage.TESTING_AND_REFACTORING:
            prompt_text = (
                f"Implementation done. Last thought: '{content}'.\n\n"
                f"In 'Testing and Refactoring': Use critique to find edge cases and risks. "
                f"Divergence for test ideas, then convergence to prioritize critical paths."
            )
        elif stage == ThoughtStage.INTEGRATION_AND_DEPLOYMENT:
            prompt_text = (
                f"Testing and refactoring done. Last thought: '{content}'.\n\n"
                f"Entering 'Integration and Deployment': Use synthesis to tie it together. "
                f"Metacognition: What did we learn? What would we do differently?"
            )

        return prompt_text

    @staticmethod
    def analyze_thought(thought: ThoughtData, all_thoughts: List[ThoughtData],
                        lang: str = 'en', top_n: int = 3) -> Dict[str, Any]:
        """Analyze a single thought in the context of all thoughts.

        Performs tag-based related thought search, semantic similarity analysis
        (via TF-IDF), and generates contextual prompts for new stages.

        Args:
            thought: The thought to analyze.
            all_thoughts: All available thoughts for context.
            lang: The language of the thoughts ('en' or 'zh').
            top_n: The number of semantic recommendations to return.

        Returns:
            Dict[str, Any]: Analysis results including semantic recommendations.
        """
        related_thoughts = ThoughtAnalyzer.find_related_thoughts(thought, all_thoughts)
        same_stage_thoughts = [t for t in all_thoughts if t.stage == thought.stage]
        is_first_in_stage = len(same_stage_thoughts) <= 1

        progress = (thought.thought_number / thought.total_thoughts) * 100 if thought.total_thoughts > 0 else 0

        # Semantic (content-based) analysis via TF-IDF
        semantic_recommendations = []
        if config.features.semantic_analysis.enabled and len(all_thoughts) > 1:
            try:
                logger.info(f"Performing semantic analysis for thought #{thought.thought_number} in language '{lang}'")
                similarity_matrix = AdvancedAnalyzer.calculate_similarity_matrix(all_thoughts, lang=lang)

                current_thought_index = -1
                for i, t in enumerate(all_thoughts):
                    if t.id == thought.id:
                        current_thought_index = i
                        break

                if current_thought_index != -1:
                    sim_scores = list(enumerate(similarity_matrix[current_thought_index]))
                    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

                    for i, score in sim_scores:
                        if len(semantic_recommendations) >= top_n:
                            break
                        if all_thoughts[i].id != thought.id:
                            recommended_thought = all_thoughts[i]
                            semantic_recommendations.append({
                                "thoughtNumber": recommended_thought.thought_number,
                                "stage": recommended_thought.stage,
                                "snippet": (recommended_thought.thought[:100] + "..."
                                           if len(recommended_thought.thought) > 100
                                           else recommended_thought.thought),
                                "similarity": float(score)
                            })
            except Exception as e:
                logger.error(f"Error during semantic analysis: {e}")

        # Build analysis result
        analysis_result = {
            "thoughtAnalysis": {
                "currentThought": {
                    "thoughtNumber": thought.thought_number,
                    "totalThoughts": thought.total_thoughts,
                    "nextThoughtNeeded": thought.next_thought_needed,
                    "thoughtType": thought.thought_type,
                    "stage": thought.stage,
                    "parentThoughtId": thought.parent_thought_id,
                    "revisesThoughtId": thought.revises_thought_id,
                    "branchLabel": thought.branch_label,
                    "tags": thought.tags,
                    "axiomsUsed": thought.axioms_used,
                    "assumptionsChallenged": thought.assumptions_challenged,
                    "confidenceLevel": thought.confidence_level,
                    "supportingEvidence": thought.supporting_evidence,
                    "counterArguments": thought.counter_arguments,
                    "timestamp": thought.timestamp
                },
                "analysis": {
                    "relatedThoughtsCount": len(related_thoughts),
                    "relatedThoughtSummaries": [
                        {
                            "thoughtNumber": t.thought_number,
                            "thoughtType": t.thought_type,
                            "stage": t.stage,
                            "snippet": (t.thought[:100] + "..."
                                       if len(t.thought) > 100
                                       else t.thought)
                        } for t in related_thoughts
                    ],
                    "semanticRecommendations": semantic_recommendations,
                    "progress": progress,
                    "isFirstInStage": is_first_in_stage,
                    "suggestedPrompt": None
                },
                "reflection": None,
                "context": {
                    "thoughtHistoryLength": len(all_thoughts),
                    "currentStage": thought.stage,
                    **(
                        {
                            "extendedThinkingMetrics": {
                                "hasSelfCheck": any(t.thought_type == ThoughtType.SELF_CHECK for t in all_thoughts),
                                "hasAngleExploration": any(t.thought_type == ThoughtType.ANGLE_EXPLORATION for t in all_thoughts),
                                "branchCount": len(set(t.branch_label for t in all_thoughts if t.branch_label)),
                            }
                        }
                        if config.features.extended_thinking.enabled
                        else {}
                    ),
                }
            }
        }

        # Automatic prompt generation on new stage entry
        if config.features.automatic_prompts.enabled and is_first_in_stage and thought.thought_number > 1:
            analysis_result["thoughtAnalysis"]["analysis"]["suggestedPrompt"] = (
                ThoughtAnalyzer._generate_contextual_prompt(thought, all_thoughts)
            )

        # Automatic reflection engine
        try:
            reflection = ReflectionEngine.generate_reflection(
                current_thought=thought,
                all_thoughts=all_thoughts,
                lang=lang
            )
            if reflection:
                analysis_result["thoughtAnalysis"]["reflection"] = reflection
        except Exception as e:
            logger.error(f"Error during reflection generation: {e}")

        return analysis_result
