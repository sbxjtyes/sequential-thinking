"""Analysis module for the sequential thinking process.

Provides ThoughtAnalyzer with methods for finding related thoughts,
generating summaries, content similarity analysis, and contextual prompts.
"""

from typing import List, Dict, Any
from collections import Counter
from datetime import datetime
import numpy as np
from .models import ThoughtData, ThoughtStage
from .logging_conf import configure_logging
from .advanced_analysis import AdvancedAnalyzer
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
    def generate_summary(thoughts: List[ThoughtData]) -> Dict[str, Any]:
        """Generate a summary of the thinking process.

        Args:
            thoughts: List of thoughts to summarize.

        Returns:
            Dict[str, Any]: Summary data including stage counts, timeline, and top tags.
        """
        if not thoughts:
            return {"summary": "No thoughts recorded yet"}

        # Group thoughts by stage
        stages = {}
        for thought in thoughts:
            if thought.stage not in stages:
                stages[thought.stage] = []
            stages[thought.stage].append(thought)

        # Count tags
        all_tags = []
        for thought in thoughts:
            all_tags.extend(thought.tags)
        tag_counts = Counter(all_tags)
        top_tags = tag_counts.most_common(5)

        try:
            # Safely calculate max total thoughts to avoid division by zero
            max_total = max((t.total_thoughts for t in thoughts), default=0)
            percent_complete = (len(thoughts) / max_total) * 100 if max_total > 0 else 0

            logger.debug(f"Calculating completion: {len(thoughts)}/{max_total} = {percent_complete}%")

            # Count thoughts by stage
            stage_counts = {
                stage: len(thoughts_list)
                for stage, thoughts_list in stages.items()
            }

            # Create timeline entries
            sorted_thoughts = sorted(thoughts, key=lambda x: x.thought_number)
            timeline_entries = [
                {"number": t.thought_number, "stage": t.stage}
                for t in sorted_thoughts
            ]

            # Create top tags entries
            top_tags_entries = [
                {"tag": tag, "count": count}
                for tag, count in top_tags
            ]

            # Check if all predefined stages are represented
            all_predefined_stages_present = all(
                stage in stages
                for stage in ThoughtStage.ALL
            )

            # Collect all unique stages used (including custom ones)
            unique_stages = list(stages.keys())

            summary = {
                "totalThoughts": len(thoughts),
                "stages": stage_counts,
                "uniqueStages": unique_stages,
                "timeline": timeline_entries,
                "topTags": top_tags_entries,
                "completionStatus": {
                    "hasAllPredefinedStages": all_predefined_stages_present,
                    "percentComplete": percent_complete
                }
            }
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            summary = {
                "totalThoughts": len(thoughts),
                "error": str(e)
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
            f"What would be a logical next step?"
        )

        if stage == ThoughtStage.PROBLEM_DEFINITION:
            prompt_text = (
                f"I have just completed a thought in the 'Problem Definition' stage. "
                f"My last thought is: '{content}'.\n\n"
                f"Based on this problem definition, please help me brainstorm the requirements. "
                f"What key aspects should I consider? What are the potential ambiguities I need to clarify?"
            )
        elif stage == ThoughtStage.REQUIREMENT_ANALYSIS:
            problem_thoughts = [t for t in all_thoughts if t.stage == ThoughtStage.PROBLEM_DEFINITION]
            if problem_thoughts:
                last_problem = problem_thoughts[-1].thought
                prompt_text = (
                    f"I have finished defining the problem, which is: '{last_problem}'.\n\n"
                    f"I am now starting the 'Requirement Analysis' stage. My first thought is: '{content}'.\n\n"
                    f"Please help me plan the requirement analysis. What key aspects should I consider?"
                )
            else:
                prompt_text = (
                    f"I have just started the 'Requirement Analysis' stage. "
                    f"My first thought is: '{content}'.\n\n"
                    f"Based on my first requirement, please help me brainstorm other related requirements."
                )
        elif stage == ThoughtStage.TECHNICAL_DESIGN:
            prompt_text = (
                f"I have completed the requirement analysis. My last thought on requirements is: '{content}'.\n\n"
                f"Now, entering the 'Technical Design' stage, please help me create a high-level technical design. "
                f"What are the key components, modules, or services? What technologies would you recommend and why?"
            )
        elif stage == ThoughtStage.IMPLEMENTATION:
            prompt_text = (
                f"The technical design is complete. My last design thought is: '{content}'.\n\n"
                f"I am now starting the 'Implementation' stage. Please help me break this down into "
                f"smaller, manageable tasks. Can you suggest a file structure and some boilerplate code?"
            )
        elif stage == ThoughtStage.TESTING_AND_REFACTORING:
            prompt_text = (
                f"I have finished a part of the implementation. My last thought is: '{content}'.\n\n"
                f"Now, in the 'Testing and Refactoring' stage, what kind of tests (unit, integration, e2e) "
                f"should I write to ensure its quality? Please provide some test case ideas."
            )
        elif stage == ThoughtStage.INTEGRATION_AND_DEPLOYMENT:
            prompt_text = (
                f"I have finished testing and refactoring. My last thought was: '{content}'.\n\n"
                f"I am now entering the 'Integration and Deployment' stage. What are the next steps? "
                f"Should I be thinking about documentation, environment configuration, or CI/CD pipelines?"
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
                    "stage": thought.stage,
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
                "context": {
                    "thoughtHistoryLength": len(all_thoughts),
                    "currentStage": thought.stage
                }
            }
        }

        # Automatic prompt generation on new stage entry
        if config.features.automatic_prompts.enabled and is_first_in_stage and thought.thought_number > 1:
            analysis_result["thoughtAnalysis"]["analysis"]["suggestedPrompt"] = (
                ThoughtAnalyzer._generate_contextual_prompt(thought, all_thoughts)
            )

        return analysis_result
